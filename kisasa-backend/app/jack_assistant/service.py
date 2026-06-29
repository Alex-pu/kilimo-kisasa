from datetime import datetime
from math import asin, cos, radians, sin, sqrt
import re

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.models.agrovet import Agrovet
from app.models.comment import Comment
from app.models.issue import Issue
from app.models.product import AgrovetProduct
from app.models.user import User, UserRole

JACK_DISPLAY_NAME = "Jack"
JACK_EMAIL = "jack@kisasa.local"
JACK_AUTH_SUBJECT = "jack-assistant-bot"
JACK_MENTION_PATTERN = re.compile(r"(^|\W)@?jack\b", re.IGNORECASE)
NEARBY_AGROVET_RADIUS_KM = 35
NEARBY_AGROVET_LIMIT = 5


def is_jack_mentioned(text: str) -> bool:
    return bool(JACK_MENTION_PATTERN.search(text or ""))


def _clean_jack_prompt(text: str) -> str:
    cleaned = JACK_MENTION_PATTERN.sub(" ", text or "")
    return " ".join(cleaned.replace(",", " ").split())


def _readable_enum(value) -> str:
    raw = getattr(value, "value", value)
    return str(raw or "").replace("_", " ").strip()


def _distance_km(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 6371 * 2 * asin(sqrt(a))


def _build_nearby_agrovet_context(db: Session, issue: Issue) -> str | None:
    if issue.location_latitude is None or issue.location_longitude is None:
        return None

    products = (
        db.query(AgrovetProduct)
        .join(Agrovet)
        .filter(AgrovetProduct.stock_quantity > 0)
        .all()
    )

    rows = []
    for product in products:
        agrovet = product.agrovet
        distance = _distance_km(
            issue.location_longitude,
            issue.location_latitude,
            agrovet.location_longitude,
            agrovet.location_latitude,
        )
        if distance <= NEARBY_AGROVET_RADIUS_KM:
            rows.append((distance, agrovet, product))

    rows.sort(key=lambda item: item[0])
    if not rows:
        return None

    lines = [
        "Nearby agrovet inventory. Use only these entries when recommending where the farmer can buy inputs; "
        "if none match the likely diagnosis, say the farmer should ask these shops or a local extension officer "
        "instead of inventing a product. At the end of the reply, direct the farmer to visit or call the nearest "
        "relevant agrovet for more advice on safe pesticide/input choice, and mention they can also wait for a "
        "verified expert recommendation in Kisasa."
    ]
    for distance, agrovet, product in rows[:NEARBY_AGROVET_LIMIT]:
        lines.append(
            "- "
            f"{agrovet.name} ({agrovet.location_name}, {distance:.1f} km away, phone {agrovet.phone_number}): "
            f"{product.product_name}, {product.category}, {product.currency} {product.price:g}, "
            f"stock {product.stock_quantity:g}"
            f"{f' {product.unit}' if product.unit else ''}"
            f"{f'. Instructions: {product.instructions}' if product.instructions else ''}"
        )
    return "\n".join(lines)


def _summarize_nearby_agrovets(context_text: str | None) -> str:
    if not context_text or "Nearby agrovet inventory" not in context_text:
        return ""

    product_lines = [
        line[2:]
        for line in context_text.splitlines()
        if line.startswith("- ")
    ][:2]
    if not product_lines:
        return ""

    return (
        " For local input advice, the farmer can visit or call "
        + "; ".join(product_lines)
        + ". They should describe the symptoms and confirm the right pesticide/input before buying or applying it. "
        "They can also wait for a verified expert recommendation on Kisasa."
    )


def _generate_local_fallback(
    prompt: str,
    issue: Issue | None = None,
    context_text: str | None = None,
) -> str:
    prompt_text = _clean_jack_prompt(prompt)
    issue_text = ""
    if issue:
        issue_text = " ".join(
            item
            for item in [
                issue.title,
                issue.description,
                _readable_enum(issue.category),
                issue.location_name,
            ]
            if item
        )

    text = f"{prompt_text} {issue_text}".lower()
    issue_hint = ""
    if issue:
        issue_hint = f" For this {_readable_enum(issue.category)} post,"

    if any(word in text for word in ["tomato", "blight", "spots", "fungus", "fungal"]):
        advice = (
            "remove badly affected leaves, avoid overhead watering, improve spacing, "
            "and use a registered copper or mancozeb fungicide if symptoms keep spreading."
        )
    elif any(word in text for word in ["maize", "armyworm", "worm", "caterpillar"]):
        advice = (
            "check the whorl early, look for fresh feeding damage, hand-pick where possible, "
            "and ask an agrovet for a registered fall armyworm product if many plants are affected."
        )
    elif any(word in text for word in ["pest", "pesticide", "insect", "aphid", "thrip", "mite", "borer"]):
        advice = (
            "first identify the pest and how widespread it is. Check the underside of leaves, stems, flowers, "
            "and fruits, then use the least risky control that fits the pest. Avoid buying a pesticide from the "
            "name alone; take a clear photo or sample to an agrovet or extension officer so the active ingredient "
            "matches the pest and crop label."
        )
    elif any(word in text for word in ["coffee", "berry", "berries", "shedding", "drop", "dropping"]):
        advice = (
            "check for moisture stress, poor nutrition, coffee berry disease, insect damage, and heavy fruit load. "
            "Look for lesions on berries, holes, yellowing leaves, and recent dry or wet spells. Do not spray blindly; "
            "confirm whether this is disease, pest, or nutrition before choosing an input."
        )
    elif any(word in text for word in ["yellow", "yellowing", "nutrient", "fertilizer", "soil"]):
        advice = (
            "check soil moisture first, then consider a soil test. Yellowing can come from nitrogen loss, "
            "waterlogging, root damage, or nutrient deficiency."
        )
    elif any(word in text for word in ["water", "irrigation", "dry", "wilting"]):
        advice = (
            "check moisture 5-10 cm below the surface, mulch where possible, and water deeply in the morning "
            "instead of giving many shallow irrigations."
        )
    elif any(word in text for word in ["price", "market", "sell"]):
        advice = (
            "compare at least two nearby markets, check transport cost, and avoid selling all produce at once "
            "if prices are moving quickly."
        )
    else:
        advice = (
            "share the crop or animal, age, location, symptoms, recent weather, and what you have already tried. "
            "A clear photo also helps experts narrow it down."
        )

    return (
        f"Jack: {issue_hint} I would start here: {advice} "
        "If the problem is severe, involve a local extension officer or verified expert before applying chemicals."
        f"{_summarize_nearby_agrovets(context_text)}"
    )


def _extract_response_text(payload: dict) -> str:
    output_text = payload.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    for item in payload.get("output", []):
        for content in item.get("content", []):
            text = content.get("text")
            if isinstance(text, str) and text.strip():
                return text.strip()

    return ""


def _extract_chat_completion_text(payload: dict) -> str:
    for choice in payload.get("choices", []):
        message = choice.get("message") or {}
        content = message.get("content")
        if isinstance(content, str) and content.strip():
            return content.strip()
    return ""


def _format_farmer_context(
    issue: Issue | None = None,
    farmer_context: dict | None = None,
) -> str:
    parts = []
    if issue:
        if issue.location_name:
            parts.append(f"post location name: {issue.location_name}")
        if issue.location_latitude is not None and issue.location_longitude is not None:
            parts.append(
                f"post coordinates: {issue.location_latitude}, {issue.location_longitude}"
            )

    if farmer_context:
        location_name = farmer_context.get("location_name")
        latitude = farmer_context.get("location_latitude")
        longitude = farmer_context.get("location_longitude")
        if location_name:
            parts.append(f"farmer location name: {location_name}")
        if latitude is not None and longitude is not None:
            parts.append(f"farmer coordinates: {latitude}, {longitude}")

    return "\n".join(parts)


def _build_jack_messages(
    prompt: str,
    issue: Issue | None = None,
    history: list[dict] | None = None,
    farmer_context: dict | None = None,
    context_text: str | None = None,
) -> list[dict]:
    location_context = _format_farmer_context(issue, farmer_context)
    context_parts = []
    if issue:
        context_parts.append(
            "Post context:"
            f"\n- Category: {_readable_enum(issue.category)}"
            f"\n- Title: {issue.title}"
            f"\n- Description: {issue.description}"
        )
    if location_context:
        context_parts.append(f"Location context:\n{location_context}")
    if context_text:
        context_parts.append(f"User-provided context:\n{context_text[:4000]}")

    messages = [
        {
            "role": "system",
            "content": (
            "You are Jack, a practical farm assistant for Kenyan farmers. "
            "Give concise, safe agricultural guidance. Use farmer location context for crop, weather, "
            "soil, pest, seasonality, and nearby-input advice when it is provided. When nearby agrovet inventory "
            "is provided, you may mention the nearest relevant shop and product, but do not invent shops, products, "
            "prices, stock, an exact address, or weather observation. At the end, direct the farmer to visit or "
            "call the nearest relevant agrovet from the provided inventory for more advice on pesticides or inputs, "
            "and mention they can also wait for a verified expert recommendation on Kisasa. Ask for missing crop, location, symptoms, "
            "recent weather, and photos when the diagnosis is uncertain. Do not claim certainty from weak "
            "evidence. Tell users to involve a local extension officer, verified expert, or agrovet before "
            "applying pesticides, veterinary medicines, or other regulated inputs."
            ),
        }
    ]

    for message in (history or [])[-6:]:
        role = message.get("role")
        content = message.get("content")
        if role in {"user", "assistant"} and content:
            messages.append({"role": role, "content": str(content)[:1200]})

    user_content = f"Farmer question/comment:\n{_clean_jack_prompt(prompt)}"
    if context_parts:
        context_block = "\n\n".join(context_parts)
        user_content = f"{context_block}\n\n{user_content}"
    messages.append({"role": "user", "content": user_content})
    return messages


def _generate_grok_fallback(
    prompt: str,
    issue: Issue | None = None,
    history: list[dict] | None = None,
    farmer_context: dict | None = None,
    context_text: str | None = None,
) -> str | None:
    if not settings.jack_grok_fallback_enabled or not settings.grok_api_key:
        return None

    try:
        response = httpx.post(
            f"{settings.jack_grok_base_url.rstrip('/')}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.grok_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.jack_grok_fallback_model,
                "messages": _build_jack_messages(
                    prompt,
                    issue,
                    history,
                    farmer_context,
                    context_text,
                ),
                "temperature": 0.3,
            },
            timeout=settings.jack_codex_fallback_timeout_seconds,
        )
        response.raise_for_status()
        reply = _extract_chat_completion_text(response.json())
    except httpx.HTTPError:
        return None

    if not reply:
        return None
    return reply if reply.startswith("Jack:") else f"Jack: {reply}"


def _generate_codex_fallback(
    prompt: str,
    issue: Issue | None = None,
    history: list[dict] | None = None,
    farmer_context: dict | None = None,
    context_text: str | None = None,
) -> str | None:
    if not settings.jack_codex_fallback_enabled or not settings.openai_api_key:
        return None

    try:
        response = httpx.post(
            "https://api.openai.com/v1/responses",
            headers={
                "Authorization": f"Bearer {settings.openai_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.jack_codex_fallback_model,
                "input": _build_jack_messages(
                    prompt,
                    issue,
                    history,
                    farmer_context,
                    context_text,
                ),
            },
            timeout=settings.jack_codex_fallback_timeout_seconds,
        )
        response.raise_for_status()
        reply = _extract_response_text(response.json())
    except httpx.HTTPError:
        return None

    if not reply:
        return None
    return reply if reply.startswith("Jack:") else f"Jack: {reply}"


def generate_farm_reply(
    prompt: str,
    issue: Issue | None = None,
    context_text: str | None = None,
    history: list[dict] | None = None,
    farmer_context: dict | None = None,
) -> str:
    grok_reply = _generate_grok_fallback(
        prompt,
        issue,
        history,
        farmer_context,
        context_text,
    )
    if grok_reply:
        return grok_reply

    codex_reply = _generate_codex_fallback(
        prompt,
        issue,
        history,
        farmer_context,
        context_text,
    )
    if codex_reply:
        return codex_reply

    return _generate_local_fallback(prompt, issue, context_text)


def get_or_create_jack_user(db: Session) -> User:
    jack = db.query(User).filter(User.firebase_uid == JACK_AUTH_SUBJECT).first()
    if jack:
        return jack

    jack = User(
        firebase_uid=JACK_AUTH_SUBJECT,
        email=JACK_EMAIL,
        full_name=JACK_DISPLAY_NAME,
        role=UserRole.EXPERT,
        bio="Farm assistant for Kisasa community replies.",
        verification_status=True,
        is_active=True,
    )
    db.add(jack)
    db.flush()
    return jack


def create_reply_if_tagged(db: Session, issue: Issue, source_comment: Comment) -> Comment | None:
    if not is_jack_mentioned(source_comment.content):
        return None

    jack = get_or_create_jack_user(db)
    if source_comment.author_id == jack.id:
        return None

    reply = Comment(
        issue_id=issue.id,
        author_id=jack.id,
        parent_comment_id=source_comment.id,
        content=generate_farm_reply(
            source_comment.content,
            issue,
            context_text=_build_nearby_agrovet_context(db, issue),
        ),
    )
    db.add(reply)
    db.commit()
    db.refresh(reply)
    return reply


def chat(
    prompt: str,
    context_text: str | None = None,
    history: list[dict] | None = None,
    farmer_context: dict | None = None,
) -> dict:
    return {
        "assistant": JACK_DISPLAY_NAME,
        "reply": generate_farm_reply(
            prompt,
            context_text=context_text,
            history=history,
            farmer_context=farmer_context,
        ),
        "created_at": datetime.utcnow(),
        "source": None,
    }
