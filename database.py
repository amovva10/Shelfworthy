"""This module defines SQLModel database schema for the book recommendation system."""

# Third-party imports
from datetime import UTC, datetime

from sqlmodel import Field, Relationship, Session, SQLModel, UniqueConstraint, select

# Local imports
from app.dependencies import engine


class User(SQLModel, table=True):
    """Stores user information."""
    id: int = Field(default=None, primary_key=True)
    username: str
    email: str
    secret: str 
    
    saved_skeets: list["SavedSkeet"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

class Genre(SQLModel, table=True):
    """Represents a book genre in the database."""
    id: int = Field(default=None, primary_key=True)
    name: str
    description: str | None = None

    classified_posts: list["ClassifiedPost"] = Relationship(back_populates="genre")


class Book(SQLModel, table=True):
    """Represents a book with attributes including title, author, and genre."""
    id: int = Field(default=None, primary_key=True)
    title: str
    author: str
    genre_id: int = Field(foreign_key="genre.id")

    saved_skeets: list["SavedSkeet"] = Relationship(back_populates="book")

class Post(SQLModel, table=True):
    """Represents a social media post."""
    id: int = Field(default=None, primary_key=True)
    handle: str
    display_name: str
    text: str
    timestamp: datetime
    like_count: int = Field(default=0)
    uri: str
    
    classified_posts: list["ClassifiedPost"] = Relationship(back_populates="post")
    saved_skeets: list["SavedSkeet"] = Relationship(back_populates="post")

class ClassifiedPost(SQLModel, table=True):
    """Stores information about the genre classification of posts."""
    post_id: int = Field(foreign_key="post.id", primary_key=True)  
    genre_id: int = Field(foreign_key="genre.id", primary_key=True)  
    
    genre: "Genre" = Relationship(back_populates="classified_posts")
    post: "Post" = Relationship(back_populates="classified_posts")

class SavedSkeet(SQLModel, table=True):
    """Represents a saved skeet by a user."""
    __table_args__ = (
        UniqueConstraint("user_id", "post_id", name="unique_saved_skeet"),
    )
    """Stores saved skeets by the user."""
    id: int = Field(default=None, primary_key=True)
    post_id: int = Field(foreign_key="post.id", nullable=True)
    user_id: int = Field(foreign_key="user.id", default=1)
    book_id: int | None = Field(default=None, foreign_key="book.id", nullable=True)
    saved_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    post: "Post" = Relationship(back_populates="saved_skeets")
    user: "User" = Relationship(back_populates="saved_skeets")
    book: "Book" = Relationship(back_populates="saved_skeets")

def list_genres(db: Session) -> list[Genre]:
    """Fetches and returns all genres from the database."""
    return db.exec(select(Genre)).all()

def create_db_and_tables():
    """Creates the database and tables based on defined models."""
    SQLModel.metadata.create_all(engine)
