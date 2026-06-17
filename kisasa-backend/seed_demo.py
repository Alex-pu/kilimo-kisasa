from app.database import Base, SessionLocal, engine
from app.models.agrovet import Agrovet
from app.models.comment import Comment
from app.models.issue import Issue, IssueCategory
from app.models.product import AgrovetProduct
from app.models.recommendation import Recommendation
from app.models.user import User, UserRole


def get_or_create_user(db, email, full_name, role=UserRole.FARMER, **extra):
    user = db.query(User).filter(User.email == email).first()
    if user:
        return user

    user = User(
        firebase_uid=f"demo:{email}",
        email=email,
        password_hash=extra.pop("password_hash", None),
        full_name=full_name,
        role=role,
        **extra,
    )
    db.add(user)
    db.flush()
    return user


def get_or_create_agrovet(db, email, **data):
    agrovet = db.query(Agrovet).filter(Agrovet.email == email).first()
    if agrovet:
        return agrovet

    agrovet = Agrovet(email=email, **data)
    db.add(agrovet)
    db.flush()
    return agrovet


def get_or_create_product(db, agrovet, product_name, **data):
    product = (
        db.query(AgrovetProduct)
        .filter(
            AgrovetProduct.agrovet_id == agrovet.id,
            AgrovetProduct.product_name == product_name,
        )
        .first()
    )
    if product:
        return product

    product = AgrovetProduct(
        agrovet_id=agrovet.id,
        product_name=product_name,
        **data,
    )
    db.add(product)
    db.flush()
    return product


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        farmer = get_or_create_user(
            db,
            "farmer.demo@kisasa.local",
            "Mary Wanjiku",
            phone="+254700111222",
            location_latitude=-1.2921,
            location_longitude=36.8219,
            location_name="Nairobi, Kenya",
        )
        expert = get_or_create_user(
            db,
            "expert.demo@kisasa.local",
            "Dr. Peter Mwangi",
            role=UserRole.EXPERT,
            phone="+254700333444",
            bio="Plant pathologist specializing in smallholder vegetable farming.",
            verification_status=True,
            location_latitude=-1.2864,
            location_longitude=36.8172,
            location_name="Nairobi, Kenya",
        )
        admin = get_or_create_user(
            db,
            "admin.demo@kisasa.local",
            "Kisasa Admin",
            role=UserRole.ADMIN,
            verification_status=True,
        )

        agrovet_1 = get_or_create_agrovet(
            db,
            "westlands@kisasa.local",
            name="Westlands Farmers Agrovet",
            description="Crop protection, fertilizers, and vegetable seed supplies.",
            phone_number="+254711222333",
            website="https://example.com/westlands-agrovet",
            location_latitude=-1.2676,
            location_longitude=36.8108,
            location_name="Westlands, Nairobi",
            address="Mpaka Road, Westlands",
            verification_status=True,
            rating=4.6,
            review_count=18,
        )
        agrovet_2 = get_or_create_agrovet(
            db,
            "ruaka@kisasa.local",
            name="Ruaka Green Inputs",
            description="Inputs for vegetables, fruit trees, and greenhouse farmers.",
            phone_number="+254722444555",
            website="https://example.com/ruaka-green",
            location_latitude=-1.2039,
            location_longitude=36.7762,
            location_name="Ruaka, Kiambu",
            address="Limuru Road, Ruaka",
            verification_status=True,
            rating=4.3,
            review_count=11,
        )

        copper = get_or_create_product(
            db,
            agrovet_1,
            "Copper Oxychloride 50WP",
            category="fungicide",
            description="Protective fungicide commonly used for tomato early blight management.",
            price=650,
            stock_quantity=24,
            unit="250g",
        )
        mancozeb = get_or_create_product(
            db,
            agrovet_2,
            "Mancozeb 80WP",
            category="fungicide",
            description="Broad-spectrum contact fungicide for fungal leaf spots.",
            price=520,
            stock_quantity=17,
            unit="200g",
        )
        foliar = get_or_create_product(
            db,
            agrovet_1,
            "Tomato Foliar Feed NPK",
            category="fertilizer",
            description="Supplemental foliar nutrition for stressed tomato plants.",
            price=780,
            stock_quantity=9,
            unit="500ml",
        )

        issue = (
            db.query(Issue)
            .filter(Issue.title == "Tomato leaves have brown spots and yellow edges")
            .first()
        )
        if not issue:
            issue = Issue(
                creator_id=farmer.id,
                title="Tomato leaves have brown spots and yellow edges",
                description=(
                    "My tomatoes started showing brown circular spots on older leaves. "
                    "Some leaves are yellowing from the edges. It has rained for three days."
                ),
                category=IssueCategory.CROP_DISEASE,
                location_latitude=-1.2921,
                location_longitude=36.8219,
                location_name="Nairobi, Kenya",
                is_urgent=True,
            )
            db.add(issue)
            db.flush()

        if not db.query(Comment).filter(Comment.issue_id == issue.id).first():
            db.add_all(
                [
                    Comment(
                        issue_id=issue.id,
                        author_id=farmer.id,
                        content="The spots are mostly on the lower leaves. I have not sprayed yet.",
                    ),
                    Comment(
                        issue_id=issue.id,
                        author_id=expert.id,
                        content="Please remove badly infected leaves and avoid overhead watering while we confirm.",
                    ),
                ]
            )

        if not db.query(Recommendation).filter(Recommendation.issue_id == issue.id).first():
            db.add(
                Recommendation(
                    issue_id=issue.id,
                    recommender_id=expert.id,
                    farm_input_name="Protective fungicide for suspected early blight",
                    description=(
                        "Apply a protective fungicide after removing infected leaves. "
                        "Rotate active ingredients and follow the label pre-harvest interval."
                    ),
                    rationale=(
                        "Rain and lower-leaf spotting point to early blight pressure. "
                        "A contact fungicide can slow spread while sanitation reduces inoculum."
                    ),
                    estimated_cost=650,
                    linked_product_ids=[copper.id, mancozeb.id, foliar.id],
                )
            )

        db.commit()
        print("Seeded demo data:")
        print(f"- farmer: {farmer.email}")
        print(f"- expert: {expert.email}")
        print(f"- admin: {admin.email}")
        print(f"- issue: {issue.title}")
        print(f"- agrovets: {agrovet_1.name}, {agrovet_2.name}")
        print("- products linked to expert recommendation")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
