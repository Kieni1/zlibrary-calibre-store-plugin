# -*- coding: utf-8 -*-
# License: GPLv3 Copyright: 2024, poochinski9
from __future__ import absolute_import, division, print_function, unicode_literals

import json
import logging
import sys
import urllib.parse

from PyQt5.Qt import QUrl
from calibre import url_slash_cleaner
from calibre.utils.browser import Browser
from calibre.gui2 import open_url
from calibre.gui2.store import StorePlugin
from calibre.gui2.store.basic_config import BasicStoreConfig
from calibre.gui2.store.search_result import SearchResult
from calibre.gui2.store.web_store_dialog import WebStoreDialog

USER_AGENT = "Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko"

BASE_API_URL = "https://z-lib.gl/eapi"
BASE_WEB_URL = "https://z-library.sk"


# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def api_request(url: str, payload: dict = None) -> dict:
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
            json_response = api_request(url, payload)
            current_page=json_response["pagination"]["current"]
            total_pages=json_response["pagination"]["total_pages"]
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

    return results

class ZLibraryStorePlugin(BasicStoreConfig, StorePlugin):
    def open(self, parent=None, detail_item=None, external=False):
        url = BASE_WEB_URL

        if external or self.config.get("open_external", False):
            open_url(QUrl(url_slash_cleaner(detail_item if detail_item else url)))
        else:
            d = WebStoreDialog(self.gui, url, parent, detail_item)
            d.setWindowTitle(self.name)
            d.set_tags(self.config.get("tags", ""))
            d.exec_()

    @staticmethod
    def get_details(search_result: SearchResult, retries=3):
        formats_json = api_request(search_result.formats)
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
