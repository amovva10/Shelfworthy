"""Routing and implementation for book endpoints."""

# Third-party imports
from datetime import datetime
from typing import List  # noqa: UP035

from fastapi import APIRouter, Cookie, Depends, HTTPException
from sqlmodel import Session, select

# Local imports
from app.bsky.atproto_utils import login_using_env, search_bsky_posts
from app.dependencies import get_db
from app.models.book import BookCreate, BookModel, BookRead
from app.models.database import Book, SavedSkeet
from app.models.post_classifier import PostClassifier
from app.routes.auth import session_store

router = APIRouter(
    prefix="/books", 
    tags=["Books"]
)

def get_logged_in_user_id(session_id: str = Cookie(None)) -> int:
    """Retrieves the user ID associated with the session ID stored in a cookie."""
    if not session_id:
        raise HTTPException(status_code=401,
                            detail="Unauthorized: Session ID is missing")
    
    # Check if the session ID exists in the session store
    user_id = session_store.get(session_id)
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid session")
    
    return int(user_id)

@router.post("/", response_model=BookRead)  # or create a BookRead if you want to control output  # noqa: E501
def create_book(book: BookCreate, db: Session = Depends(get_db),
                user_id: int = Depends(get_logged_in_user_id)):
    """Creates a new book entry, linking it to the logged-in user through SavedSkeet."""
    # Check if the book already exists based on title and author only
    statement = select(BookModel).where(BookModel.title == book.title,
                                        BookModel.author == book.author)
    existing_book = db.exec(statement).first()

    if existing_book:
        # If the book already exists, associate it with the user
        saved_check = select(SavedSkeet).where(
            SavedSkeet.book_id == existing_book.id,
            SavedSkeet.user_id == user_id
        )
        if db.exec(saved_check).first():
            return existing_book  # Already saved

        db_saved_skeet = SavedSkeet(user_id=user_id,
                                    book_id=existing_book.id, post_id=0)
        db.add(db_saved_skeet)
        db.commit()
        db.refresh(db_saved_skeet)
        return existing_book

    # If the book doesn't exist already, create a new Book entry with default values
    db_book = BookModel(
        title=book.title,
        author=book.author,
        genre_id=1,
    )

    db.add(db_book)
    db.commit()
    db.refresh(db_book)

    db_saved_skeet = SavedSkeet(user_id=user_id, book_id=db_book.id, post_id=0)
    db.add(db_saved_skeet)
    db.commit()
    db.refresh(db_saved_skeet)

    return db_book

@router.get("/myshelf", response_model=list[BookRead])
def get_my_saved_books(db: Session = Depends(get_db),
                       user_id: int = Depends(get_logged_in_user_id)):
    """Retrieves all books saved by the currently logged-in user."""
    results = db.exec(
            select(BookModel)
            .join(SavedSkeet, SavedSkeet.book_id == BookModel.id)
            .where(SavedSkeet.user_id == user_id)
            .distinct()
        ).all()

    if not results:
        raise HTTPException(status_code=404, detail="No saved books found")

    return results

@router.get("/{book_id}", response_model=Book)
def get_book(book_id: int, db: Session = Depends(get_db)):
    """Retrieves a specific book by its ID.

    Args:
    - book_id (int): The ID of the book.

    Returns:
    - The book object if found, else raises a 404 error.
    """
    book = db.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book

@router.put("/{book_id}", response_model=Book)
def update_book(book_id: int, updated_book: Book, db: Session = Depends(get_db)):
    """Updates an existing book's details.

    Args:
    - book_id (int): The ID of the book to update.
    - updated_book (Book): The updated book data.

    Returns:
    - The updated book object.
    """
    book = db.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    book.title = updated_book.title
    book.author = updated_book.author
    book.genre_id = updated_book.genre_id

    db.add(book)
    db.commit()
    db.refresh(book)
    return book

@router.delete("/{book_id}")
def delete_book(book_id: int, db: Session = Depends(get_db)):
    """Deletes a book."""
    """
    Args:
    - book_id (int): The ID of the book.

    Returns:
    - The book object if found, else raises a 404 error.
    """
    book = db.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    db.delete(book)
    db.commit()  
    return {"detail": "Book deleted successfully"}

# Function to retrieve books based on a genre by analyzing posts from Bluesky
def fetch_books_by_genre(genre: str) -> List[Book]:  # noqa: UP006
    """Retrieves books based by genre.

    Args:
        genre (str): The name of the genre.

    Returns:
        A list of Book objects extracted from classified posts.
    """
    client = login_using_env()
    raw_posts, _ = search_bsky_posts(client)

    books: List[Book] = []  # noqa: UP006

    for post in raw_posts:
        classifier = PostClassifier(
            post_text=post["text"],
            handle=post.get("handle", "unknown"),
            display_name=post.get("display_name", "Unknown"),
            like_count=post.get("like_count", 0),
            timestamp=datetime.fromisoformat(post["timestamp"]),
            uri=post.get("uri", "unknown")
        )
        predicted_genre = classifier.classify_genre()

        if predicted_genre.lower() == genre.lower():
            entities = classifier.extract_entities()
            title = entities.get("book_titles", [""])[0]
            author = entities.get("authors", [""])[0]

            if title:  # Only add if a title was found
                books.append(Book(title=title, author=author or None))

    if not books:
        raise HTTPException(status_code=404,
                            detail=f"No books found for genre '{genre}'")

    return books

@router.get("/genres/{genre}", response_model=List[Book])  # noqa: UP006
def get_books_by_genre_from_posts(genre: str):
    """Retrieves books based on a genre by analyzing posts from Bluesky."""
    return fetch_books_by_genre(genre)
    