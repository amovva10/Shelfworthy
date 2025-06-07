"""Class that will extract a book author and book title."""

# Load model directly
from transformers import AutoModelForTokenClassification, AutoTokenizer, pipeline

tokenizer = AutoTokenizer.from_pretrained("dbmdz/bert-large-cased-finetuned-conll03-english")  # noqa: E501
model = AutoModelForTokenClassification.from_pretrained("dbmdz/bert-large-cased-finetuned-conll03-english")  # noqa: E501

# Initialize the NER pipeline with the specified model
ner_pipeline = pipeline("ner", model=model, tokenizer=tokenizer, grouped_entities=True)

class TextModel:
    """A simple class to represent a text model."""
    def __init__(self, text: str):
        """Initialize the text model with the given text."""
        self.text = text

# Example usage with TextModel
text_model = TextModel("J.K. Rowling wrote the Harry Potter series. The first book, "
"Harry Potter and the Philosopher's Stone, was published in 1997.")

# Run the NER pipeline on the text
entities = ner_pipeline(text_model.text)

# Extract authors and book titles
extracted = {"authors": [], "book_titles": []}
for entity in entities:
    if entity["entity_group"] == "PER":
        extracted["authors"].append(entity["word"])
    elif entity["entity_group"] == "WORK_OF_ART":
        extracted["book_titles"].append(entity["word"])

# Print the extracted entities
print("Authors:", extracted["authors"])
print("Book Titles:", extracted["book_titles"])