import os
import hashlib
from flask import Flask, render_template, request, redirect, session
from flask_session import Session
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, ForeignKey, text
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
    Column('isbn', String, primary_key=True),  # Define isbn as the primary key
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

# Create tables 
metadata.create_all(engine)

from sqlalchemy import text  # Import the text function from SQLAlchemy

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
        if db.execute(text("SELECT id FROM users WHERE username = :username"), {"username": username}).fetchone():
            return render_template("register.html", error="Username already taken. Choose another one.")

        # Hash the password before storing it in the database
        hashed_password = hash_password(password)

        # Insert the user into the database
        result = db.execute(text("INSERT INTO users (username, password) VALUES (:username, :password)"),
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
        query = text("SELECT * FROM users WHERE username = :username")
        user = db.execute(query, {"username": username}).fetchone()

        # Check if the user exists and the password is correct
        if user and hash_password(password) == user[2]:  # Accessing password using index 2
            # Log the user in
            session["user_id"] = user[0]  # Accessing user_id using index 0
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
        query = text("""
            SELECT * FROM books
            WHERE isbn ILIKE :search_query
            OR title ILIKE :search_query
            OR author ILIKE :search_query
        """)
        books = db.execute(query, {"search_query": f"%{search_query}%"}).fetchall()

        if not books:
            return render_template("search.html", error="No matching books found.")

        return render_template("search.html", books=books)

    return render_template("search.html")

# Book page route
@app.route("/book", methods=["GET"])
def book():
    # Check if an ISBN is provided in the query parameters
    isbn = request.args.get("isbn")

    if isbn:
        # Query the database for the book details
        query_book = text("""
            SELECT * FROM books WHERE isbn = :isbn
        """)
        book = db.execute(query_book, {"isbn": isbn}).fetchone()

        # Query the database for reviews related to the book
        query_reviews = text("""
            SELECT * FROM reviews WHERE book_isbn = :isbn
        """)
        reviews = db.execute(query_reviews, {"isbn": isbn}).fetchall()

        if not book:
            return render_template("error.html", error="Book not found.")

        return render_template("book.html", book=book, reviews=reviews)
    else:
        # If no ISBN is provided, render the book page without book details
        return render_template("book.html")

# Import the text function from SQLAlchemy
from sqlalchemy import text

# Route for submitting reviews
@app.route("/submit_review", methods=["POST"])
def submit_review():
    # Check if the user is logged in
    if "user_id" not in session:
        return redirect("/login")  # Redirect to login page if user is not logged in

    # Get review data from the form
    book_isbn = request.form.get("isbn")
    rating = int(request.form.get("rating"))
    comment = request.form.get("comment")
    user_id = session["user_id"]

    # Validate review data
    if not book_isbn or not rating:
        return render_template("error.html", error="Incomplete review data.")

    # Insert the review into the database using text()
    db.execute(text("INSERT INTO reviews (book_isbn, username, rating, comment) VALUES (:book_isbn, :username, :rating, :comment)"),
               {"book_isbn": book_isbn, "username": user_id, "rating": rating, "comment": comment})
    db.commit()

    # Redirect back to the book page after submitting the review
    return redirect("/book?isbn=" + book_isbn)



@app.route("/")
def index():
    welcome_message = "Project 1: Welcome to my Flask application!<br><br>"

    if "user_id" in session:
        # Links for logged-in users
        links = [
            "<a href='/logout'>Logout</a><br>",
            "<a href='/search'>Search Books</a><br>",
        ]
    else:
        # Links for non-logged-in users
        links = [
            "<a href='/register'>Register</a><br>",
            "<a href='/login'>Login</a><br>",
        ]

    # Combine the welcome message, links, and an extra line break for better formatting
    content = welcome_message + "".join(links)

    return content

# Run the application
if __name__ == "__main__":
    app.run(debug=True)
