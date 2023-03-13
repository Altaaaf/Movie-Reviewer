from flask import Flask, render_template, request, redirect, url_for, session
from utils.movie import get_imdb_movie_details, get_movie_id
import re
import secrets
from flask_sslify import SSLify
from flask_talisman import Talisman
from utils.database import init_pool, get_movie_reviews, save_movie_review
app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(32)
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['JSON_AS_ASCII'] = False
sslify = SSLify(app)
app.config['SSLIFY_ENABLE'] = True
talisman = Talisman(app, content_security_policy={
    'default-src': '\'self\'',
    'script-src': [
        '\'self\'',
        'https://stackpath.bootstrapcdn.com',
        '\'unsafe-inline\'',  # Allow inline scripts
    ],
    'style-src': [
        '\'self\'',
        '\'unsafe-inline\'',
        'https://stackpath.bootstrapcdn.com',
    ],
    'img-src': [
        '\'self\'',
        'https://m.media-amazon.com'
    ],
    'font-src': [
        '\'self\'',
        'https://stackpath.bootstrapcdn.com',
    ],
    'object-src': '\'none\'',
    'frame-ancestors': '\'none\'',
    'base-uri': '\'self\'',
    'form-action': '\'self\'',
    'frame-src': '\'self\'',
})
talisman.frame_options = 'DENY'
talisman.force_https = True
talisman.strict_transport_security = True
talisman.session_cookie_secure = True
talisman.session_cookie_httpOnly = True
talisman.referrer_policy = 'strict-origin-when-cross-origin'
talisman.content_security_policy.update({
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'SAMEORIGIN',
    'X-XSS-Protection': '1; mode=block',
})


@app.before_first_request
def init_database():
    init_pool()


@ app.route('/', methods=["GET"])
def index():
    return render_template('index.html')


@app.route('/search', methods=['POST'])
def search():
    """
    A view function that handles the movie search request.

    It gets the movie name from the form data, validates it, and stores it in the session.
    Then it redirects to the movie search page for the given movie name.

    :return: A redirect response to the movie search page.
    """
    try:
        # Get the movie name from the form data
        movie_name = request.form['movie_name']

        # If the movie name is empty, render the error page
        if not movie_name:
            return render_template('error.html', error_msg="Movie name is missing")

        # If the movie name is not in the correct format, try to get its ID from IMDb search
        if not re.match(r'^tt\d{6,11}$', movie_name):
            movie_id = get_movie_id(movie_name)

            # If the movie ID is not found, render the error page
            if movie_id is None:
                return render_template('error.html', error_msg="Unable to find IMDb id, using movie name")

            # If the movie ID is found, use it as the new movie name
            movie_name = movie_id

        # Store the movie name in the session
        searches = session.get('searches', [])
        if movie_name not in searches:
            searches.append(movie_name)
        session['searches'] = searches

        # Redirect to the movie search page for the given movie name
        return redirect(url_for('movie_search', movie_name=movie_name))
    except Exception as err:
        print(err)

        # If an error occurs, render the error page
        return render_template('error.html', error_msg="Unexpected error occured")


@app.route('/movie/<movie_name>')
def movie_search(movie_name):
    """
    Renders the results page for the specified movie name.

    Args:
        movie_name (str): The ID or name of the movie to search for.

    Returns:
        The rendered results template for the specified movie name.
    """
    try:
        # Get movie details from IMDb
        name, image, trailer, description, rating_value, total_rating, date_published, content_rating, duration, genre, actors, directors = get_imdb_movie_details(
            movie_name)

        # Check if movie details were found
        if name is None:
            return render_template('error.html', error_msg="Unable to find movie details for this movie")

        # Get movie reviews
        reviews = get_movie_reviews(movie_name)

        # Render the results template with movie details and reviews
        return render_template('results.html',
                               name=name,
                               image=image,
                               trailer=trailer,
                               description=description,
                               rating_value=rating_value,
                               total_rating=total_rating,
                               date_published=date_published,
                               content_rating=content_rating,
                               duration=duration,
                               genre=genre,
                               actors=actors,
                               directors=directors,
                               movie_name=movie_name,
                               reviews=reviews)
    except Exception as err:
        print(err)
        return render_template('error.html', error_msg="Unexpected error occured")


@app.route('/save_review/<movie_name>', methods=['POST'])
def save_review(movie_name):
    """
    This function saves a review for a movie in the database.

    Args:
        movie_name (str): The name of the movie to save the review for.

    Returns:
        render_template: A template for success.html if the review was successfully saved. Otherwise, a template for
        error.html is returned.
    """
    try:
        review = request.form['review']

        # Save the review for the movie in the database
        save_movie_review(movie_name, review)

        # Return a template for success.html with a link to the previous movie page
        return render_template('success.html', previous_movie=f"/movie/{movie_name}")
    except Exception as err:
        print(err)
        # Return a template for error.html if an error occurred
        return render_template('error.html', error_msg="Unexpected error occured")


@app.route('/clear_searches', methods=['POST'])
def clear_searches():
    """
    Clear the previous search history stored in the session.

    Returns:
        Flask redirect object to the index page.
    """
    try:
        # remove the 'searches' key from the session
        session.pop('searches', None)
        # redirect to the index page
        return redirect(url_for('index'))
    except Exception as err:
        # log any errors and return the error page
        print(err)
        return render_template('error.html', error_msg="Unexpected error occured")


if __name__ == '__main__':
    app.run(debug=True)
