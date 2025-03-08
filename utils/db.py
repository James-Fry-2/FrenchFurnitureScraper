import os
import certifi
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

connection_string = os.environ.get('DB_CONNECTION_STRING')

scraping_client = MongoClient(connection_string, tlsCAFile=certifi.where())

if os.environ.get('FLASK_ENV') == 'development':
	scraping_db = scraping_client['cba-meubles-scraping-dev']
else:
	scraping_db = scraping_client['cba-meubles-scraping']