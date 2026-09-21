from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Unified SQLAlchemy 2.0 Declarative Base.
    All ORM models in app.models inherit from this base class.
    """
    pass
