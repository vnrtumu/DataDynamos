"""SQLite engine + session management (SQLModel)."""

from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine

from app.config import settings

# Ensure the data dir exists before SQLite tries to create the file there.
settings.data_path.mkdir(parents=True, exist_ok=True)

_DB_PATH = settings.data_path / "app.db"
engine = create_engine(
    f"sqlite:///{_DB_PATH}",
    connect_args={"check_same_thread": False},
)


def init_db() -> None:
    """Create all tables. Called on app startup."""
    # Import models so their tables register on SQLModel.metadata.
    import app.models  # noqa: F401

    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a DB session."""
    with Session(engine) as session:
        yield session
