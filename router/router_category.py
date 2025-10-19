from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import schemas, crud, models
from database import get_db
from roles import require_role  # your role dependency

router = APIRouter(prefix="/categories", tags=["Categories"])

def response_format(data=None, message="Success", success=True):
    return {"success": success, "message": message, "data": data}

# ---------------------- Create Category ----------------------
@router.post("/")
def create_category(category: schemas.CategoryCreate, db: Session = Depends(get_db), 
                    current_user: models.User = Depends(require_role("admin", "superadmin"))):
    db_category = crud.create_category(db, category)
    return response_format(db_category, "Category created successfully")

# ---------------------- Get Category by ID ----------------------
# ---------------------- Get Products by Category ID ----------------------
@router.get("/{category_id}/products")
def get_products_by_category(category_id: int, db: Session = Depends(get_db)):
    # Check if category exists
    db_category = crud.get_category(db, category_id)
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Get products in that category
    products = db.query(models.Product).filter(models.Product.category_id == category_id).all()

    return response_format(products, f"Products in category {db_category.name} retrieved successfully")


# ---------------------- Get All Categories ----------------------
@router.get("/", )
def get_categories(db: Session = Depends(get_db)):
    db_categories = crud.get_categories(db)
    return response_format(db_categories, "All categories retrieved successfully")

# ---------------------- Update Category ----------------------
@router.put("/{category_id}")
def update_category(category_id: int, category: schemas.CategoryUpdate, db: Session = Depends(get_db),
                    current_user: models.User = Depends(require_role("admin", "superadmin"))):
    db_category = crud.update_category(db, category_id, category)
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    return response_format(db_category, "Category updated successfully")

# ---------------------- Delete Category ----------------------
@router.delete("/{category_id}")
def delete_category(category_id: int, db: Session = Depends(get_db),
                    current_user: models.User = Depends(require_role("superadmin"))):
    db_category = crud.delete_category(db, category_id)
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found or has products")
    return response_format(db_category, "Category deleted successfully")
