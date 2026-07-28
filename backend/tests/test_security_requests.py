import base64
import json
import os
import tempfile

os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.gettempdir()}/pos_security_tests.db"
os.environ["JWT_SECRET_KEY"] = "test-secret-for-security-tests-please-replace-1234567890"
os.environ["ENVIRONMENT"] = "test"
os.environ["DEBUG"] = "false"
os.environ["ENABLE_API_DOCS"] = "true"
os.environ["SEED_DEMO_DATA"] = "false"
os.environ["REFRESH_COOKIE_SECURE"] = "false"

from fastapi.testclient import TestClient

from app.auth.models import User
from app.audit.models import AuditLog
from app.core.database import Base, SessionLocal, engine
from app.core.security import hash_password
from app.main import app
from app.orders.models import Order
from app.products.models import Ingredient
from app.stock.models import IngredientStockMovement


def _reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        admin = User(
            username="admin",
            full_name="Admin User",
            email="admin@example.test",
            hashed_password=hash_password("AdminPassword123!"),
            role="admin",
        )
        cashier_a = User(
            username="cashier_a",
            full_name="Cashier A",
            email="cashier-a@example.test",
            hashed_password=hash_password("CashierPassword123!"),
            role="cashier",
        )
        cashier_b = User(
            username="cashier_b",
            full_name="Cashier B",
            email="cashier-b@example.test",
            hashed_password=hash_password("CashierPassword123!"),
            role="cashier",
        )
        db.add_all([admin, cashier_a, cashier_b])
        db.flush()
        other_order = Order(cashier_id=cashier_b.id, status="draft")
        own_order = Order(cashier_id=cashier_a.id, status="draft")
        db.add_all([other_order, own_order])
        db.add(Ingredient(
            name="Test Tomatoes",
            unit="kg",
            current_stock=10.0,
            low_stock_threshold=5.0,
            cost_per_unit=2.0,
            supplier="Test Supplier",
            category="Vegetable",
        ))
        db.commit()
        return {"other_order_id": other_order.id, "own_order_id": own_order.id}
    finally:
        db.close()


def _login(client: TestClient, username: str, password: str = "CashierPassword123!") -> str:
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def _alg_none_token(subject: int) -> str:
    def encode(part: dict) -> str:
        raw = json.dumps(part, separators=(",", ":")).encode("utf-8")
        return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")

    return f'{encode({"alg": "none", "typ": "JWT"})}.{encode({"sub": str(subject), "role": "admin"})}.'


def test_cashier_cannot_call_admin_route():
    _reset_db()
    with TestClient(app, raise_server_exceptions=False) as client:
        token = _login(client, "cashier_a")
        response = client.get("/api/users", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 403


def test_alg_none_jwt_is_rejected():
    _reset_db()
    with TestClient(app, raise_server_exceptions=False) as client:
        token = _alg_none_token(1)
        response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401


def test_cashier_cannot_access_another_cashiers_order_by_id():
    ids = _reset_db()
    with TestClient(app, raise_server_exceptions=False) as client:
        token = _login(client, "cashier_a")
        response = client.get(
            f"/api/orders/{ids['other_order_id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403


def test_purchase_order_receive_increments_stock_and_audits():
    _reset_db()
    with TestClient(app, raise_server_exceptions=False) as client:
        token = _login(client, "admin", "AdminPassword123!")
        headers = {"Authorization": f"Bearer {token}"}

        db = SessionLocal()
        try:
            ingredient = db.query(Ingredient).filter(Ingredient.name == "Test Tomatoes").one()
            ingredient_id = ingredient.id
            starting_stock = ingredient.current_stock
        finally:
            db.close()

        create_response = client.post(
            "/api/stock/purchase-orders",
            json={"ingredient_id": ingredient_id, "quantity_ordered": 7.5},
            headers=headers,
        )
        assert create_response.status_code == 200, create_response.text
        purchase_order = create_response.json()
        assert purchase_order["status"] == "pending"
        assert purchase_order["ingredient_name"] == "Test Tomatoes"

        pending_response = client.get("/api/stock/purchase-orders?status=pending", headers=headers)
        assert pending_response.status_code == 200
        assert any(po["id"] == purchase_order["id"] for po in pending_response.json())

        receive_response = client.post(
            f"/api/stock/purchase-orders/{purchase_order['id']}/receive",
            headers=headers,
        )
        assert receive_response.status_code == 200, receive_response.text
        assert receive_response.json()["status"] == "received"

        db = SessionLocal()
        try:
            ingredient = db.query(Ingredient).filter(Ingredient.id == ingredient_id).one()
            assert ingredient.current_stock == starting_stock + 7.5
            movement = db.query(IngredientStockMovement).filter(
                IngredientStockMovement.ingredient_id == ingredient_id,
                IngredientStockMovement.reason == "restock",
            ).one()
            assert movement.quantity_change == 7.5
            actions = {
                row.action for row in db.query(AuditLog)
                .filter(AuditLog.entity_type == "purchase_order")
                .all()
            }
            assert {"create_purchase_order", "receive_purchase_order"} <= actions
        finally:
            db.close()


def test_cashier_cannot_manage_purchase_orders():
    _reset_db()
    with TestClient(app, raise_server_exceptions=False) as client:
        token = _login(client, "cashier_a")
        response = client.get(
            "/api/stock/purchase-orders",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403


def test_cashier_cannot_read_audit_logs():
    _reset_db()
    with TestClient(app, raise_server_exceptions=False) as client:
        token = _login(client, "cashier_a")
        response = client.get(
            "/api/audit/logs",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403
