# database.py
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "sqlite:///./data/database/events.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit = False, autoflush = False, bind = engine)

Base = declarative_base()

class EventORM(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String, index=True)
    start_date = Column(String)
    end_date = Column(String)
    start_time = Column(String, nullable=True)
    end_time = Column(String, nullable=True)
    location = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    speaker = Column(String, nullable=True)
    organizer = Column(String, nullable=True)
    registration_needed = Column(String, nullable=True)
    url = Column(String, nullable=True)
    image_key = Column(String, nullable=True)

def init_db() -> None:
    Base.metadata.create_all(bind=engine)
