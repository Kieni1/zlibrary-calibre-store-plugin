# -*- coding: utf-8 -*-
# License: GPLv3 Copyright: 2024, poochinski9
from __future__ import absolute_import, division, print_function, unicode_literals

import json
import logging
import re
import sys
import time
import urllib.parse
from urllib.robotparser import RobotFileParser

from PyQt5.Qt import QUrl
from bs4 import BeautifulSoup
from calibre import browser, url_slash_cleaner
from calibre.utils.browser import Browser
from calibre.gui2 import open_url
from calibre.gui2.store import StorePlugin
from calibre.gui2.store.basic_config import BasicStoreConfig
from calibre.gui2.store.search_result import SearchResult
from calibre.gui2.store.web_store_dialog import WebStoreDialog
import ssl

BASE_URL = "https://libgen.gs"
USER_AGENT = "Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko"

BASE_API_URL = "https://z-lib.gl/eapi"
BASE_WEB_URL = "https://z-library.sk"

# Declare global variables at the module level
title_index = None
image_index = None
author_index = None
year_index = None
pages_index = None
size_index = None
ext_index = None
mirrors_index = None

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def custom_browser(url: str, payload: dict = None) -> dict:
    data = None
    if payload is not None:
        data = urllib.parse.urlencode(payload).encode('utf-8')

    browser = Browser()
    browser.set_handle_robots(False)
    browser.set_user_agent(USER_AGENT)
    browser.set_current_header(header="content-type", value="application/x-www-form-urlencoded")
    response = browser.open(url, data=data).read()
    json_response = json.loads(response)
    return json_response


#####################################################################
# Plug-in base class
#####################################################################
def search_libgen(query, max_results:int, timeout=60):
    results = []
    total_pages = 1
    current_page = 1

    payload = {
        "message": query,
        "order": "popular",
        "languages[]": "null",
        "extensions[]": "null"
    }

    while current_page<=total_pages and len(results)<max_results:
        try:
            url = f'{BASE_API_URL}/book/search'
            json_response = custom_browser(url, payload)
            current_page=json_response["pagination"]["current"]
            total_pages=json_response["pagination"]["total_pages"]
            print(f'Current page {current_page}')
            print(f'Total pages {total_pages}')
            print(f'Max results {max_results}')
            for book in json_response["books"]:
                s = SearchResult()
                s.store_name = "Z-Library"
                s.title = book["title"]
                s.author = book["author"]
                s.cover_url = book["cover"]
                s.drm = 2
                s.formats = f"https://z-lib.gl/eapi/book/{book["id"]}/{book["hash"]}/formats"
                s.detail_item = f'{BASE_WEB_URL}{book["href"]}'
                results.append(s)

            payload = {
                "message": query,
                "order": "popular",
                "languages[]": "null",
                "extensions[]": "null",
                "page":current_page+1
            }
        except Exception as e:
            logger.error(e)

    print(len(results))
    return results

def extract_indices(soup):
    elements = ['Author(s)', 'Year', 'Pages', 'Size', 'Ext', 'Mirrors']
    indices = {}

    for idx, th in enumerate(soup.find_all('th')):
        for element in elements:
            if element in th.get_text():
                indices[element] = idx

    global author_index, year_index, pages_index, size_index, ext_index, mirrors_index, title_index, image_index

    image_index = 0
    title_index = 1
    author_index = indices.get('Author(s)')
    year_index = indices.get('Year')
    pages_index = indices.get('Pages')
    size_index = indices.get('Size')
    ext_index = indices.get('Ext')
    mirrors_index = indices.get('Mirrors')


def transform_download_url(url):
    # Pattern for the first format: /ads23875abc (where abc can be letters and numbers)
    pattern1 = re.compile(r'/ads([a-fA-F0-9]+)')
    # Pattern for the second format: /ads.php?md5=235798237abc (where abc can be letters and numbers)
    pattern2 = re.compile(r'/ads\.php\?md5=([a-fA-F0-9]+)')

    # Check and transform the first format
    match1 = pattern1.match(url)
    if match1:
        return f'/get.php?md5={match1.group(1)}'

    # Check and transform the second format
    match2 = pattern2.match(url)
    if match2:
        return f'/get.php?md5={match2.group(1)}'

    # If no match, return the original URL
    return url


def build_search_result(tr):
    tds = tr.find_all('td')
    s = SearchResult()

    # Extracting the title
    title_links = tds[title_index].find_all("a", href=True)
    s.title = " ".join(link.text.strip() for link in title_links if link.text.strip())

    # Extracting the author
    s.author = tds[author_index].text.strip()

    # Extracting size, pages, and year
    size = tds[size_index].text.strip()
    pages = tds[pages_index].text.strip()
    year = tds[year_index].text.strip()

    if pages == "0 pages":
        s.price = f"{size}\n{year}"
    else:
        s.price = f"{size}\n{pages} pages\n{year}"

    # Extracting formats
    s.formats = tds[ext_index].text.strip().upper()

    # Extracting the details URL
    first_link_in_last_td = tds[mirrors_index].find("a", href=True)

    # Details url:
    try:
        s.detail_item = BASE_URL + first_link_in_last_td["href"].replace("get.php", "ads.php")
    except:
        s.detail_item = None

    # Setting DRM status
    s.drm = SearchResult.DRM_UNLOCKED

    # Extracting image
    try:
        image_src = tds[image_index].find("img").get("src")
    except:
        image_src = None
        logger.exception("Error extracting image src")

    if image_src:
        s.cover_url = BASE_URL + image_src

    return s


class LibgenStorePlugin(BasicStoreConfig, StorePlugin):
    def open(self, parent=None, detail_item=None, external=False):
        url = BASE_URL

        if external or self.config.get("open_external", False):
            open_url(QUrl(url_slash_cleaner(detail_item if detail_item else url)))
        else:
            d = WebStoreDialog(self.gui, url, parent, detail_item)
            d.setWindowTitle(self.name)
            d.set_tags(self.config.get("tags", ""))
            d.exec_()

    @staticmethod
    def get_details(search_result: SearchResult, retries=3):
        formats_json = custom_browser(search_result.formats)
        formats = []
        for format in formats_json["books"]:
            format_extension = format["extension"]
            formats.append(format_extension.upper())
        search_result.formats = " ".join(formats)

    @staticmethod
    def search(query, max_results=10, timeout=60):
        for result in search_libgen(query, max_results=max_results, timeout=timeout):
            yield result

    def config_widget(self):
        pass


if __name__ == "__main__":
    query_string = " ".join(sys.argv[1:])
    for result in search_libgen(bytes(" ".join(sys.argv[1:]), "utf-8")):
        print(result)
