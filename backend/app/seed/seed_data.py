"""
Seed Data Script
Loads real data from Notebooks datasets to populate the database.
"""
import json
import pandas as pd
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.auth.models import User
from app.products.models import Category, Product
from app.orders.models import Table, Order, OrderItem
from app.payments.models import Payment
from app.customers.models import Customer
from app.ai.anomalies.models import AnomalyAlert


def _candidate_data_paths(filename: str) -> list[Path]:
    """Return possible locations for bundled seed datasets."""
    configured = Path(settings.NOTEBOOKS_PATH)
    bundled = Path("Ai models")
    return [
        configured / "datasets" / filename,
        configured / "data" / "raw" / filename,
        bundled / "datasets" / filename,
        bundled / "data" / "raw" / filename,
    ]


def _first_existing_data_path(filename: str) -> Path | None:
    for path in _candidate_data_paths(filename):
        if path.exists():
            return path
    return None


def seed_all(db: Session):
    """Run all seeders if database is empty."""
    if db.query(User).count() > 0:
        print("[SEED] Database already populated, skipping.")
        seed_orders_and_payments(db)
        # Still seed ingredients if they don't exist yet (new feature)
        from app.seed.seed_ingredients import seed_ingredients
        seed_ingredients(db)
        return

    print("[SEED] Seeding database...")
    seed_users(db)
    seed_categories_and_products(db)
    seed_tables(db)
    seed_customers(db)
    seed_orders_and_payments(db)
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
    dataset_path = _first_existing_data_path("enterprise_pos_dataset.csv")
    if dataset_path:
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
    path = _first_existing_data_path("customers.csv")

    if not path:
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


def seed_orders_and_payments(db: Session, max_orders: int = 25000):
    """Replay real transaction rows into POS order/payment tables for reports."""
    dataset_note = "Seeded from enterprise_pos_dataset.csv source order"
    dataset_orders = db.query(Order).filter(Order.notes.like(f"{dataset_note}%")).all()
    total_orders = db.query(Order).count()
    if total_orders > 0 and not dataset_orders:
        print("  [SEED] Non-dataset orders already exist, skipping transaction seed")
        return
    if len(dataset_orders) >= max_orders:
        print(f"  [SEED] Dataset orders already populated ({len(dataset_orders)} orders), skipping")
        return
    if dataset_orders:
        dataset_order_ids = [order.id for order in dataset_orders]
        db.query(Payment).filter(Payment.order_id.in_(dataset_order_ids)).delete(synchronize_session=False)
        db.query(OrderItem).filter(OrderItem.order_id.in_(dataset_order_ids)).delete(synchronize_session=False)
        db.query(Order).filter(Order.id.in_(dataset_order_ids)).delete(synchronize_session=False)
        db.commit()
        print(f"  [SEED] Removed {len(dataset_order_ids)} previous dataset-seeded orders")

    path = _first_existing_data_path("enterprise_pos_dataset.csv")
    if not path:
        print("  [SEED] No enterprise_pos_dataset.csv found, skipping orders")
        return

    products_by_name = {product.name: product for product in db.query(Product).all()}
    if not products_by_name:
        print("  [SEED] Products missing, skipping orders")
        return

    users_by_username = {user.username: user for user in db.query(User).all()}
    cashier_fallback = users_by_username.get("cashier1") or users_by_username.get("admin")
    if not cashier_fallback:
        print("  [SEED] Cashier user missing, skipping orders")
        return

    cashier_map = {
        "C01": users_by_username.get("cashier1", cashier_fallback),
        "C02": users_by_username.get("cashier1", cashier_fallback),
        "C03": users_by_username.get("cashier2", cashier_fallback),
        "C04": users_by_username.get("cashier2", cashier_fallback),
    }
    customers = {customer.id for customer in db.query(Customer.id).all()}
    tables_by_number = {table.number: table for table in db.query(Table).all()}

    df = pd.read_csv(path, sep="|")
    df = df[df["is_voided"].astype(str).str.lower() != "true"].copy()
    df = df[df["item_name"].isin(products_by_name.keys())]
    df["source_created_at"] = pd.to_datetime(
        df["order_date"].astype(str) + " " + df["order_time"].astype(str),
        errors="coerce",
    )
    df = df.dropna(subset=["source_created_at"])
    if df.empty:
        print("  [SEED] No usable transaction rows found, skipping orders")
        return

    latest_source_date = df["source_created_at"].max().to_pydatetime()
    date_shift = datetime.utcnow() - latest_source_date
    ordered_source_ids = (
        df[["order_id", "source_created_at"]]
        .drop_duplicates("order_id")
        .sort_values("source_created_at")
        .tail(max_orders)
    )
    order_ids = ordered_source_ids["order_id"].tolist()
    df = df[df["order_id"].isin(order_ids)].copy()

    created_orders = 0
    created_items = 0
    for source_order_id, group in df.groupby("order_id", sort=True):
        first = group.iloc[0]
        table = None
        if not pd.isna(first["table_number"]):
            table_number = int(first["table_number"])
            table = tables_by_number.get(table_number)
            if table is None:
                table = Table(number=table_number, section="Dataset", capacity=4, status="available")
                db.add(table)
                db.flush()
                tables_by_number[table_number] = table

        source_created_at = first["source_created_at"]
        created_at = source_created_at.to_pydatetime() + date_shift

        customer_id = None if pd.isna(first["customer_id"]) else int(first["customer_id"])
        cashier = cashier_map.get(str(first["cashier_id"]), cashier_fallback)
        order = Order(
            table_id=table.id if table else None,
            customer_id=customer_id if customer_id and customer_id in customers else None,
            cashier_id=cashier.id,
            status="paid",
            total_amount=0.0,
            discount_pct=float(first.get("discount_pct", 0.0) or 0.0),
            discount_amount=0.0,
            notes=f"{dataset_note} {source_order_id}",
            created_at=created_at,
            updated_at=created_at,
        )
        db.add(order)
        db.flush()

        gross_total = 0.0
        net_total = 0.0
        for _, row in group.iterrows():
            product = products_by_name.get(row["item_name"])
            if not product:
                continue
            unit_price = round(float(row["price"]), 2)
            line_total = round(float(row["line_total"]), 2)
            gross_total += unit_price
            net_total += line_total
            db.add(OrderItem(
                order_id=order.id,
                product_id=product.id,
                product_name=product.name,
                quantity=1,
                unit_price=unit_price,
                discount_pct=float(row.get("discount_pct", 0.0) or 0.0),
                subtotal=line_total,
                notes=f"Source detail {row['order_details_id']}",
            ))
            created_items += 1

        order.total_amount = round(net_total, 2)
        order.discount_amount = round(max(gross_total - net_total, 0.0), 2)
        db.add(Payment(
            order_id=order.id,
            amount=order.total_amount,
            method="unknown" if pd.isna(first["payment_method"]) else str(first["payment_method"]),
            status="completed",
            reference=f"dataset-order-{source_order_id}",
            created_at=created_at,
        ))
        created_orders += 1

    db.commit()
    print(f"  [SEED] Created {created_orders} orders, {created_items} order items, {created_orders} payments")


def seed_anomaly_alerts(db: Session):
    """Load real anomaly alerts from Module 3."""
    from app.ai.anomalies.service import get_alerts_data

    alerts = get_alerts_data()
    if not alerts:
        print("  [SEED] No anomaly alerts CSV found, skipping")
        return

    count = 0
    for row in alerts[:200]:
        alert = AnomalyAlert(
            order_id=str(row.get("order_id", f"ORD-{count}")),
            risk_score=float(row.get("risk_score", 0.5)),
            risk_level=str(row.get("risk_level", "ALERTE")),
            predicted_label=int(row.get("predicted_label", 0)),
            anomaly_type=str(row.get("anomaly_type", "")),
            reason_codes=str(row.get("reason_codes", "")),
            alert_explanation=str(row.get("alert_explanation", "Anomaly detected by ML model")),
            model_name=str(row.get("model_name", "RandomForest")),
        )
        db.add(alert)
        count += 1

    db.commit()
    print(f"  [SEED] Created {count} anomaly alerts")
