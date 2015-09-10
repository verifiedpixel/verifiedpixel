import json
from requests import request
# from io import StringIO
from bs4 import BeautifulSoup


# from .exceptions import APIGracefulException


# @TODO: for debug purpose
from pprint import pprint  # noqa


# retrieves the reverse search html for processing. This actually does the
# reverse image lookup
def retrieve(image_url):
    # returned_code = StringIO()
    full_url = 'https://www.google.com/searchbyimage?&image_url=' + image_url

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.11'
        ' (KHTML, like Gecko) Chrome/23.0.1271.97 Safari/537.11'
    }
    # conn.setopt(conn.WRITEFUNCTION, returned_code.write)
    response = request('GET', full_url, headers=headers, allow_redirects=True)
    return response.text

# Parses returned code (html,js,css) and assigns to array using beautifulsoup


def google_image_results_parser(code):
    soup = BeautifulSoup(code)

    # initialize 2d array
    whole_array = {'links': [],
                   'description': [],
                   'title': [],
                   'result_qty': []}

    # Links for all the search results
    for li in soup.findAll('li', attrs={'class': 'g'}):
        sLink = li.find('a')
        whole_array['links'].append(sLink['href'])

    # Search Result Description
    for desc in soup.findAll('span', attrs={'class': 'st'}):
        whole_array['description'].append(desc.get_text())

    # Search Result Title
    for title in soup.findAll('h3', attrs={'class': 'r'}):
        whole_array['title'].append(title.get_text())

    # Number of results
    for result_qty in soup.findAll('div', attrs={'id': 'resultStats'}):
        whole_array['result_qty'].append(result_qty.get_text())

    return build_json_return(whole_array)


def build_json_return(whole_array):
    return json.dumps(whole_array)


def get_gris_results(href):
    code = retrieve(href)
    return google_image_results_parser(code)

results = get_gris_results(
    'http://vppmaster.dev.superdesk.org/api/upload/55c9fdfb6cdb31004e08aa5f/raw?_schema=http')
print(results)
