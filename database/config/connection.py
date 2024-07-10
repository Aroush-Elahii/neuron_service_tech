from pymongo import MongoClient
from contextlib import contextmanager

# Defining the MongoDB connection string
DATABASE_URL = "mongodb://localhost:27017/"

#  MongoClient object
client = MongoClient(DATABASE_URL)

#  Creating Database NST
db = client.nst

# Access a specific database
collection_users = db["users"]

# Create a context manager to handle the database connection
@contextmanager
def get_db():
    try:
        yield db
    finally:
        client.close()