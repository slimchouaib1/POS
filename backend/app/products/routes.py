from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.deps import get_db, get_current_user, require_role
from app.core.config import settings
from app.products.models import Category, Product, Ingredient, ProductIngredient
from app.audit.models import AuditLog
from app.products.schemas import (
    IngredientCreate, IngredientUpdate, IngredientOut,
    RecipeLineCreate, RecipeLineUpdate, RecipeLineOut,
    CategoryCreate, CategoryOut, ProductCreate, ProductUpdate, ProductOut,
)

router = APIRouter(prefix="/api", tags=["Products & Categories"])


# ─── Categories ─────────────────────────────────────
@router.get("/categories", response_model=list[CategoryOut])
def list_categories(
    db: Session = Depends(get_db),
    _=Depends(require_role(settings.ROLE_ADMIN, settings.ROLE_MANAGER, settings.ROLE_CASHIER, settings.ROLE_STOCK_MANAGER)),
):
    cats = db.query(Category).order_by(Category.display_order).all()
    result = []
    for c in cats:
        count = db.query(Product).filter(Product.category_id == c.id).count()
        out = CategoryOut.model_validate(c)
        out.product_count = count
        result.append(out)
    return result


@router.post("/categories", response_model=CategoryOut)
def create_category(
    data: CategoryCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(settings.ROLE_ADMIN, settings.ROLE_MANAGER)),
):
    cat = Category(**data.model_dump())
    db.add(cat)
    db.flush()
    db.add(AuditLog(
        user_id=current_user.id,
        action="create_category",
        entity_type="category",
        entity_id=cat.id,
        details=f"Created category {cat.name}",
    ))
    db.commit()
    db.refresh(cat)
    out = CategoryOut.model_validate(cat)
    out.product_count = 0
    return out


@router.put("/categories/{cat_id}", response_model=CategoryOut)
def update_category(
    cat_id: int,
    data: CategoryCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(settings.ROLE_ADMIN, settings.ROLE_MANAGER)),
):
    cat = db.query(Category).filter(Category.id == cat_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Catégorie introuvable")
    for k, v in data.model_dump().items():
        setattr(cat, k, v)
    db.add(AuditLog(
        user_id=current_user.id,
        action="update_category",
        entity_type="category",
        entity_id=cat.id,
        details=f"Updated category {cat.name}",
    ))
    db.commit()
    db.refresh(cat)
    count = db.query(Product).filter(Product.category_id == cat.id).count()
    out = CategoryOut.model_validate(cat)
    out.product_count = count
    return out


# ─── Products ───────────────────────────────────────
@router.get("/products", response_model=list[ProductOut])
def list_products(
    category_id: Optional[int] = Query(None, gt=0),
    section: Optional[str] = Query(None, max_length=80),
    search: Optional[str] = Query(None, max_length=100),
    available_only: bool = Query(False),
    db: Session = Depends(get_db),
    _=Depends(require_role(settings.ROLE_ADMIN, settings.ROLE_MANAGER, settings.ROLE_CASHIER, settings.ROLE_STOCK_MANAGER)),
):
    q = db.query(Product)
    if category_id:
        q = q.filter(Product.category_id == category_id)
    if section:
        q = q.filter(Product.section == section)
    if search:
        q = q.filter(Product.name.ilike(f"%{search}%"))
    if available_only:
        q = q.filter(Product.is_available == True)
    products = q.order_by(Product.name).all()
    result = []
    for p in products:
        out = ProductOut.model_validate(p)
        out.category_name = p.category.name if p.category else ""
        result.append(out)
    return result


@router.post("/products", response_model=ProductOut)
def create_product(
    data: ProductCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(settings.ROLE_ADMIN, settings.ROLE_MANAGER)),
):
    if not db.query(Category).filter(Category.id == data.category_id).first():
        raise HTTPException(status_code=404, detail="Catégorie introuvable")
    product = Product(**data.model_dump())
    db.add(product)
    db.flush()
    db.add(AuditLog(
        user_id=current_user.id,
        action="create_product",
        entity_type="product",
        entity_id=product.id,
        details=f"Created product {product.name}",
    ))
    db.commit()
    db.refresh(product)
    out = ProductOut.model_validate(product)
    out.category_name = product.category.name if product.category else ""
    return out


@router.put("/products/{product_id}", response_model=ProductOut)
def update_product(
    product_id: int,
    data: ProductUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(settings.ROLE_ADMIN, settings.ROLE_MANAGER)),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Produit introuvable")
    if data.category_id is not None and not db.query(Category).filter(Category.id == data.category_id).first():
        raise HTTPException(status_code=404, detail="Catégorie introuvable")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(product, k, v)
    db.add(AuditLog(
        user_id=current_user.id,
        action="update_product",
        entity_type="product",
        entity_id=product.id,
        details=f"Updated product {product.name}",
    ))
    db.commit()
    db.refresh(product)
    out = ProductOut.model_validate(product)
    out.category_name = product.category.name if product.category else ""
    return out


@router.patch("/products/{product_id}/toggle", response_model=ProductOut)
def toggle_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(settings.ROLE_ADMIN, settings.ROLE_MANAGER)),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Produit introuvable")
    product.is_available = not product.is_available
    db.add(AuditLog(
        user_id=current_user.id,
        action="toggle_product",
        entity_type="product",
        entity_id=product.id,
        details=f"Set product {product.name} availability to {product.is_available}",
    ))
    db.commit()
    db.refresh(product)
    out = ProductOut.model_validate(product)
    out.category_name = product.category.name if product.category else ""
    return out


@router.delete("/products/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(settings.ROLE_ADMIN, settings.ROLE_MANAGER)),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Produit introuvable")
    product_name = product.name
    db.delete(product)
    db.add(AuditLog(
        user_id=current_user.id,
        action="delete_product",
        entity_type="product",
        entity_id=product_id,
        details=f"Deleted product {product_name}",
    ))
    db.commit()
    return {"detail": "Produit supprimé"}


# ─── Ingredients ────────────────────────────────────────
@router.get("/ingredients", response_model=list[IngredientOut])
def list_ingredients(
    db: Session = Depends(get_db),
    _=Depends(require_role(settings.ROLE_ADMIN, settings.ROLE_MANAGER, settings.ROLE_CASHIER, settings.ROLE_STOCK_MANAGER)),
):
    return db.query(Ingredient).order_by(Ingredient.name).all()


@router.get("/ingredients/{ingredient_id}", response_model=IngredientOut)
def get_ingredient(
    ingredient_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_role(settings.ROLE_ADMIN, settings.ROLE_MANAGER, settings.ROLE_CASHIER, settings.ROLE_STOCK_MANAGER)),
):
    ing = db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()
    if not ing:
        raise HTTPException(status_code=404, detail="Ingrédient introuvable")
    return ing


@router.post("/ingredients", response_model=IngredientOut)
def create_ingredient(
    data: IngredientCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(settings.ROLE_ADMIN, settings.ROLE_MANAGER)),
):
    existing = db.query(Ingredient).filter(Ingredient.name == data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Un ingrédient avec ce nom existe déjà")
    
    try:
        ing = Ingredient(**data.model_dump())
        db.add(ing)
        db.commit()
        db.refresh(ing)
        
        # Audit Log
        db.add(AuditLog(
            user_id=current_user.id,
            action="create_ingredient",
            entity_type="ingredient",
            entity_id=ing.id,
            details=f"Created ingredient {ing.name}"
        ))
        db.commit()
    except Exception:
        db.rollback()
        raise
        
    return ing


@router.put("/ingredients/{ingredient_id}", response_model=IngredientOut)
def update_ingredient(
    ingredient_id: int,
    data: IngredientUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(settings.ROLE_ADMIN, settings.ROLE_MANAGER)),
):
    ing = db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()
    if not ing:
        raise HTTPException(status_code=404, detail="Ingrédient introuvable")
        
    if data.name and data.name != ing.name:
        existing = db.query(Ingredient).filter(Ingredient.name == data.name).first()
        if existing:
            raise HTTPException(status_code=400, detail="Un ingrédient avec ce nom existe déjà")
            
    try:
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(ing, k, v)
        db.commit()
        db.refresh(ing)
        
        # Audit Log
        db.add(AuditLog(
            user_id=current_user.id,
            action="update_ingredient",
            entity_type="ingredient",
            entity_id=ing.id,
            details=f"Updated ingredient {ing.name}"
        ))
        db.commit()
    except Exception:
        db.rollback()
        raise
        
    return ing


@router.delete("/ingredients/{ingredient_id}")
def delete_ingredient(
    ingredient_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(settings.ROLE_ADMIN, settings.ROLE_MANAGER)),
):
    ing = db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()
    if not ing:
        raise HTTPException(status_code=404, detail="Ingrédient introuvable")
        
    # Check dependencies in recipes
    usages = db.query(ProductIngredient).filter(ProductIngredient.ingredient_id == ingredient_id).all()
    if usages:
        product_names = []
        for usage in usages[:3]:
            product_names.append(usage.product.name)
        
        err_msg = f"Used in: {', '.join(product_names)}"
        if len(usages) > 3:
            err_msg += f" and {len(usages) - 3} others"
            
        raise HTTPException(status_code=400, detail=err_msg)
        
    try:
        ing_name = ing.name
        db.delete(ing)
        
        # Audit Log
        db.add(AuditLog(
            user_id=current_user.id,
            action="delete_ingredient",
            entity_type="ingredient",
            entity_id=ingredient_id,
            details=f"Deleted ingredient {ing_name}"
        ))
        db.commit()
    except Exception:
        db.rollback()
        raise
        
    return {"detail": "Ingrédient supprimé"}


# ─── Recipes ────────────────────────────────────────────
@router.get("/products/{product_id}/recipe", response_model=list[RecipeLineOut])
def get_product_recipe(
    product_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_role(settings.ROLE_ADMIN, settings.ROLE_MANAGER, settings.ROLE_CASHIER, settings.ROLE_STOCK_MANAGER)),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Produit introuvable")
        
    recipe_lines = db.query(ProductIngredient).filter(ProductIngredient.product_id == product_id).all()
    result = []
    for line in recipe_lines:
        out = RecipeLineOut(
            ingredient_id=line.ingredient_id,
            ingredient_name=line.ingredient.name,
            unit=line.ingredient.unit,
            quantity_needed=line.quantity_needed
        )
        result.append(out)
    return result


@router.post("/products/{product_id}/recipe", response_model=RecipeLineOut)
def add_recipe_line(
    product_id: int,
    data: RecipeLineCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(settings.ROLE_ADMIN, settings.ROLE_MANAGER)),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Produit introuvable")
        
    ing = db.query(Ingredient).filter(Ingredient.id == data.ingredient_id).first()
    if not ing:
        raise HTTPException(status_code=404, detail="Ingrédient introuvable")
        
    existing = db.query(ProductIngredient).filter(
        ProductIngredient.product_id == product_id,
        ProductIngredient.ingredient_id == data.ingredient_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="This ingredient is already in the recipe. Please edit the existing line.")
        
    try:
        line = ProductIngredient(
            product_id=product_id,
            ingredient_id=data.ingredient_id,
            quantity_needed=data.quantity_needed
        )
        db.add(line)
        db.commit()
        db.refresh(line)
        
        # Audit Log
        db.add(AuditLog(
            user_id=current_user.id,
            action="update_recipe",
            entity_type="product",
            entity_id=product_id,
            details=f"Added {data.quantity_needed} {ing.unit} of {ing.name} to recipe"
        ))
        db.commit()
    except Exception:
        db.rollback()
        raise
        
    out = RecipeLineOut(
        ingredient_id=line.ingredient_id,
        ingredient_name=ing.name,
        unit=ing.unit,
        quantity_needed=line.quantity_needed
    )
    return out


@router.put("/products/{product_id}/recipe/{ingredient_id}", response_model=RecipeLineOut)
def update_recipe_line(
    product_id: int,
    ingredient_id: int,
    data: RecipeLineUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(settings.ROLE_ADMIN, settings.ROLE_MANAGER)),
):
    line = db.query(ProductIngredient).filter(
        ProductIngredient.product_id == product_id,
        ProductIngredient.ingredient_id == ingredient_id
    ).first()
    
    if not line:
        raise HTTPException(status_code=404, detail="Ligne de recette introuvable")
        
    try:
        line.quantity_needed = data.quantity_needed
        db.commit()
        db.refresh(line)
        
        # Audit Log
        db.add(AuditLog(
            user_id=current_user.id,
            action="update_recipe",
            entity_type="product",
            entity_id=product_id,
            details=f"Updated {line.ingredient.name} quantity to {data.quantity_needed} {line.ingredient.unit} in recipe"
        ))
        db.commit()
    except Exception:
        db.rollback()
        raise
        
    out = RecipeLineOut(
        ingredient_id=line.ingredient_id,
        ingredient_name=line.ingredient.name,
        unit=line.ingredient.unit,
        quantity_needed=line.quantity_needed
    )
    return out


@router.delete("/products/{product_id}/recipe/{ingredient_id}")
def delete_recipe_line(
    product_id: int,
    ingredient_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(settings.ROLE_ADMIN, settings.ROLE_MANAGER)),
):
    line = db.query(ProductIngredient).filter(
        ProductIngredient.product_id == product_id,
        ProductIngredient.ingredient_id == ingredient_id
    ).first()
    
    if not line:
        raise HTTPException(status_code=404, detail="Ligne de recette introuvable")
        
    try:
        ing_name = line.ingredient.name
        db.delete(line)
        
        # Audit Log
        db.add(AuditLog(
            user_id=current_user.id,
            action="update_recipe",
            entity_type="product",
            entity_id=product_id,
            details=f"Removed {ing_name} from recipe"
        ))
        db.commit()
    except Exception:
        db.rollback()
        raise
        
    return {"detail": "Ligne de recette supprimée"}
