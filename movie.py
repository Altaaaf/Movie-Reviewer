from bs4 import BeautifulSoup
import requests
import json
import re


def get_movie_id(movie_name):
    """
    Given a movie name, returns the corresponding IMDb ID of the first search result
    from the IMDb search page.

    Args:
        movie_name (str): The name of the movie to search for.

    Returns:
        str: The IMDb ID of the first search result, or None if no search result was found.
    """
    # Make a request to the IMDb search page with the given movie name
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/111.0"
        }
        params = {
            "q": movie_name,
            "s": "tt",
            "ttype": "ft",
            "ref_": "fn_ft",
        }
        response = requests.get(
            "https://www.imdb.com/find", headers=headers, params=params, timeout=5)

        # Parse the HTML content of the response with BeautifulSoup
        soup = BeautifulSoup(response.content, "html.parser")

        # Find the first div tag with a class name that starts with "findSection"
        div_tags = soup.find_all(
            "div", class_=lambda x: x and x.startswith("sc-17bafbdb-2"))
        if div_tags:
            # If we found a matching div tag, find the first href link inside its UL tag
            ul_tag = div_tags[0].find("ul")
            if ul_tag:
                first_link = ul_tag.find("a")["href"]
                # Extract the ID from the URL and return it
                tt_id = re.search(r"/title/(tt\d+)/", first_link).group(1)
                return tt_id

    except Exception as err:
        print(err)
    # If there was an error or we didn't find a matching div tag or UL tag, return None
    return None


def get_imdb_movie_details(movie_id: str) -> tuple:
    """Retrieve details of a movie from IMDb using its ID.

    Args:
        movie_id (str): The IMDb ID of the movie.

    Returns:
        tuple: A tuple containing various details of the movie, including its name,
            image, trailer URL, description, rating value, total rating count,
            content rating, duration, genre, actors, and directors.

            If the movie details cannot be retrieved, None is returned for all values.
    """
    try:
        movie_url = f'https://www.imdb.com/title/{movie_id}'
        response = requests.get(
            movie_url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/111.0"
            },
            timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract movie details from the JSON-LD script tag
        rating_script = soup.find('script', {'type': 'application/ld+json'})
        if rating_script:
            movie_data = rating_script.string.strip()
            movie_dict = json.loads(movie_data)

            name = movie_dict['name']
            image = movie_dict['image']
            description = movie_dict['description']
            trailer = movie_dict['trailer']['embedUrl']
            rating_value = movie_dict['aggregateRating']['ratingValue']
            total_rating = movie_dict['aggregateRating']['ratingCount']
            content_rating = movie_dict['contentRating']  # PG13, R, etc
            genre = movie_dict['genre']
            date_published = movie_dict['datePublished']
            actors = [(person['name'], 'https://www.imdb.com' + person['url'])
                      for person in movie_dict['actor']]
            directors = [(person['name'], 'https://www.imdb.com' + person['url'])
                         for person in movie_dict['director']]

            # Extract movie duration from the duration string
            time_str = movie_dict['duration']
            duration = f"{int(time_str[2:time_str.find('H')])}H:{int(time_str[time_str.find('H')+1:time_str.find('M')])}M"

            return name, image, trailer, description, rating_value, total_rating, date_published, content_rating, duration, genre, actors, directors

    except Exception as err:
        print(err)

    # If there was an error or the script tag was not found, return None for all values
    return None, None, None, None, None, None, None, None, None, None, None, None
