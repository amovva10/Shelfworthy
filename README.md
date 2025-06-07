# ShelfWorthy – Backend Features

This is a personal showcase of my backend contributions to **ShelfWorthy**, a book recommendation system that pulls books from Bluesky posts and uses NLP to classify them by genre.

This repo contains the backend modules I built and worked on:

- `database.py` – SQLAlchemy DB setup and session manager
- `ner.py` – Named Entity Recognition for identifying book titles in posts
- `post_classifier.py` – Custom classifier to assign genre labels using keywords/NLP
- `book.py`, `genre.py`, `post.py`, `user.py` – FastAPI route logic for handling core app entities
- `test_database.py` – Unit test file for DB operations and model validations

## Key Features I Implemented

- Extracted book titles from Bluesky posts using custom NER logic
- Classified books into genres via `PostClassifier`
- Ensured all `SavedSkeet` entries are linked to a valid `Book` and `Genre`
- Cleaned database schema by removing unused models and fixing constraint violations
- Wrote unit tests to verify DB integrity and genre classification accuracy

## Tech Stack
- **FastAPI** – Web framework
- **SQLAlchemy** – ORM for Python
- **PostgreSQL** – Relational DB
- **Pytest** – Testing framework
- **Spacy** – For Named Entity Recognition (NER)

