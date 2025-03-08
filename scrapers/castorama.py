from .scraper import Scraper
from static.castorama import sections_to_scrape, specs_headers
from utils.helpers import isolate_uppercase
import math

class CastoramaScraper(Scraper):

  def __init__(self):
    print('Init Castorama scraper')
    self.marketplace = 'castorama'
    self.root_url = 'https://www.castorama.fr'
    self.sitemap_urls = ['/']
    self.with_proxy = False

  def scrape_section_urls(self, raw_response):
    urls = []
    sitemap_div = raw_response.find('nav', {'data-test-id': 'mega_nav'})
    for section in sections_to_scrape:
      link = sitemap_div.find('a', text=section)
      if link:
        urls.append(link['href'])
      else:
        print(f"Section {section} not found")
    return urls
  
  def scrape_total_pages(self, raw_response):
    products_nb = raw_response.find('p', {'data-test-id': 'search-options-total-results'}).text.strip().replace(' produits', '')
    return math.ceil(int(products_nb)/24)

  def scrape_new_products(self, raw_response):
    def format_product(product):
      picture_url = product.find('img', {'data-test-id': 'image'})['src']
      product_url = product.find('a', {'data-test-id': 'product-panel-main-section'})['href']
      return {
        'reference': product_url.split('/')[-1].split('_')[0],
        'product_url': product_url,
        'picture_url': picture_url
      }
    products = raw_response.find_all('div', {'data-test-id': 'product-panel'})
    return map(lambda product: format_product(product), products)

  def scrape_product_info(self, raw_response):
    # Breadcrumbs info
    breadcrumbs = raw_response.find('div', {'data-test-id': 'bread-crumbs'})
    product_family = breadcrumbs.find_all('a')[-3].text.strip()
    product_type = breadcrumbs.find_all('a')[-1].text.strip()
  
    title = raw_response.find('h1', {'id': 'product-title'}).text.strip()

    # Product specs
    product_specs = raw_response.find('div', {'id': 'product-details'})

    product_specifications = {}
    for index, spec_key in enumerate(specs_headers):
      try:
        header = product_specs.find(lambda item: item.name == 'th' and item.text in specs_headers[spec_key])
        if spec_key in ['width', 'depth', 'height']:
          product_specifications[spec_key] = float(header.find_next_sibling('td').text.strip().replace('cm', '').replace('mm', ''))
        else:
          product_specifications[spec_key] = header.find_next_sibling('td').text.strip()
      except:
        product_specifications[spec_key] = None

    return {
      'product_family': product_family,
      'product_type': product_type,
      'title': title,
      'crossed_out_price': None,
      'brand_name': product_specifications['brand_name'],
      'width': product_specifications['width'],
      'depth': product_specifications['depth'],
      'height': product_specifications['height'],
      'color': product_specifications['color'],
      'material': product_specifications['material']
    }

  def scrape_product_price(self, raw_response):
    try:
      price_div = raw_response.find('div', {'data-test-id': 'product-primary-price'})
      return float(price_div.find('div').text.strip())
    except:
      return None

  def format_product_list_url(self, url):
    return url

  def format_url_with_pagination(self, url, page):
    return f"{url}?page={page}"
