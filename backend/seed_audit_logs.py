"""Seed audit logs with realistic sample data."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
import random
from app.core.database import SessionLocal
from app.audit.models import AuditLog
from app.auth.models import User

db = SessionLocal()

users = db.query(User).all()
if not users:
    print("No users found, run the main seed first.")
    sys.exit(1)

user_map = {u.role: u for u in users}

# Check if logs already exist
existing = db.query(AuditLog).count()
if existing > 10:
    print(f"Already {existing} audit logs, skipping seed.")
    sys.exit(0)

now = datetime.utcnow()
logs = []

# Login events
for i in range(15):
    u = random.choice(users)
    ts = now - timedelta(hours=random.randint(1, 168))
    logs.append(AuditLog(
        user_id=u.id, action="login", entity_type="auth",
        details=f"User {u.full_name} logged in",
        created_at=ts,
    ))

# Failed logins
for i in range(3):
    ts = now - timedelta(hours=random.randint(1, 72))
    logs.append(AuditLog(
        user_id=None, action="login_failed", entity_type="auth",
        details=f"Failed login attempt for username: unknown_user{i}",
        created_at=ts,
    ))

# Order events
for i in range(20):
    u = random.choice([u for u in users if u.role in ("cashier", "admin", "manager")])
    order_id = random.randint(1, 50)
    ts = now - timedelta(hours=random.randint(1, 168))
    action = random.choice(["create_order", "order_paid", "order_in_progress", "order_served"])
    items_count = random.randint(1, 8)
    total = round(random.uniform(5, 120), 2)
    if action == "create_order":
        detail = f"Created order #{order_id} with {items_count} items, total {total} DT"
    elif action == "order_paid":
        detail = f"Order #{order_id} status changed: served -> paid"
    elif action == "order_in_progress":
        detail = f"Order #{order_id} status changed: draft -> in_progress"
    else:
        detail = f"Order #{order_id} status changed: in_progress -> served"
    logs.append(AuditLog(
        user_id=u.id, action=action, entity_type="order",
        entity_id=order_id, details=detail, created_at=ts,
    ))

# Payment events
for i in range(12):
    u = random.choice([u for u in users if u.role in ("cashier", "admin", "manager")])
    order_id = random.randint(1, 50)
    payment_id = random.randint(1, 30)
    amount = round(random.uniform(8, 95), 2)
    method = random.choice(["cash", "card", "cash", "card"])
    ts = now - timedelta(hours=random.randint(1, 168))
    logs.append(AuditLog(
        user_id=u.id, action="payment", entity_type="payment",
        entity_id=payment_id, details=f"Payment of {amount} DT via {method} for order #{order_id}",
        created_at=ts,
    ))

# Product updates
for i in range(8):
    u = user_map.get("admin") or users[0]
    product_id = random.randint(1, 20)
    ts = now - timedelta(hours=random.randint(1, 168))
    action = random.choice(["update_product", "update_product", "delete_product"])
    detail = f"Updated product #{product_id} price" if action == "update_product" else f"Deleted product #{product_id}"
    logs.append(AuditLog(
        user_id=u.id, action=action, entity_type="product",
        entity_id=product_id, details=detail, created_at=ts,
    ))

# Stock adjustments
for i in range(6):
    u = user_map.get("stock_manager") or users[0]
    ts = now - timedelta(hours=random.randint(1, 120))
    logs.append(AuditLog(
        user_id=u.id, action="stock_adjust", entity_type="ingredient",
        entity_id=random.randint(1, 30),
        details=f"Stock adjustment: +{random.randint(50, 500)} units",
        created_at=ts,
    ))

# User management
u = user_map.get("admin") or users[0]
for i in range(3):
    ts = now - timedelta(hours=random.randint(24, 168))
    logs.append(AuditLog(
        user_id=u.id, action="create_user", entity_type="user",
        entity_id=random.randint(1, 5),
        details=f"Created user with role cashier",
        created_at=ts,
    ))

# Cancelled orders
for i in range(4):
    uc = random.choice([u for u in users if u.role in ("cashier", "manager")])
    order_id = random.randint(1, 50)
    ts = now - timedelta(hours=random.randint(1, 120))
    logs.append(AuditLog(
        user_id=uc.id, action="order_cancelled", entity_type="order",
        entity_id=order_id,
        details=f"Order #{order_id} cancelled. Reason: Customer left",
        created_at=ts,
    ))

for log in logs:
    db.add(log)
db.commit()
print(f"[SEED] Created {len(logs)} audit log entries.")
db.close()
