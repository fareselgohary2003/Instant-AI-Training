from pathlib import Path
from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATABASE_PATH = PROJECT_ROOT / "ai_task_agent.db"

DATABASE_URL = f"sqlite:///{DATABASE_PATH.as_posix()}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for SQLAlchemy database models."""
    pass


def get_db() -> Generator[Session, None, None]:
    """Provide a database session and always close it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _safe_migrate() -> None:
    """Safely apply schema enhancements to existing SQLite database without data loss."""
    try:
        with engine.connect() as conn:
            # Check if workflow_runs exists
            res = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='workflow_runs'")
            ).fetchone()
            if res:
                col_info = conn.execute(text("PRAGMA table_info(workflow_runs)")).fetchall()
                col_names = [c[1] for c in col_info]
                if "duration_seconds" not in col_names:
                    conn.execute(text("ALTER TABLE workflow_runs ADD COLUMN duration_seconds FLOAT"))
                if "requires_approval" not in col_names:
                    conn.execute(text("ALTER TABLE workflow_runs ADD COLUMN requires_approval BOOLEAN DEFAULT 0"))
                conn.commit()
    except Exception as exc:
        print(f"Warning: Safe database migration encountered an issue: {exc}")


def init_db() -> None:
    """Create all registered database tables and apply safe migrations."""
    # Import models so SQLAlchemy registers them before creating tables.
    from app.db.models import WorkflowRun, WorkflowStep, ApprovalRequest  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _safe_migrate()
