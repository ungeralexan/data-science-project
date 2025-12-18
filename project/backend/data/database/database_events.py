
from sqlalchemy import create_engine, Column, Integer, String, Text, JSON, ForeignKey, UniqueConstraint, event
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
import uuid

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

# Enable foreign key support for SQLite 
# This will ensure that foreign key constraints are enforced in the database.
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record): # pylint: disable=unused-argument
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

# Create a configured "Session" class. A session is used to interact with the database.
SessionLocal = sessionmaker(
    autocommit = False, # Disable autocommit mode. (This means changes are not automatically saved to the database.)
    autoflush = False,  # Disable autoflush mode. (This means changes are not automatically sent to the database.)
    bind = engine # Bind the session to the engine. (This connects the session to our database)
)

# Function to generate a unique identifier (UUID) as a hex string.
def gen_uuid() -> str:
    return uuid.uuid4().hex

# Create a base class for our ORM models. A base is a class that other ORM models will inherit from.
Base = declarative_base() 

# Define the MainEventORM class which represents the "main_events" table in the database.
class MainEventORM(Base):
    __tablename__ = "main_events"

    id = Column(String, primary_key=True, index=True, default=gen_uuid)
    title = Column(String, index=True)
    start_date = Column(String)
    end_date = Column(String)
    start_time = Column(String, nullable=True)
    end_time = Column(String, nullable=True)
    location = Column(String, nullable=True)
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
    like_count = Column(Integer, default=0, nullable=False)
    going_count = Column(Integer, default=0, nullable=False)
    main_event_temp_key = Column(String, nullable=True)  # Temporary key for linking, cleared after processing
    sub_event_ids = Column(JSON, nullable=True)  # Array of sub_event IDs

    # Relationship to sub_events
    sub_events = relationship("SubEventORM", back_populates="main_event", cascade="all, delete-orphan")
    
    # Relationship to users who liked this event
    liked_by_users = relationship("UserLikeORM", back_populates="main_event", foreign_keys="UserLikeORM.main_event_id")

    # Relationship to users who are going to this event
    going_by_users = relationship("UserGoingORM", back_populates="main_event", foreign_keys="UserGoingORM.main_event_id")


# Define the SubEventORM class which represents the "sub_events" table in the database.
class SubEventORM(Base):
    __tablename__ = "sub_events"
    __table_args__ = {"sqlite_autoincrement": True}

    id = Column(String, primary_key=True, index=True, default=gen_uuid)
    title = Column(String, index=True)
    start_date = Column(String)
    end_date = Column(String)
    start_time = Column(String, nullable=True)
    end_time = Column(String, nullable=True)
    location = Column(String, nullable=True)
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
    like_count = Column(Integer, default=0, nullable=False)
    going_count = Column(Integer, default=0, nullable=False)
    main_event_temp_key = Column(String, nullable=True)  # Temporary key for linking, cleared after processing
    main_event_id = Column(String, ForeignKey("main_events.id", ondelete="CASCADE"), nullable=True)

    # Relationship to main_event
    main_event = relationship("MainEventORM", back_populates="sub_events")
    
    # Relationship to users who liked this event
    liked_by_users = relationship("UserLikeORM", back_populates="sub_event", foreign_keys="UserLikeORM.sub_event_id")

    # Relationship to users who are going to this event
    going_by_users = relationship("UserGoingORM", back_populates="sub_event", foreign_keys="UserGoingORM.sub_event_id")


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
    suggested_event_ids = Column(JSON, nullable=True)  # List of suggested main_event IDs

    # Relationship to liked events - cascade delete when user is deleted
    liked_events = relationship("UserLikeORM", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)


# Define the UserLikeORM class which represents the "user_likes" table in the database.
# This table stores which users have liked which events (both main_events and sub_events).
class UserLikeORM(Base):
    __tablename__ = "user_likes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # CASCADE means that if a user or event is deleted, all their likes are also deleted.
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    main_event_id = Column(String, ForeignKey("main_events.id", ondelete="CASCADE"), nullable=True)
    sub_event_id = Column(String, ForeignKey("sub_events.id", ondelete="CASCADE"), nullable=True)

    # Ensure a user can only like an event once (separate constraints for main and sub events)
    __table_args__ = (
        UniqueConstraint("user_id", "main_event_id", name="unique_user_main_event_like"),
        UniqueConstraint("user_id", "sub_event_id", name="unique_user_sub_event_like"),
    )

    # Relationships
    user = relationship("UserORM", back_populates="liked_events")
    main_event = relationship("MainEventORM", back_populates="liked_by_users", foreign_keys=[main_event_id])
    sub_event = relationship("SubEventORM", back_populates="liked_by_users", foreign_keys=[sub_event_id])

# Define the UserGoingORM class which represents the "user_going" table in the database.
# This table stores which users are going to which events (both main_events and sub_events).
class UserGoingORM(Base):
    __tablename__ = "user_going"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    main_event_id = Column(String, ForeignKey("main_events.id", ondelete="CASCADE"), nullable=True)
    sub_event_id = Column(String, ForeignKey("sub_events.id", ondelete="CASCADE"), nullable=True)

    __table_args__ = (
        UniqueConstraint("user_id", "main_event_id", name="unique_user_main_event_going"),
        UniqueConstraint("user_id", "sub_event_id", name="unique_user_sub_event_going"),
    )

    user = relationship("UserORM")
    main_event = relationship("MainEventORM", back_populates="going_by_users", foreign_keys=[main_event_id])
    sub_event = relationship("SubEventORM", back_populates="going_by_users", foreign_keys=[sub_event_id])



# Function to initialize the database and create tables.
def init_db() -> None:
    Base.metadata.create_all(bind=engine) # Create all tables in the database based on the ORM models defined.