from concurrent.futures import ThreadPoolExecutor
from http.client import HTTPResponse
from nis import cat
import urllib.request as request
import urllib.parse as parse
import re
import json
import os

class CatImageScraper:

    def __init__(self, cat_breeds, page, fullsize=False, maxThreads=1) -> None:
        self.cat_breeds = cat_breeds
        self.duckduckgo_content_url = "https://duckduckgo.com/i.js"
        self.image_parent_path = "cat_breeds"
        self.items_per_page = 100     # each page contains 100 images via duckduckgo
        self.page = page
        self.fullsize = fullsize
        self.maxThreads = maxThreads
        self.headers = {
            "Host": "duckduckgo.com",
            "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:97.0) Gecko/20100101 Firefox/97.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://duckduckgo.com/",
            "Upgrade-Insecure-Requests": "1"
        }

    # Vqd is a unique identifier used in duckduckgo search. Seemingly unique per client.
    def extractVqd(self, cat_breed: str) -> str:
        duckduckgo_initialurl = "https://duckduckgo.com/"
        params = {
            "q": cat_breed.replace(' ', "%20") + " cat"
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


    def getJsonContent(self, cat_breed: str, current_page: int, vqd: str) -> None:
        params = {
            "q": cat_breed.replace(' ', "%20") + " cat",
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

    def extractImageUrl(self, json_response) -> list:
        if self.fullsize:
            return [e["image"] for e in json_response["results"]]
        else:
            return [e["thumbnail"] for e in json_response["results"]]

    def downloadImage(self, cat_breed: str, image_urls: list, image_counter: int) -> int:
        # check file exists
        parent_relative_path = "./" + self.image_parent_path
        if not os.path.isdir(parent_relative_path):
            os.mkdir(parent_relative_path)

        breed_relative_path = parent_relative_path + "/" + cat_breed
        if not os.path.isdir(breed_relative_path):
            os.mkdir(breed_relative_path)

        for url in image_urls:
            request.urlretrieve(url, breed_relative_path + "/" + cat_breed + "_" + str(image_counter))
            image_counter += 1

        return image_counter

    def retrieveAndDownload(self, cat_breed: str):
        # Get vqd from initial query
        vqd = self.extractVqd(cat_breed)

        # retrieve json content (with image links) in a step interval
        page_limit = self.page + 1
        image_counter = 1
        for i in range(1, page_limit):
            json_response = self.getJsonContent(cat_breed=cat_breed, current_page=i, vqd=vqd)
            image_urls = self.extractImageUrl(json_response)
            image_counter = self.downloadImage(cat_breed=cat_breed, image_urls=image_urls, image_counter=image_counter)

    def processCatBreeds(self, cat_breeds: list):
        for cat_breed in cat_breeds:
            self.retrieveAndDownload(cat_breed=cat_breed)

    def scrape(self) -> None:
        cat_breed_partitions = list(splitList(self.cat_breeds, 5))

        with ThreadPoolExecutor(max_workers=self.maxThreads) as executor:
            for partition in cat_breed_partitions:
                executor.submit(self.processCatBreeds, partition)

def splitList(input_list: list, number_of_parts: int):
    k, m = divmod(len(input_list), number_of_parts)
    return (input_list[i * k + min(i, m): (i + 1) * k + min (i + 1, m)] for i in range(number_of_parts))