"""Routing and implementation for book endpoints."""

# Third-party imports
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Cookie, Depends, HTTPException
from sqlmodel import Session, select

# Local imports
from app.bsky.atproto_utils import login_using_env, search_bsky_posts
from app.dependencies import get_db
from app.models.database import SavedSkeet
from app.models.post import Post, PostModel, PostRead
from app.models.post_classifier import PostClassifier
from app.routes.auth import session_store

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/posts", 
    tags=["Posts"]
)

# Function to fetch all posts classified by genre
def fetch_classified_posts(genre: Optional[str] = None):
    """Fetch and classify posts by genre."""
    client = login_using_env()
    logger.info("Logged in successfully")

    # Fetch posts
    raw_posts, _ = search_bsky_posts(client)
    logger.info(f"Fetched {len(raw_posts)} posts")

    # Classify each post by genre
    classified_posts = {}

    for post in raw_posts:
        classifier = PostClassifier(
            post_text=post["text"],
            handle=post.get("handle", "unknown"),
            display_name=post.get("display_name", "Unknown"),
            like_count=post.get("like_count", 0),
            timestamp=datetime.fromisoformat(post["timestamp"]),
            uri=post.get("uri", "unknown")
        )
        genre_name = classifier.classify_genre()
        logger.info(f"Post classified as {genre_name}")

        classified_posts.setdefault(genre_name, []).append(post)

    # Filter if genre is specified
    if genre:
        if genre not in classified_posts:
            raise HTTPException(status_code=404, detail=f"Genre '{genre}' not found")
        return {"genre": genre, "posts": classified_posts[genre]}

    return [{"genre": g, "posts": p} for g, p in classified_posts.items()]

@router.get("/classified")
async def get_classified_posts_endpoint(genre: Optional[str] = None):
    """API endpoint to fetch classified posts by genre."""
    return fetch_classified_posts(genre)

def get_logged_in_user_id(session_id: str = Cookie(None)) -> int:
    """Retrieves the user ID from the session store using the session ID."""
    if not session_id:
        raise HTTPException(status_code=401,
                            detail="Unauthorized: Session ID is missing")
    
    # Check if the session ID exists in the session store
    user_id = session_store.get(session_id)
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid session")
    
    return int(user_id)

@router.post("/", response_model=Post)
def create_post(post: Post, db: Session = Depends(get_db),
                user_id: int = Depends(get_logged_in_user_id)):
    """Saves a skeet by creating a SavedSkeet entry that links the
    current user with a BlueSky post (creating the post if needed).
    """  # noqa: D205
    # Check if the post already exists by URI
    statement = select(PostModel).where(PostModel.uri == post.uri)
    results = db.exec(statement)
    existing_post = results.first()

    if existing_post:
        db_post = existing_post
    else:
        # Create a new post if it doesn't exist
        db_post = PostModel(
            handle=post.handle,
            display_name=post.display_name,
            text=post.text,
            timestamp=post.timestamp,
            like_count=post.like_count,
            uri=post.uri
        )
        db.add(db_post)
        db.commit()
        db.refresh(db_post)

    # Check if this post is already saved by this user
    saved_statement = select(SavedSkeet).where(
        (SavedSkeet.post_id == db_post.id) &
        (SavedSkeet.user_id == user_id)
    )
    saved_result = db.exec(saved_statement).first()

    if saved_result:
        # Already saved, just return the post
        return db_post

    # Otherwise, save it
    saved_skeet = SavedSkeet(post_id=db_post.id, user_id=user_id)
    db.add(saved_skeet)
    db.commit()

    return db_post

@router.get("/myshelf", response_model=list[Post])
def get_my_saved_posts(db: Session = Depends(get_db),
                       user_id: int = Depends(get_logged_in_user_id)):
    """Retrieves all posts saved by the currently logged-in user."""
    results = db.exec(
        select(PostModel)
        .join(SavedSkeet, SavedSkeet.post_id == PostModel.id)  
        .where(SavedSkeet.user_id == user_id)
    ).all()

    if not results:
        raise HTTPException(status_code=404, detail="No saved posts found")
    return results


@router.get("/{post_id}", response_model=PostRead)
def get_post(post_id: int, db: Session = Depends(get_db),
             user_id: int = Depends(get_logged_in_user_id)):
    """Retrieves a specific post by its ID, saved by the currently logged-in user."""
    # Construct the select query with a join 
    statement = select(PostModel).join(SavedSkeet, SavedSkeet.post_id == PostModel.id) \
        .where(SavedSkeet.user_id == user_id, PostModel.id == post_id)

    # Execute the query and get the first result
    post = db.execute(statement).scalars().first()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")
    
    return post


@router.put("/{post_id}", response_model=Post)
def update_post(post_id: int, db: Session = Depends(get_db)):
    """Placeholder endpoint for updating a post. Currently no fields are editable."""
    post = db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # This is a placeholder and doesn't actually modify the post
    # In the future, may add a modifiable 'notes' field to a post for users to add notes
    return post

@router.delete("/{post_id}")
def unsave_post(post_id: int, db: Session = Depends(get_db),
                user_id: int = Depends(get_logged_in_user_id)):
    """Removes a skeet from the user's saved skeets (shelf).

    Does NOT delete the post from the database.
    """
    # Find the saved skeet entry for this user and post
    statement = select(SavedSkeet).where(
        (SavedSkeet.post_id == post_id) &
        (SavedSkeet.user_id == user_id)
    )
    result = db.exec(statement).first()

    if not result:
        raise HTTPException(status_code=404,
                            detail="Saved skeet not found for this user")

    # Delete the saved skeet entry
    db.delete(result)
    db.commit()

    return {"detail": "Post unsaved successfully"}
