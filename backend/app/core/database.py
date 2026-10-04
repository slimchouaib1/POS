from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import settings


engine_kwargs = {"echo": settings.DEBUG}
if settings.DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    **engine_kwargs
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def init_db():
    """Create all tables. Called on startup."""
    # Import all models so they register with Base
    import app.auth.models  # noqa
    import app.products.models  # noqa
    import app.orders.models  # noqa
    import app.payments.models  # noqa
    import app.stock.models  # noqa
    import app.suppliers.models  # noqa
    import app.customers.models  # noqa
    import app.ai.anomalies.models  # noqa
    import app.audit.models  # noqa

    Base.metadata.create_all(bind=engine)

    # Lightweight auto-migration for Table columns if using postgres
    try:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE tables ADD COLUMN IF NOT EXISTS current_covers INTEGER DEFAULT 0;"))
            conn.execute(text("ALTER TABLE tables ADD COLUMN IF NOT EXISTS reservation_time VARCHAR(50) DEFAULT '';"))
    except Exception as e:
        print(f"[DB] Migration note: {e}")

