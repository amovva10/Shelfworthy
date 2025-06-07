"""Routing and implementation for user endpoints."""

# Third-party imports
from fastapi import APIRouter, Depends, HTTPException
from passlib.context import CryptContext
from sqlmodel import Session, select

# Local imports
from app.dependencies import get_db
from app.models.database import User
from app.models.user import UserCreate, UserRead

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hashes a password using bcrypt."""
    return pwd_context.hash(password)

@router.post("/", response_model=UserRead)
def create_user(user_in: UserCreate, db: Session = Depends(get_db)):
    """Creates a new user entry.

    Args:
    - user (User): The user data to be added.

    Returns:
    - The created user with an assigned ID.
    """
    # Check if user already exists
    existing_user = db.exec(select(User).where(User.email == user_in.email)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        username=user_in.username,
        email=user_in.email,
        secret=hash_password(user_in.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.get("/", response_model=list[UserRead])
def get_users(db: Session = Depends(get_db)):
    """Retrieves all users in the database.

    Returns:
    - A list of user objects.
    """
    users = db.exec(select(User)).all()
    return users

@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """Retrieves a specific user by their ID.

    Args:
    - user_id (int): The ID of the user.

    Returns:
    - The user object if found, else raises a 404 error.
    """
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/{user_id}", response_model=UserRead)
def update_user(user_id: int, updated_user: User, db: Session = Depends(get_db)):
    """Updates an existing user's details.

    Args:
    - user_id (int): The ID of the user to update.
    - updated_user (User): The updated user data.

    Returns:
    - The updated user object.
    """
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.username = updated_user.username
    user.email = updated_user.email
    user.secret = hash_password(updated_user.secret)

    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """Deletes a user by ID.

    Args:
    - user_id (int): The ID of the user to delete.

    Returns:
    - A success message if deleted.
    """
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"detail": "User deleted successfully"}
