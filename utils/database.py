import sqlite3
from queue import Queue
import os
from threading import Lock
from datetime import datetime

# Check if the database file exists, and create it if it does not
if not os.path.isfile(os.getcwd() + "/Movies.db"):
    try:
        conn = sqlite3.connect(
            os.getcwd() + "/Movies.db", check_same_thread=False)
        cursor = conn.cursor()

        cursor.execute("""CREATE TABLE MovieReviews (
                    ID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                    MovieID TEXT,
                    Name TEXT ,
                    Timestamp TEXT,
                    Content TEXT
                )""")

        conn.commit()
        conn.close()

    except Exception as err:
        input("Failed to create database" + str(err))

# Initialize global variables for connection pooling
LOCK = Lock()
MAX_CONNECTIONS = 1
CONNECTION_POOL = Queue(maxsize=MAX_CONNECTIONS)


def init_pool():
    """
    Initialize the connection pool by creating the maximum number of
    connections allowed and adding them to the connection pool queue.
    """
    print("Starting database pool")
    for i in range(MAX_CONNECTIONS):
        connection = sqlite3.connect(
            os.getcwd() + "/Movies.db", check_same_thread=False)
        CONNECTION_POOL.put(connection)


def save_movie_review(movie_name, review):
    """
    Save a movie review to the database.

    Args:
        movie_name (str): The name of the movie.
        review (str): The review content.

    Returns:
        The result of the database execute() method.
    """
    try:
        LOCK.acquire()
        connection_ = CONNECTION_POOL.get()
        cursor_ = connection_.cursor()

        # Insert a new review into the database
        ret = cursor_.execute("INSERT INTO MovieReviews VALUES (null, ?, ?, ?, ?)",
                              (movie_name, "Anonymous User", datetime.now().strftime("%Y-%m-%d"), review))

        connection_.commit()
        return ret
    except Exception as err:
        print(err)
    finally:
        try:
            cursor_.close()
            CONNECTION_POOL.put(connection_)
        except Exception as err:
            print(err)
        LOCK.release()


def get_movie_reviews(movie_name):
    """
    Get all reviews for a movie from the database.

    Args:
        movie_name (str): The name of the movie.

    Returns:
        A list of tuples containing the Name, Timestamp, and Content for each review.
    """
    try:
        LOCK.acquire()
        connection_ = CONNECTION_POOL.get()
        cursor_ = connection_.cursor()

        # Get all reviews for the specified movie
        ret = cursor_.execute(
            "SELECT Name, Timestamp, Content FROM MovieReviews WHERE MovieID=?", (movie_name,))
        results = ret.fetchall()
        connection_.commit()
        return results
    except Exception as err:
        print(err)
    finally:
        try:
            cursor_.close()
            CONNECTION_POOL.put(connection_)
        except Exception as err:
            print(err)
        LOCK.release()
