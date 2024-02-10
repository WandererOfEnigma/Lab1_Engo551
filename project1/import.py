import os
import csv
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, text, UniqueConstraint
from sqlalchemy.orm import scoped_session, sessionmaker

# Check for the DATABASE_URL environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure the database connection using the environment variable
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

# Test the database connection
try:
    db.execute(text("SELECT 1"))  # Wrap SQL expression with text()
    print("Connection successful!")
except Exception as e:
    print("Connection failed:", e)
finally:
    db.close()

# Create necessary database tables if they don't exist
metadata = MetaData()

# Books table (if not already created)
books = Table('books', metadata,
    Column('isbn', String, primary_key=True),  # Define isbn as the primary key
    Column('title', String),
    Column('author', String),
    Column('year', Integer),
    # Add more columns based on your book details
)

# Create tables
metadata.create_all(engine)

# Open the CSV file and insert data into the books table
with open('books.csv', 'r', encoding='utf-8') as file:
    reader = csv.reader(file)
    next(reader)  # Skip the header row

    for row in reader:
        isbn, title, author, year = row
        db.execute(text("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)"),
                   {"isbn": isbn, "title": title, "author": author, "year": int(year)})

# Commit the changes to the database
db.commit()
