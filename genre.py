"""Routing and implementation for genre endpoints."""

# Third-party imports
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

# Local imports
from app.dependencies import get_db
from app.models.database import Genre, list_genres

router = APIRouter(
    prefix="/genres",
    tags=["Genres"]
)

@router.post("/", response_model=Genre)
def create_genre(genre: Genre, db: Session = Depends(get_db)):
    """Creates a new genre entry.

    Args:
    - genre (Genre): The genre data to be added.

    Returns:
    - The created genre with an assigned ID.
    """
    db.add(genre)
    db.commit()
    db.refresh(genre)
    return genre

@router.get("/", response_model=list[Genre])
def get_genres(db: Session = Depends(get_db)):
    """Retrieves all genres in the database.

    Returns:
    - A list of genre objects.
    """
    genres = list_genres(db)  
    print("DEBUG: Retrieved genres from the database:", genres)
    return genres

@router.get("/{genre_id}", response_model=Genre)
def get_genre(genre_id: int, db: Session = Depends(get_db)):
    """Retrieves a specific genre by its ID.

    Args:
    - genre_id (int): The ID of the genre.

    Returns:
    - The genre object if found, else raises a 404 error.
    """
    genre = db.get(Genre, genre_id)
    if not genre:
        raise HTTPException(status_code=404, detail="Genre not found")
    return genre

@router.put("/{genre_id}", response_model=Genre)
def update_genre(genre_id: int, updated_genre: Genre, db: Session = Depends(get_db)):
    """Updates an existing genre's details.

    Args:
    - genre_id (int): The ID of the genre to update.
    - updated_genre (Genre): The updated genre data.

    Returns:
    - The updated genre object.
    """
    genre = db.get(Genre, genre_id)
    if not genre:
        raise HTTPException(status_code=404, detail="Genre not found")

    genre.name = updated_genre.name
    genre.description = updated_genre.description

    db.add(genre)
    db.commit()
    db.refresh(genre)
    return genre

@router.delete("/{genre_id}")
def delete_genre(genre_id: int, db: Session = Depends(get_db)):
    """Deletes a genre by ID.

    Args:
    - genre_id (int): The ID of the genre to delete.

    Returns:
    - A success message if deleted.
    """
    genre = db.get(Genre, genre_id)
    if not genre:
        raise HTTPException(status_code=404, detail="Genre not found")
    db.delete(genre)
    db.commit()
    return {"detail": "Genre deleted successfully"}
