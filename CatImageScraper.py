from http.client import HTTPResponse
import urllib.request as request
import urllib.parse as parse
import re
import json
import os

class CatImageScraper:

    def __init__(self, cat_breed, page) -> None:
        self.cat_breed = cat_breed
        self.cat_breed_query = cat_breed.replace(' ', "%20") + " cat"
        self.duckduckgo_content_url = "https://duckduckgo.com/i.js"
        self.image_parent_path = "cat_breeds"
        self.image_counter = 1
        self.items_per_page = 100     # each page contains 100 images via duckduckgo
        self.page = page
        self.headers = {
            "Host": "duckduckgo.com",
            "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:97.0) Gecko/20100101 Firefox/97.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://duckduckgo.com/",
            "Upgrade-Insecure-Requests": "1"
        }

    # Vqd is a unique identifier used in duckduckgo search. Seemingly unique per client.
    def extractVqd(self) -> str:
        duckduckgo_initialurl = "https://duckduckgo.com/"
        params = {
            "q": self.cat_breed_query
        }
        request_obj = self.generateRequest(duckduckgo_initialurl, params, self.headers)
        # Response from urlopen comes as bytes when read, so need to decode to string
        response = request.urlopen(request_obj)
        response_string = self.decodeResponseToString(response)
        vqd_extract_regex = re.search(r'vqd=\'(.*?)\'', response_string, re.M|re.I)
        vqd = vqd_extract_regex.group(1)
        return vqd

    def generateRequest(self, url: str, params: dict, headers: dict) -> request.Request:
        params_string = parse.urlencode(params)
        request_obj = request.Request(url + "?" + params_string)
        for key, value in headers.items():
            request_obj.add_header(key, value)

        return request_obj

    def decodeResponseToString(self, response: HTTPResponse) -> str:
        response_bytes = response.read()
        return response_bytes.decode("utf8") # TODO: read from Content-Type header for charset


    def getJsonContent(self, current_page: int, vqd: str) -> None:
        params = {
            "q": self.cat_breed_query,
            "o": "json",
            "p": 1,
            "s": current_page * self.items_per_page,
            "u": "bing",
            "f": ",,,,,",
            "l": "us-en",
            "vqd": vqd
        }
        request_obj = self.generateRequest(self.duckduckgo_content_url, params, self.headers)
        response = request.urlopen(request_obj)
        response_string = self.decodeResponseToString(response)
        json_response = json.loads(response_string)
        return json_response

    def extractThumbnailUrl(self, json_response) -> list:
        return [e["thumbnail"] for e in json_response["results"]]

    def downloadThumbnail(self, thumbnail_urls: list) -> None:
        # check file exists
        parent_relative_path = "./" + self.image_parent_path
        if not os.path.isdir(parent_relative_path):
            os.mkdir(parent_relative_path)

        breed_relative_path = parent_relative_path + "/" + self.cat_breed
        if not os.path.isdir(breed_relative_path):
            os.mkdir(breed_relative_path)

        for url in thumbnail_urls:
            request.urlretrieve(url, breed_relative_path + "/" + self.cat_breed + "_" + str(self.image_counter))
            self.image_counter += 1

    def scrape(self) -> None:

        # Get vqd from initial query
        vqd = self.extractVqd()

        # retrieve json content (with thumbnail image links) in a step interval
        for i in range(1, self.page + 1):
            json_response = self.getJsonContent(current_page=i, vqd=vqd)

            thumbnail_urls = self.extractThumbnailUrl(json_response)

            self.downloadThumbnail(thumbnail_urls)