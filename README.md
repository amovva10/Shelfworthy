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

## Tools Used
- **FastAPI** – Web framework
- **SQLAlchemy** – ORM for Python
- **PostgreSQL** – Relational DB
- **Pytest** – Testing framework
- **Spacy** – For Named Entity Recognition (NER)

![homepage -sw](https://github.com/user-attachments/assets/5ff74f9c-1b71-48b3-86cd-6144f5443fec)

![sign in - sw](https://github.com/user-attachments/assets/ade2e8ad-bf69-4cc0-ab0a-ac3e0aa5ddbe)

![skeets - sw](https://github.com/user-attachments/assets/9c5b84f8-5b62-4949-a710-e2d210239aef)

![shelf - sw](https://github.com/user-attachments/assets/68667589-d0a2-48f9-ad43-33c8b53727fb)

