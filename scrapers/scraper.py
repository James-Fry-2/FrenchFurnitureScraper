import requests
import random
import datetime as dt
import time
from bs4 import BeautifulSoup
from utils.db import scraping_db
from bson import ObjectId
from utils.google_cloud_service import GoogleCloudService

class Scraper:
  def __init__(self, marketplace):
    self.marketplace = marketplace
    self.with_proxy = False

  def add_new_section_urls(self):
    section_urls = []
    for url in self.sitemap_urls:
      try:
        raw_response = self.get_url(f"{self.root_url}{url}", with_proxy=self.with_proxy)
        returned_urls = self.scrape_section_urls(raw_response)
        section_urls = section_urls + returned_urls
      except:
        print(f"Marketplace {self.marketplace}: wrong url > {url}")
    for url in section_urls:
      self.create_section_url({
        'marketplace': self.marketplace,
        'link': url,
        'last_scraped_at': None,
        'is_valid': None
      })
    return f"Marketplace {self.marketplace}: {len(section_urls)} section urls added"

  def check_section_urls(self):
    section_urls = scraping_db.section_urls.find({'marketplace': self.marketplace, 'is_valid': None})
    for section_url in section_urls:
      url = self.format_product_list_url(section_url['link'])
      try:
        response = self.get_url(
          f"{self.root_url}{self.format_url_with_pagination(url, 1)}",
          with_proxy=self.with_proxy
        )
        total_pages = self.scrape_total_pages(response)
        if total_pages:
          self.update_section_url(section_url['_id'], { '$set': { 'is_valid': True } })
      except:
        print(f"Marketplace {self.marketplace}: wrong url > {url}")
        self.update_section_url(section_url['_id'], { '$set': { 'is_valid': False } })
    return f"Marketplace {self.marketplace}: all sections urls checked"

  def add_new_products(self):
    url_count = self.count_section_urls_to_scrape()
    if url_count == 0:
      return f"Marketplace {self.marketplace}: no section to scrape"
    section_urls = self.get_section_urls_to_scrape()
    products_count = 0
    for section_url in section_urls:
      products_count_section = 0
      try:
        url = self.format_product_list_url(section_url['link'])
        current_page = 1
        total_pages = 1
        while current_page <= total_pages:
          response = self.get_url(
            f"{self.root_url}{self.format_url_with_pagination(url, current_page)}",
            with_proxy=self.with_proxy
          )
          products = self.scrape_new_products(response)
          for product in products:
            self.create_product(product)
            products_count_section += 1
          if current_page == 1:
            total_pages = self.scrape_total_pages(response)
          current_page += 1
        self.update_section_url(section_url['_id'], {
          '$set': {
            'last_scraped_at': dt.datetime.utcnow(),
            'products_count': products_count_section,
            'error': None
          }
        })
        products_count += products_count_section
      except Exception as error:
        self.update_section_url(section_url['_id'], { '$set': {'error': str(error)} })
    return f"Marketplace {self.marketplace}: {products_count} products added"

  def update_products(self):
    product_count = None
    while product_count != 0:
      product_count = self.count_products_to_update()
      products = self.get_products_to_scrape()
      for product in products:
        try:
          response = self.get_url(f"{self.root_url}{product['product_url']}", with_proxy=self.with_proxy)
          if response is None:
            continue
          if (product['last_scraped_at']) == None:
            fields_to_update = self.scrape_product_info(response)
          else:
            fields_to_update = {}
          fields_to_update.update({
            'last_scraped_at': dt.datetime.utcnow(),
            'error': None
          })
          if self.marketplace != 'brico_depot':
            current_price = self.scrape_product_price(response)
          else:
            current_price = self.scrape_product_price(f"{self.root_url}{product['product_url']}")
          self.update_product(
            product['_id'],
            {
              '$set': fields_to_update,
              '$push' : {
                'price_ts': {
                  'date': dt.datetime.utcnow(),
                  'value': current_price
                }
              }
            }
          )
        except Exception as error:
          print(error)
          self.update_product(product['_id'], { '$set': {'error': str(error)} })
    return f"Marketplace {self.marketplace}: {product_count} products updated"
  
  """
    SUPPORT FUNCTIONS
  """

  def get_url(self, url, with_proxy=False):
    status_code = None
    print(f"Scraping url: {url} with{'' if with_proxy else 'out'} proxy")
    # while status_code != 200 and status_code != 404:
    if with_proxy:
      # proxy_username = 'brd-customer-hl_ee9057bc-zone-web_unlocker'
      # proxy_password = 'yingp2ao2lak'
      # proxy_host = 'zproxy.lum-superproxy.io:22225'
      proxy_username = 'brd-customer-hl_ee9057bc-zone-data_center'
      proxy_password = 'kkp3hjmql29e'
      proxy_host = 'brd.superproxy.io:22225'  
      session = requests.Session()
      session.proxies = {
        'http': f'http://{proxy_username}:{proxy_password}@{proxy_host}',
        'https': f'http://{proxy_username}:{proxy_password}@{proxy_host}'
      }
      headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
        'accept-language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7'
      }
      response = session.get(url, verify=False, headers=headers)
    else:
      if self.marketplace == 'leroy_merlin':
        cookies = {
          'datadome': 'sS3N8zeeFz9QEN2mVYAwbu~UWsVoF1oCIYtkBpf4jb_s9R7E3xSbvTXNJaYQpxUdn3x4qnPy~5t2A3drxRJx1F1KB2H3IrFwdCAbHsmr66qegJm1bRlXgM0R~wbdA_Z4',
          'lm-csrf': 'uD57AfOdneintQ0RvuaHH8yjHo4K31cixPhvUlxuhfA=.1701679331192.4ZoCPPl/uUBK8D83BUxGu/c2Oci/nRMzn1c8e0drbV0='
        }
      elif self.marketplace == 'but':
        cookies = {
          'datadome': 'pxr8t6RpdtBhyqPEo3RJ~i_Z44nDv7nQQiNrwvH0NffM9s05sakFtcffhJPMgykNYvGTq9eHOCrVp0EDGx68bEISmMExkuGeu8pEgXxU7ILw~7HzK7cXag~CGbFJeAcp'
        }
      else:
        cookies = {}
        
      headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'accept-language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7'
      }
      response = requests.get(url, verify=False, cookies=cookies, headers=headers)
    # status_code = response.status_code
    print(response)
    time.sleep(random.random() + 1)
    if response.status_code == 200 or response.status_code == 404:
      return BeautifulSoup(response.content, 'html.parser')
    else:
      return None

  def save_picture_in_bucket(self, reference, url):
    return GoogleCloudService().save_picture(self.marketplace, reference, url)

  # PRODUCTS

  def create_product(self, payload={}):
    if not scraping_db.products.find_one({
      'marketplace': self.marketplace,
      'reference': payload['reference']
    }):
      product_payload = {
        'brand_name': None,
        'color': None,
        'country': None,
        'created_at': dt.datetime.utcnow(),
        'depth': None,
        'finish': None,
        'height': None,
        'crossed_out_price': None,
        'last_scraped_at': None,
        'marketplace': self.marketplace,
        'material': None,
        'picture_bucket_path': None,
        'picture_url': None,
        'price_ts': [],
        'product_family': None,
        'product_type': None,
        'product_url': None,
        'reference': None,
        'title': None,
        'width': None,
        'shade': None
      }
      try:
        if payload.get('picture_url'):
          picture_bucket_path = self.save_picture_in_bucket(payload['reference'], payload['picture_url'])
          product_payload['picture_bucket_path'] = picture_bucket_path
      except:
        pass
      product_payload.update(payload)
      scraping_db.products.insert_one(product_payload)

  def update_product(self, product_id, payload={}):
    if payload.get('$set', {}).get('picture_url'):
      product = scraping_db.products.find_one({'_id': ObjectId(product_id)})
      picture_bucket_path = self.save_picture_in_bucket(product['reference'], payload.get('$set', {}).get('picture_url'))
      payload.get('$set')['picture_bucket_path'] = picture_bucket_path
    scraping_db.products.update_one({'_id': ObjectId(product_id)}, payload)

  def count_products_to_update(self):
    return scraping_db.products.count_documents({
      'marketplace': self.marketplace,
      '$or': [
        {'last_scraped_at': {'$lt': dt.datetime.utcnow() - dt.timedelta(days=30)}},
        {'last_scraped_at': None}
      ]
    })

  def get_products_to_scrape(self):
    return scraping_db.products.find({
      'marketplace': self.marketplace,
      '$or': [
        {'last_scraped_at': {'$lt': dt.datetime.utcnow() - dt.timedelta(days=30)}},
        {'last_scraped_at': None}
      ]
    }).limit(100)

  # SECTION URLS

  def create_section_url(self, payload={}):
    if not scraping_db.section_urls.find_one({'link': payload['link']}):
      scraping_db.section_urls.insert_one(payload)

  def update_section_url(self, section_url_id, payload={}):
    scraping_db.section_urls.update_one({'_id': ObjectId(section_url_id)}, payload)

  def count_section_urls_to_scrape(self):
    return scraping_db.section_urls.count_documents({
      'marketplace': self.marketplace,
      'is_valid': True,
      '$or': [
        {'last_scraped_at': {'$lt': dt.datetime.utcnow() - dt.timedelta(days=30)}},
        {'last_scraped_at': None}
      ]
    })

  def get_section_urls_to_scrape(self):
    return scraping_db.section_urls.find({
      'marketplace': self.marketplace,
      'is_valid': True,
      '$or': [
        {'last_scraped_at': {'$lt': dt.datetime.utcnow() - dt.timedelta(days=30)}},
        {'last_scraped_at': None}
      ]
    })
