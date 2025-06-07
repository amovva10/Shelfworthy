"""Class that will classify a post text into a book genre."""
import os
from datetime import datetime

from huggingface_hub import InferenceClient
from sqlmodel import Session, select

from app.bsky.atproto_utils import login_using_env, search_bsky_posts

# Local imports
from app.dependencies import engine
from app.huggingface.utils import get_zero_shot_client
from app.models.database import (
    Book,
    ClassifiedPost,
    Genre,
    Post,
    SavedSkeet,
    create_db_and_tables,
)


class PostClassifier:
    """Classify the text."""

    def __init__(self, post_text: str, handle: str, display_name: str,
                 like_count: int, timestamp: datetime, uri: str):
        """Take text from Bluesky."""
        self.post_text = post_text
        self.handle = handle
        self.display_name = display_name
        self.like_count = like_count
        self.timestamp = timestamp
        self.uri = uri
        self.qa_client = InferenceClient(
            provider="hf-inference",
            api_key=os.getenv("HUGGINGFACE_INFERENCE_TOKEN"),
        )

    def classify_genre(self) -> str:
        """Classifies the post text into a book genre."""
        candidate_labels = [
            "science fiction",
            "fantasy",
            "self-help",
            "romance",
            "thriller",
        ]

        hf_client = get_zero_shot_client()
        result = hf_client.zero_shot_classification(
            self.post_text, candidate_labels=candidate_labels, multi_label=True
        )
        choice = result[0]
        return choice["label"]
    

    def extract_author(self) -> str:
        """Extracts the author name from the post text."""
        result = self.qa_client.question_answering(
            model="deepset/roberta-base-squad2",
            question="Who is the author?",
            context=self.post_text,
        )
        return result.get("answer", "") if result else ""

    def extract_book_title(self) -> str:
        """Extracts the book title from the post text."""
        result = self.qa_client.question_answering(
            model="deepset/roberta-base-squad2",
            question="What is the book title?",
            context=self.post_text,
        )
        return result.get("answer", "") if result else ""

    def extract_entities(self) -> dict:
        """Extracts author names and book titles from the post text."""
        author = self.extract_author()
        book_title = self.extract_book_title()

        # Validate and clean book title
        if not book_title or book_title.lower() in ["booksky", "unknown", "none"]:
            book_title = None
        else:
        # Remove author's name from the book title if present
            if author and author.lower() in book_title.lower():
                book_title = book_title.lower().replace(author.lower(), "").strip()
        # Keep only the main title
            book_title = book_title.split("/")[0].strip()
        # Capitalize the book title
            book_title = book_title.title()

        # Validate and clean author
        if not author or author.lower() in ["unknown", "none", "author", "anonymous"]:
            author = None
        else:
        # format author name 
            author = " ".join(author.split()).title()
        return {"authors": [author], "book_titles": [book_title]}
    
    # Save genre to database
    def save_genre_to_db(self, genre_name: str):
        """Saves the predicted genre to the database."""
        create_db_and_tables()
        with Session(engine) as session:
            post = session.exec(select(Post).where(Post.text == self.post_text)).first()
            if not post:
                post = Post(
                    handle=self.handle,
                    display_name=self.display_name,
                    text=self.post_text,
                    timestamp=self.timestamp,
                    like_count=self.like_count,
                    uri=self.uri
                )
                session.add(post)
                session.commit()
                session.refresh(post)

            genre = session.exec(select(Genre).where(Genre.name == genre_name)).first()
            if not genre:
                genre = Genre(name=genre_name)
                session.add(genre)
                session.commit()
                session.refresh(genre)

            existing_entry = session.exec(
                select(ClassifiedPost).where(
                    ClassifiedPost.post_id == post.id,
                    ClassifiedPost.genre_id == genre.id
                )
            ).first()

            if not existing_entry:
                classified_post = ClassifiedPost(post_id=post.id, genre_id=genre.id)
                session.add(classified_post)
                session.commit()

    def save_book_to_db(self, book_title: str, author: str, genre_name: str) -> Book:
        """Saves the book title and author to the database."""
        create_db_and_tables()
        with Session(engine) as session:
            genre = session.exec(select(Genre).where(Genre.name == genre_name)).first()
            if not genre:
                genre = Genre(name=genre_name)
                session.add(genre)
                session.commit()
                session.refresh(genre)

            if not book_title:
                raise ValueError("Book title cannot be empty!")

            existing_book = session.exec(
                select(Book).where(Book.title == book_title, Book.author == author)
            ).first()

            if not existing_book:
                book = Book(title=book_title, author=author, genre_id=genre.id)
                session.add(book)
                session.commit()
                session.refresh(book)
                return book
            return existing_book

    def save_skeet_to_db(self, book: Book | None = None):
        """Saves the skeet (post) and links to user and book if available."""
        create_db_and_tables()
        with Session(engine) as session:
            post = session.exec(select(Post).where(Post.text == self.post_text)).first()
            if not post:
                post = Post(
                    handle=self.handle,
                    display_name=self.display_name,
                    text=self.post_text,
                    timestamp=self.timestamp,
                    like_count=self.like_count,
                    uri=self.uri
                )
                session.add(post)
                session.commit()
                session.refresh(post)

            saved_skeet = session.exec(
                select(SavedSkeet).where(
                    SavedSkeet.post_id == post.id,
                    SavedSkeet.user_id == 1
                )
            ).first()

            if saved_skeet:
                if book and saved_skeet.book_id is None:
                    saved_skeet.book_id = book.id
                    session.add(saved_skeet)
                    session.commit()
            else:
                new_saved_skeet = SavedSkeet(
                    post_id=post.id,
                    user_id=1,
                    book_id=book.id if book else None
                )
                session.add(new_saved_skeet)
                session.commit()

    @staticmethod
    def classify_and_save_posts():
        """Fetches posts, classifies their genres, saves the genres to the database."""
        client = login_using_env()
        raw_posts, formatted_posts = search_bsky_posts(client)

        for post in raw_posts:
            classifier = PostClassifier(
                post_text=post["text"],
                handle=post.get("handle", "unknown"),
                display_name=post.get("display_name", "Unknown"),
                like_count=post.get("like_count", 0),
                timestamp=datetime.fromisoformat(post["timestamp"]),
                uri=post.get("uri", "unknown")
            )
            genre = classifier.classify_genre()
            classifier.save_genre_to_db(genre)
            post['predicted_genre'] = genre

        # Extract entities
            entities = classifier.extract_entities()
            post['authors'] = entities['authors']
            post['book_titles'] = entities['book_titles']

            for author, book_title in zip(post['authors'], post['book_titles']):
                if not book_title:
                    print(f"Saving skeet without book: {post['text']}")
                    classifier.save_skeet_to_db()
                else:
                    book = classifier.save_book_to_db(book_title, author, genre)
                    classifier.save_skeet_to_db(book)

        return raw_posts, formatted_posts
