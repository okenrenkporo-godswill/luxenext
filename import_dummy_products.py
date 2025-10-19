import requests
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Product, Category
from datetime import datetime, timezone

def import_dummy_products():
    db: Session = SessionLocal()

    # 1. Get all categories from DummyJSON
    categories_url = "https://dummyjson.com/products/categories"
    categories = requests.get(categories_url).json()

    imported_products = 0
    imported_categories = 0

    for cat in categories:
        # ✅ handle both dict and string
        cat_name = cat["name"] if isinstance(cat, dict) else cat
        cat_slug = cat["slug"] if isinstance(cat, dict) else cat

        # 2. Ensure category exists
        category = db.query(Category).filter(Category.name == cat_name).first()
        if not category:
            category = Category(name=cat_name, description=f"Auto-imported {cat_name}")
            db.add(category)
            db.commit()
            db.refresh(category)
            imported_categories += 1

        # 3. Fetch products in this category
        products_url = f"https://dummyjson.com/products/category/{cat_slug}"
        products = requests.get(products_url).json().get("products", [])

        for p in products:
            # 4. Skip if product already exists
            existing = db.query(Product).filter(Product.name == p["title"]).first()
            if existing:
                continue

            # 5. Insert product
            product = Product(
                name=p["title"],
                description=p["description"],
                price=float(p["price"]),
                stock=int(p["stock"]),
                image_url=p["images"][0] if p["images"] else None,
                thumbnail_url=p["thumbnail"],
                category_id=category.id,
                created_at=datetime.now(timezone.utc)
            )
            db.add(product)
            imported_products += 1

        db.commit()

    db.close()
    print(f"✅ Imported {imported_products} products across {imported_categories} new categories.")

if __name__ == "__main__":
    import_dummy_products()
