"""
POS Intelligent Timsoft — FastAPI Main Application
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db, SessionLocal

# Import all routers
from app.auth.routes import router as auth_router
from app.products.routes import router as products_router
from app.orders.routes import router as orders_router
from app.payments.routes import router as payments_router
from app.stock.routes import router as stock_router
from app.customers.routes import router as customers_router
from app.reporting.routes import router as reporting_router
from app.users.routes import router as users_router
from app.audit.routes import router as audit_router
from app.ai.recommendations.routes import router as ai_rec_router
from app.ai.forecasting.routes import router as ai_forecast_router
from app.ai.anomalies.routes import router as ai_anomaly_router
from app.ai.segmentation.routes import router as ai_seg_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print(f"[START] Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    init_db()
    print("[OK] Database tables created")

    if settings.SEED_DEMO_DATA:
        from app.seed.seed_data import seed_all
        db = SessionLocal()
        try:
            seed_all(db)
        finally:
            db.close()
    else:
        print("[SEED] Demo data seeding disabled")

    # Load AI Models
    from app.ai.recommendations.service import load_association_rules
    load_association_rules()

    yield

    # Shutdown
    print("[STOP] Shutting down")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Système POS Intelligent pour Cafés et Restaurants — Timsoft PFE",
    lifespan=lifespan,
    debug=settings.DEBUG,
    docs_url="/docs" if settings.ENABLE_API_DOCS else None,
    redoc_url="/redoc" if settings.ENABLE_API_DOCS else None,
    openapi_url="/openapi.json" if settings.ENABLE_API_DOCS else None,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
    response.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; frame-ancestors 'none'; object-src 'none'; base-uri 'self'",
    )
    if settings.ENVIRONMENT == "production":
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled request error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})

# Register all routers
app.include_router(auth_router)
app.include_router(products_router)
app.include_router(orders_router)
app.include_router(payments_router)
app.include_router(stock_router)
app.include_router(customers_router)
app.include_router(reporting_router)
app.include_router(users_router)
app.include_router(audit_router)
app.include_router(ai_rec_router)
app.include_router(ai_forecast_router)
app.include_router(ai_anomaly_router)
app.include_router(ai_seg_router)


@app.get("/")
def root():
    response = {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
    }
    if settings.ENABLE_API_DOCS:
        response["docs"] = "/docs"
    return response


@app.get("/api/health")
def health():
    return {"status": "healthy"}
