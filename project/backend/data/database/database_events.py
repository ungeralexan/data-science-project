
from sqlalchemy import create_engine, Column, Integer, String, Text, JSON
from sqlalchemy.orm import declarative_base, sessionmaker

from config import DATABASE_URL  # pylint: disable=import-error

#
#   This file sets up the database connection and defines ORM models for events and users.
#   ORM models are Python classes that map to database tables, allowing us to interact with the database using Python code.
#

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

# Create a base class for our ORM models. A base is a class that other ORM models will inherit from.
Base = declarative_base() 

# Define the EventORM class which represents the "events" table in the database.
# By adding (Base) we make EventORM inherit from the Base class we created earlier.
class EventORM(Base):
    __tablename__ = "events" # Name of the table in the database.

    # Define the columns of the table.
    id = Column(Integer, primary_key=True, index=True, autoincrement=True) # Primary key column, auto-incremented integer.
    title = Column(String, index=True)
    start_date = Column(String)
    end_date = Column(String)
    start_time = Column(String, nullable=True)
    end_time = Column(String, nullable=True)
    location = Column(String, nullable=True)  # Kept for backward compatibility / full address string
    street = Column(String, nullable=True)
    house_number = Column(String, nullable=True)
    zip_code = Column(String, nullable=True)
    city = Column(String, nullable=True)
    country = Column(String, nullable=True)
    room = Column(String, nullable=True)
    floor = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    speaker = Column(String, nullable=True)
    organizer = Column(String, nullable=True)
    registration_needed = Column(String, nullable=True)
    url = Column(String, nullable=True)
    image_key = Column(String, nullable=True)
    like_count = Column(Integer, default=0, nullable=False)  # Number of likes for the event


# Define the UserORM class which represents the "users" table in the database.
class UserORM(Base):
    __tablename__ = "users"  # Name of the table in the database.

    # Define the columns of the table.
    user_id = Column(Integer, primary_key=True, index=True, autoincrement=True)  # Primary key column, auto-incremented integer.
    password = Column(String, nullable=False)  # Hashed password
    email = Column(String, unique=True, index=True, nullable=False)  # Unique email address
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    interest_keys = Column(JSON, nullable=True)  # List of interest keywords
    interest_text = Column(Text, nullable=True)  # Free-form interest description
    suggested_event_ids = Column(JSON, nullable=True)  # List of suggested event IDs


# Function to initialize the database and create tables.
def init_db() -> None:
    Base.metadata.create_all(bind=engine) # Create all tables in the database based on the ORM models defined.
