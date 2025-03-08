import json
import urllib3
import datetime
from flask import Flask, request, Response

from scrapers.brico_depot import BricoDepotScraper
from scrapers.brico_marche import BricoMarcheScraper
from scrapers.but import ButScraper
from scrapers.castorama import CastoramaScraper
from scrapers.conforama_es import ConforamaEsScraper
from scrapers.conforama import ConforamaScraper
from scrapers.ikea import IkeaScraper
from scrapers.kitea import KiteaScraper
from scrapers.leen_bakker import LeenBakkerScraper
from scrapers.leroy_merlin import LeroyMerlinScraper
from scrapers.moviflor import MoviflorScraper
from exporter.exporter import Exporter
from utils.db import scraping_db

app = Flask(__name__)
urllib3.disable_warnings()

SCRAPERS = {
  'brico_depot': BricoDepotScraper,
  'brico_marche': BricoMarcheScraper,
  'but': ButScraper,
  'castorama': CastoramaScraper,
  'conforama_es': ConforamaEsScraper,
  'conforama': ConforamaScraper,
  'ikea': IkeaScraper,
  'kitea': KiteaScraper,
  'leen_bakker': LeenBakkerScraper,
  'leroy_merlin': LeroyMerlinScraper,
  'moviflor': MoviflorScraper
}

@app.route('/')
def home():
  response = 'CBA Meubles scraping app'
  return Response(json.dumps(response), mimetype='application/json')

@app.route('/add_new_section_urls/<marketplace>', methods=['GET'])
def add_new_section_urls(marketplace):
  return SCRAPERS[marketplace]().add_new_section_urls()

@app.route('/reset_section_urls/<marketplace>', methods=['GET'])
def reset_section_urls(marketplace):
  scraping_db.section_urls.update_many({'marketplace': marketplace}, {'$set': {
    'is_valid': None,
    'last_scraped_at': None,
    'error': None,
    'products_count': None
  }})
  return f'Marketplace {marketplace}: section urls reset'

@app.route('/check_section_urls/<marketplace>', methods=['GET'])
def check_section_urls(marketplace):
  return SCRAPERS[marketplace]().check_section_urls()

@app.route('/add_new_products/<marketplace>', methods=['GET'])
def add_new_products(marketplace):
  return SCRAPERS[marketplace]().add_new_products()

@app.route('/update_products/<marketplace>', methods=['GET'])
def update_products(marketplace):
  return SCRAPERS[marketplace]().update_products()

@app.route('/export_data/<marketplace>', methods=['GET'])
def export_data(marketplace):
  Exporter(marketplace).export_to_gdrive()
  return 'Data exported'

@app.route('/remove_duplicates/<marketplace>', methods=['GET'])
def custom_action(marketplace):
  pipeline = [
    {
      '$match': {'marketplace': marketplace}
    },
    {
      '$group': {
          '_id': {'reference': '$reference'},
          'unique_id': {'$first': '$_id'}
      }
    },
    {
        '$project': {'_id': '$unique_id'}
    }
  ]
  distinct_documents = list(scraping_db.products.aggregate(pipeline))
  result = scraping_db.products.delete_many({
    'marketplace': marketplace,
    '_id': {'$nin': [doc['_id'] for doc in distinct_documents]}
  })
  return f"Deleted {result.deleted_count} duplicate documents"

if __name__ == '__main__':
    app.run(debug=True)
