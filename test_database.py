"""This module contains tests for the database schema and functionality."""

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from app.models.database import Book, Genre, User, list_genres

TEST_DATABASE_URL = "sqlite:///./test.sqlite"
test_engine = create_engine(TEST_DATABASE_URL,
                            connect_args={"check_same_thread": False})

SQLModel.metadata.create_all(test_engine)

@pytest.fixture(scope="session")
def db_session():
    """Test database session."""
    with Session(test_engine) as session:
        yield session  


def test_add_genre(db_session: Session):
    """Test adding a genre to ensure genres exist."""
    thriller = db_session.exec(select(Genre).where(Genre.name == "Thriller")).first()
    if not thriller:
        thriller = Genre(name="Thriller", description="Thriller book")
        db_session.add(thriller)
        db_session.commit()

    result = db_session.exec(select(Genre).where(Genre.name == "Thriller")).first()
    assert result is not None
    assert result.description == "Thriller book"

def test_list_genres(db_session: Session):
    """Test that list_genres() returns genres."""
    genres = list_genres(db_session)
    assert isinstance(genres, list)  
    assert len(genres) > 0  
    assert any(g.name == "Thriller" for g in genres)  


def test_book_table(db_session: Session):
    """Test Book table stores a book."""
    genre = db_session.exec(select(Genre).where(Genre.name == "Thriller")).first()  
    existing_book = db_session.exec(select(Book).where(Book.title == "Test Book")).first()  # noqa: E501
    
    if not existing_book:
        book = Book(title="Test Book", author="Test Author", genre_id=genre.id)
        db_session.add(book)
        db_session.commit()

    result = db_session.exec(select(Book).where(Book.title == "Test Book")).first()
    assert result is not None

def test_user_table(db_session: Session):
    """Test User table stores data."""
    user = User(
        username="simpletestuser",
        email="simple@example.com",
        secret="fakehashedpassword"
    )
    db_session.add(user)
    db_session.commit()

    result = db_session.exec(select(User).where(User.username == "simpletestuser")).first()  # noqa: E501
    assert result is not None
    assert result.email == "simple@example.com"

