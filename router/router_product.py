from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import schemas, crud
from database import get_db
import os, shutil
from PIL import Image
from roles import require_role
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from typing import Optional
from fastapi.responses import FileResponse
from roles import require_role
from models import Product, Category
from datetime import datetime,timezone

import os, shutil, requests,models
from bs4 import BeautifulSoup
router = APIRouter(
    prefix="/products", tags=["Products"]
)

def response_format(data=None, message="Success", success=True):
    return {"success": success, "message": message, "data": data}


@router.get("/")
def get_products(db: Session = Depends(get_db)):
    db_products = crud.get_products(db)
    return response_format(db_products, "All products retrieved successfully")



def scrape_image(source_url: str, save_path: str):
    try:
        response = requests.get(source_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        img_tag = soup.find("img")
        if not img_tag or "src" not in img_tag.attrs:
            return None

        img_url = img_tag["src"]
        if img_url.startswith("//"):
            img_url = "https:" + img_url
        elif img_url.startswith("/"):
            from urllib.parse import urljoin
            img_url = urljoin(source_url, img_url)

        img_data = requests.get(img_url).content
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "wb") as f:
            f.write(img_data)
        return save_path
    except Exception as e:
        print(f"Error scraping image: {e}")
        return None

# -------------------------------
# Create product with optional image upload
# -------------------------------
@router.post("/")
async def create_product(
    name: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    stock: int = Form(...),
    category_id: int = Form(...),
    file: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    product_data = schemas.ProductCreate(
        name=name,
        description=description,
        price=price,
        stock=stock,
        category_id=category_id
    )

    image_path = None
    thumbnail_path = None

    if file:
        os.makedirs("static/images", exist_ok=True)
        # Save full image
        image_path = f"static/images/{file.filename}"
        with open(image_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        product_data.image_url = image_path

        # Generate thumbnail
        thumbnail_size = (200, 200)  # pixels
        image = Image.open(image_path)
        image.thumbnail(thumbnail_size)
        name, ext = os.path.splitext(file.filename)
        thumbnail_filename = f"{name}_thumb{ext}"
        thumbnail_path = f"static/images/{thumbnail_filename}"
        image.save(thumbnail_path)

        product_data.thumbnail_url = thumbnail_path

    db_product = crud.create_product(db, product_data)
    return response_format(db_product, "Product created successfully")

# -------------------------------
# Create product from scraped image
# -------------------------------

# backend/app/routers/products.py


@router.post("/scrape/")
def create_product_from_url(
    name: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    stock: int = Form(...),
    category_id: int = Form(...),
    source_url: str = Form(...),
    db: Session = Depends(get_db),
    _= Depends(require_role("admin", "superadmin"))
):
    product_data = schemas.ProductCreate(
        name=name,
        description=description,
        price=price,
        stock=stock,
        category_id=category_id
    )
    save_path = f"static/images/{name.replace(' ', '_')}.jpg"
    scraped_image_path = scrape_image(source_url, save_path)
    product_data.image_url = scraped_image_path

    db_product = crud.create_product(db, product_data)
    return response_format(db_product, "Product created with scraped image successfully")


@router.post("/import-dummy-products")
def import_all_products(db: Session = Depends(get_db)):
    categories_url = "https://dummyjson.com/products/categories"
    categories = requests.get(categories_url).json()  # list of dicts

    

    imported_products = 0
    imported_categories = 0

    for cat in categories:
        cat_name = cat["name"]  # For DB
        cat_slug = cat["slug"]  # For API calls

        print("Processing:", cat_name, cat_slug)  # Debugging

        # ✅ Ensure category exists
        category = db.query(Category).filter(Category.name == cat_name).first()
        if not category:
            category = Category(name=cat_name, description=f"Auto-imported {cat_name}")
            db.add(category)
            db.commit()
            db.refresh(category)
            imported_categories += 1

        # ✅ Fetch products for this category using slug
        products_url = f"https://dummyjson.com/products/category/{cat_slug}"
        products_data = requests.get(products_url).json()
        products = products_data.get("products", [])

        

        for p in products:
            existing = db.query(Product).filter(Product.name == p["title"]).first()
            if existing:
                continue

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

    return {
        "message": f"✅ Imported {imported_products} products across {imported_categories} categories"
    }



# -------------------------------
# Get Top Products
# -------------------------------
@router.get("/top")
def get_top_products(
    limit: int = 10,
    sort_by: str = "sales",  # can be 'sales' or 'views'
    db: Session = Depends(get_db)
):
    """
    Returns top products based on sales count or views.
    Defaults to top 10 by sales.
    """
    query = db.query(Product)

    # You can adjust this depending on your Product model fields
    if hasattr(Product, "sales_count") and sort_by == "sales":
        query = query.order_by(Product.sales_count.desc())
    elif hasattr(Product, "views") and sort_by == "views":
        query = query.order_by(Product.views.desc())
    else:
        query = query.order_by(Product.created_at.desc())  # fallback

    top_products = query.limit(limit).all()
    return response_format(top_products, f"Top {limit} products by {sort_by}")

# -------------------------------
# Download product image
# -------------------------------

@router.get("/search")
def search_products(
    
    q: str = Query(..., min_length=2, description="Search keyword"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    min_price: Optional[float] = Query(None, description="Minimum price"),
    max_price: Optional[float] = Query(None, description="Maximum price"),
    sort: Optional[str] = Query("relevance", description="Sort by: price_asc, price_desc, name_asc, name_desc"),
    skip: int = Query(0, ge=0, description="Number of items to skip for pagination"),
    limit: int = Query(20, ge=1, le=100, description="Max number of items to return"),
    db: Session = Depends(get_db)
):
   
    results = crud.search_products(
        db=db,
        q=q,
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
        sort=sort,
        skip=skip,
        limit=limit
    )
    return {
        "success": True,
        "message": "Search results retrieved successfully",
        "pagination": {
            "skip": skip,
            "limit": limit,
            "count": len(results)
        },
        "data": results
    }

@router.get("/download/{product_id}")
def download_image(product_id: int, db: Session = Depends(get_db)):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not db_product or not db_product.image_url:
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(db_product.image_url)




@router.get("/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db)):
    db_product = crud.get_product(db, product_id)
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    return response_format(db_product, "Product retrieved successfully")

# -------------------------------
# Update product
# -------------------------------
@router.put("/{product_id}")
async def update_product(
    product_id: int,
    name: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    stock: int = Form(...),
    category_id: int = Form(...),
    file: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    db_product = crud.get_product(db, product_id)
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")

    update_data = schemas.ProductUpdate(
        name=name,
        description=description,
        price=price,
        stock=stock,
        category_id=category_id
    )

    # Handle image upload
    if file:
        os.makedirs("static/images", exist_ok=True)
        image_path = f"static/images/{file.filename}"
        with open(image_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        update_data.image_url = image_path

        # Generate thumbnail
        image = Image.open(image_path)
        image.thumbnail((200, 200))
        name_, ext = os.path.splitext(file.filename)
        thumbnail_path = f"static/images/{name_}_thumb{ext}"
        image.save(thumbnail_path)
        update_data.thumbnail_url = thumbnail_path

    updated_product = crud.update_product(db, db_product, update_data)
    return response_format(updated_product, "Product updated successfully")


# -------------------------------
# Delete product
# -------------------------------
@router.delete("/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    db_product = crud.get_product(db, product_id)
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    crud.delete_product(db, db_product)
    return response_format(None, "Product deleted successfully")
