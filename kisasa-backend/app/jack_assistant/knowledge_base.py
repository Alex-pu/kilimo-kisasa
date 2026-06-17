from dataclasses import dataclass
from pathlib import Path
import re

KNOWLEDGE_DIR = Path(__file__).resolve().parent / "knowledge"
SUPPORTED_EXTENSIONS = {".md", ".txt"}
STOP_WORDS = {
    "about",
    "after",
    "also",
    "and",
    "are",
    "can",
    "for",
    "from",
    "have",
    "how",
    "jack",
    "should",
    "that",
    "the",
    "then",
    "this",
    "what",
    "when",
    "with",
    "your",
}


@dataclass(frozen=True)
class KnowledgeMatch:
    title: str
    source: str
    content: str
    score: int


def _words(text: str) -> set[str]:
    return {
        word
        for word in re.findall(r"[a-z0-9]+", (text or "").lower())
        if len(word) > 2 and word not in STOP_WORDS
    }


def _title_from_content(path: Path, content: str) -> str:
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("#"):
            return line.lstrip("#").strip() or path.stem.replace("-", " ").title()
    return path.stem.replace("-", " ").replace("_", " ").title()


def _safe_document_path(filename: str) -> Path:
    normalized = re.sub(r"[^a-zA-Z0-9._-]+", "-", (filename or "").strip()).strip(".-")
    if not normalized:
        raise ValueError("Document filename is required")

    path = KNOWLEDGE_DIR / normalized
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        path = path.with_suffix(".md")

    resolved_dir = KNOWLEDGE_DIR.resolve()
    resolved_path = path.resolve()
    if resolved_dir not in resolved_path.parents or path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError("Document filename must end in .md or .txt")

    return path


def _summarize(content: str, query_terms: set[str]) -> str:
    lines = [
        line.strip(" -\t")
        for line in content.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    if not lines:
        return ""

    ranked = sorted(
        lines,
        key=lambda line: len(_words(line) & query_terms),
        reverse=True,
    )
    selected = [line for line in ranked[:4] if line]
    return " ".join(selected)[:900]


def find_best_match_in_text(
    prompt: str,
    content: str | None,
    title: str = "Provided Text",
    source: str = "provided-text",
) -> KnowledgeMatch | None:
    query_terms = _words(prompt)
    if not query_terms or not content:
        return None

    content = content.strip()
    if not content:
        return None

    content_terms = _words(content)
    title_terms = _words(title)
    score = len(query_terms & content_terms) + (2 * len(query_terms & title_terms))
    if score <= 0:
        return None

    return KnowledgeMatch(
        title=title,
        source=source,
        content=_summarize(content, query_terms),
        score=score,
    )


def list_documents() -> list[dict]:
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
    documents = []
    for path in sorted(KNOWLEDGE_DIR.iterdir()):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            content = path.read_text(encoding="utf-8", errors="ignore")
            documents.append({
                "title": _title_from_content(path, content),
                "source": path.name,
            })
    return documents


def get_document(filename: str) -> dict | None:
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
    try:
        path = _safe_document_path(filename)
    except ValueError:
        return None
    if not path.exists() or not path.is_file():
        return None

    content = path.read_text(encoding="utf-8", errors="ignore")
    return {
        "title": _title_from_content(path, content),
        "source": path.name,
        "content": content,
    }


def save_document(filename: str, content: str) -> dict:
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
    path = _safe_document_path(filename)
    path.write_text(content.strip() + "\n", encoding="utf-8")
    saved_content = path.read_text(encoding="utf-8", errors="ignore")
    return {
        "title": _title_from_content(path, saved_content),
        "source": path.name,
        "content": saved_content,
    }


def delete_document(filename: str) -> bool:
    try:
        path = _safe_document_path(filename)
    except ValueError:
        return False
    if not path.exists() or not path.is_file():
        return False
    path.unlink()
    return True


def find_best_match(prompt: str) -> KnowledgeMatch | None:
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
    query_terms = _words(prompt)
    if not query_terms:
        return None

    best: KnowledgeMatch | None = None
    for path in KNOWLEDGE_DIR.iterdir():
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        content = path.read_text(encoding="utf-8", errors="ignore")
        document_terms = _words(content)
        title = _title_from_content(path, content)
        title_terms = _words(title)
        score = len(query_terms & document_terms) + (2 * len(query_terms & title_terms))
        if score <= 0:
            continue

        match = KnowledgeMatch(
            title=title,
            source=path.name,
            content=_summarize(content, query_terms),
            score=score,
        )
        if best is None or match.score > best.score:
            best = match

    return best
