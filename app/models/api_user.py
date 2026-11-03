
from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


class AuthBase(DeclarativeBase):
    pass


class APIUser(AuthBase):
    __tablename__ = "api_users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    username: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )

    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    customer_access: Mapped[list["CustomerAccess"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class CustomerAccess(AuthBase):
    __tablename__ = "api_user_customers"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("api_users.id", ondelete="CASCADE"),
        primary_key=True,
    )

    customer_id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
    )

    user: Mapped["APIUser"] = relationship(
        back_populates="customer_access",
    )
