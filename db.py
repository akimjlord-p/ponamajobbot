from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from models import Base, UserBase, ReportBase # noqa: F401

engine = create_async_engine("sqlite+aiosqlite:///db.db", echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

def create_db():
    Base.metadata.create_all(engine)