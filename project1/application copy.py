import os
import hashlib  # For password hashing
import secrets
from flask import Flask, render_template, request, redirect, session
from flask_session import Session
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, ForeignKey
from sqlalchemy.orm import scoped_session, sessionmaker

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure the database connection
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

# Configure Flask application
app = Flask(__name__)

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set a secret key for the session (replace with your own secret key)
app.secret_key = "secrets.token_hex(16)"

# Function to hash passwords using SHA-256 (you can use a more secure method in production)
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Create necessary database tables if they don't exist
metadata = MetaData()

# Users table (if not already created) 
users = Table('users', metadata,
    Column('id', Integer, primary_key=True),
    Column('username', String),
    Column('password', String),
)

# Books table (if not already created)
books = Table('books', metadata,
    Column('id', Integer, primary_key=True),
    Column('isbn', String),
    Column('title', String),
    Column('author', String),
    Column('year', Integer),
    # Add more columns based on your book details
)

# Reviews table (if not already created)
reviews = Table('reviews', metadata,
    Column('id', Integer, primary_key=True),
    Column('book_isbn', String, ForeignKey('books.isbn')),
    Column('username', String),
    Column('rating', Integer),
    Column('comment', String),
)

#Create tables 
metadata.create_all(engine)

# Registration route
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Validate input (check for existing username, password requirements, etc.)
        if not username or not password:
            return render_template("register.html", error="Username and password are required.")

        # Check if the username is already taken
        if db.execute("SELECT id FROM users WHERE username = :username", {"username": username}).fetchone():
            return render_template("register.html", error="Username already taken. Choose another one.")

        # Hash the password before storing it in the database
        hashed_password = hash_password(password)

        # Insert the user into the database
        result = db.execute("INSERT INTO users (username, password) VALUES (:username, :password)",
                            {"username": username, "password": hashed_password})
        db.commit()

        # Log the user in after registration
        user_id = result.lastrowid
        session["user_id"] = user_id

        return redirect("/")  # Redirect to the home page after registration

    return render_template("register.html")

# Login route
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Validate input
        if not username or not password:
            return render_template("login.html", error="Username and password are required.")

        # Query the database for the user
        user = db.execute("SELECT * FROM users WHERE username = :username", {"username": username}).fetchone()

        # Check if the user exists and the password is correct
        if user and hash_password(password) == user["password"]:
            # Log the user in
            session["user_id"] = user["id"]
            return redirect("/")  # Redirect to the home page after login

        return render_template("login.html", error="Invalid username or password.")

    return render_template("login.html")

# Logout route
@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect("/")

# Search route
@app.route("/search", methods=["GET", "POST"])
def search():
    if request.method == "POST":
        search_query = request.form.get("search_query")

        # Validate input
        if not search_query:
            return render_template("search.html", error="Please enter a search query.")

        # Query the database for matching books
        books = db.execute("""
            SELECT * FROM books
            WHERE isbn ILIKE :search_query
            OR title ILIKE :search_query
            OR author ILIKE :search_query
            """,
            {"search_query": f"%{search_query}%"}
        ).fetchall()

        if not books:
            return render_template("search.html", error="No matching books found.")

        return render_template("search.html", books=books)

    return render_template("search.html")

# Book page route
@app.route("/book/<isbn>", methods=["GET"])
def book(isbn):
    # Query the database for the book details
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()

    # Query the database for reviews related to the book
    reviews = db.execute("SELECT * FROM reviews WHERE book_isbn = :isbn", {"isbn": isbn}).fetchall()

    if not book:
        return render_template("error.html", error="Book not found.")

    return render_template("book.html", book=book, reviews=reviews)


# Run the application
if __name__ == "__main__":
    app.run(debug=True)

@app.route("/")
def index():
    return "Project 1: TODO"
