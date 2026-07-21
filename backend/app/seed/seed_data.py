"""
Seed Data Script
Loads real data from Notebooks datasets to populate the database.
"""
import json
import pandas as pd
from pathlib import Path
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.auth.models import User
from app.products.models import Category, Product
from app.orders.models import Table
from app.customers.models import Customer
from app.ai.anomalies.models import AnomalyAlert


def seed_all(db: Session):
    """Run all seeders if database is empty."""
    if db.query(User).count() > 0:
        print("[SEED] Database already populated, skipping.")
        # Still seed ingredients if they don't exist yet (new feature)
        from app.seed.seed_ingredients import seed_ingredients
        seed_ingredients(db)
        return

    print("[SEED] Seeding database...")
    seed_users(db)
    seed_categories_and_products(db)
    seed_tables(db)
    seed_customers(db)
    seed_anomaly_alerts(db)
    # Seed ingredients & recipes
    from app.seed.seed_ingredients import seed_ingredients
    seed_ingredients(db)
    print("[SEED] Done!")


def seed_users(db: Session):
    """Create default users for each role."""
    required_passwords = {
        "admin": settings.SEED_ADMIN_PASSWORD,
        "manager": settings.SEED_MANAGER_PASSWORD,
        "cashier": settings.SEED_CASHIER_PASSWORD,
        "stock_manager": settings.SEED_STOCK_PASSWORD,
    }
    missing = [role for role, password in required_passwords.items() if not password]
    if missing:
        raise RuntimeError(
            "SEED_DEMO_DATA requires explicit seed passwords for roles: "
            + ", ".join(missing)
        )

    users = [
        ("admin", "Sarah Johnson", "admin@restaurant.com", required_passwords["admin"], "admin"),
        ("manager", "Michael Chen", "manager@restaurant.com", required_passwords["manager"], "manager"),
        ("cashier1", "Emily Rodriguez", "cashier1@restaurant.com", required_passwords["cashier"], "cashier"),
        ("cashier2", "Bob Martinez", "cashier2@restaurant.com", required_passwords["cashier"], "cashier"),
        ("stock", "David Kim", "stock@restaurant.com", required_passwords["stock_manager"], "stock_manager"),
    ]
    for username, full_name, email, password, role in users:
        user = User(
            username=username,
            full_name=full_name,
            email=email,
            hashed_password=hash_password(password),
            role=role,
        )
        db.add(user)
    db.commit()
    print(f"  [SEED] Created {len(users)} users")


def seed_categories_and_products(db: Session):
    """Load products from enterprise_pos_dataset.csv (pipe-separated)."""
    notebooks = Path(settings.NOTEBOOKS_PATH)

    # Load manifest for item-to-section/category mappings
    manifest_path = notebooks / "models" / "xgboost" / "manifest.json"
    item_map = {}
    sections = []
    categories_list = []

    if manifest_path.exists():
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
        item_map = manifest.get("item_map", {})
        sections = manifest.get("sections", [])
        categories_list = manifest.get("categories", [])

    # Create categories from manifest
    category_icons = {
        "Appetizer": "appetizer", "Beverage": "beverage", "Dessert": "dessert",
        "Main Course": "main", "Side": "side", "Breakfast": "breakfast",
        "Snack": "snack", "Soup": "soup",
    }

    cat_objects = {}
    if categories_list:
        for i, cat_name in enumerate(categories_list):
            cat = Category(
                name=cat_name,
                icon=category_icons.get(cat_name, "food"),
                display_order=i,
            )
            db.add(cat)
            db.flush()
            cat_objects[cat_name] = cat
    else:
        for i, name in enumerate(["Appetizers", "Main Course", "Desserts", "Beverages", "Snacks"]):
            cat = Category(name=name, display_order=i)
            db.add(cat)
            db.flush()
            cat_objects[name] = cat

    # Load products from POS dataset (PIPE separated!)
    dataset_path = notebooks / "datasets" / "enterprise_pos_dataset.csv"
    if dataset_path.exists():
        df = pd.read_csv(dataset_path, sep="|", nrows=50000)
        # Get unique items with their most common attributes
        items = df.groupby("item_name").agg({
            "price": "median",
            "category": lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else "Main Course",
            "restaurant_type": lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else "",
        }).reset_index()

        created = 0
        for _, row in items.iterrows():
            cat_name = row["category"]
            if cat_name not in cat_objects:
                cat = Category(name=cat_name, display_order=len(cat_objects))
                db.add(cat)
                db.flush()
                cat_objects[cat_name] = cat

            product = Product(
                name=row["item_name"],
                category_id=cat_objects[cat_name].id,
                section=row.get("restaurant_type", ""),
                price=round(float(row["price"]), 2),
                stock_quantity=100,
                low_stock_threshold=10,
            )
            db.add(product)
            created += 1

        db.commit()
        print(f"  [SEED] Created {len(cat_objects)} categories, {created} products")
    else:
        db.commit()
        print("  [SEED] No dataset found, categories only")


def seed_tables(db: Session):
    """Create restaurant tables across sections."""
    sections_tables = [
        ("Main Hall", 8, 4),
        ("Terrace", 4, 4),
        ("VIP", 2, 6),
        ("Bar", 2, 2),
    ]
    count = 0
    table_num = 1
    for section, num_tables, capacity in sections_tables:
        for _ in range(num_tables):
            table = Table(number=table_num, section=section, capacity=capacity)
            db.add(table)
            table_num += 1
            count += 1
    db.commit()
    print(f"  [SEED] Created {count} tables")


def seed_customers(db: Session):
    """Load customers from customers.csv."""
    notebooks = Path(settings.NOTEBOOKS_PATH)
    path = notebooks / "datasets" / "customers.csv"

    if not path.exists():
        print("  [SEED] No customers.csv found, skipping")
        return

    # Try pipe separator first, then comma
    try:
        df = pd.read_csv(path, sep="|")
        if len(df.columns) <= 1:
            df = pd.read_csv(path)
    except Exception:
        df = pd.read_csv(path)

    count = 0
    for _, row in df.head(200).iterrows():
        customer = Customer(
            id=int(row.get("customer_id", count + 1)),
            name=f"Customer {row.get('customer_id', count + 1)}",
            archetype=str(row.get("archetype", "")),
            price_tier=str(row.get("price_tier", "")),
            time_preference=str(row.get("time_preference", "")),
            day_preference=str(row.get("day_preference", "")),
        )
        db.add(customer)
        count += 1

    db.commit()
    print(f"  [SEED] Created {count} customers")


def seed_anomaly_alerts(db: Session):
    """Load real anomaly alerts from Module 3."""
    notebooks = Path(settings.NOTEBOOKS_PATH)
    alerts_path = notebooks / "Module 3" / "Final" / "exports" / "final_anomaly_alerts_dashboard.csv"

    if not alerts_path.exists():
        print("  [SEED] No anomaly alerts CSV found, skipping")
        return

    try:
        df = pd.read_csv(alerts_path, nrows=200)
    except Exception:
        print("  [SEED] Error reading anomaly alerts, skipping")
        return

    count = 0
    for _, row in df.iterrows():
        risk_score = float(row.get("risk_score", row.get("anomaly_score", 0.5)))
        risk_level = "CRITIQUE" if risk_score > 0.7 else "ALERTE" if risk_score > 0.4 else "NORMAL"

        alert = AnomalyAlert(
            order_id=str(row.get("order_id", f"ORD-{count}")),
            risk_score=risk_score,
            risk_level=risk_level,
            predicted_label=int(row.get("predicted_label", row.get("final_label", 0))),
            anomaly_type=str(row.get("anomaly_type", "")),
            reason_codes=str(row.get("reason_codes", row.get("top_features", ""))),
            alert_explanation=str(row.get("alert_explanation", row.get("explanation", "Anomaly detected by ML model"))),
            model_name=str(row.get("model_name", "RandomForest")),
        )
        db.add(alert)
        count += 1

    db.commit()
    print(f"  [SEED] Created {count} anomaly alerts")
