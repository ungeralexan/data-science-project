
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import declarative_base, sessionmaker

# SQLite database URL
DATABASE_URL = "sqlite:///./data/database/events.db"

# Create the database engine. An engine is an object that manages the connection to the database.
engine = create_engine(
    DATABASE_URL, # Database URL

    # SQLite specific argument to allow multiple threads. 
    # A thread is a sequence of instructions that can be managed independently by a scheduler.
    # This allows multiple threads to handle different user requests simultaneously.
    connect_args={"check_same_thread": False}, 
)

# Create a configured "Session" class. A session is used to interact with the database.
SessionLocal = sessionmaker(
    autocommit = False, # Disable autocommit mode. (This means changes are not automatically saved to the database.)
    autoflush = False,  # Disable autoflush mode. (This means changes are not automatically sent to the database.)
    bind = engine # Bind the session to the engine. (This connects the session to our database)
)

# Create a base class for our ORM models.
Base = declarative_base() 

# Define the EventORM class which represents the "events" table in the database.
class EventORM(Base):
    __tablename__ = "events" # Name of the table in the database.

    # Define the columns of the table.
    id = Column(Integer, primary_key=True, index=True, autoincrement=True) # Primary key column, auto-incremented integer.
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

# Function to initialize the database and create tables.
def init_db() -> None:
    Base.metadata.create_all(bind=engine) # Create all tables in the database based on the ORM models defined.
