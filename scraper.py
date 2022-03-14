from importlib.resources import path
from CatImageScraper import CatImageScraper
from Configuration import Configuration

property_file_name = "properties.ini"

configuration = Configuration(path_to_config=property_file_name)

max_threads = configuration.getProperty('DEFAULT','MaxThreads', int)
pages_to_query = configuration.getProperty('DEFAULT','PagesToQuery', int)
image_full_size = configuration.getProperty('DEFAULT','ImageFullSize', bool)
cat_breeds = configuration.getProperty('DEFAULT','CatBreeds', list)

print(type(max_threads), type(pages_to_query), type(image_full_size), type(cat_breeds))

cat_scraper = CatImageScraper(cat_breeds=cat_breeds, page=pages_to_query, fullsize=image_full_size, maxThreads=max_threads)
cat_scraper.scrape()