from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, String


class Base(DeclarativeBase):
    pass


class UserBase(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)


class ReportBase(Base):
    __tablename__ = "reports"
    id: Mapped[int] = mapped_column(primary_key=True)
    message: Mapped[str] = mapped_column(String())
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))


