import math
from .scraper import Scraper
from static.conforama_es import sections_to_scrape, specs_headers
from utils.helpers import isolate_uppercase

class ConforamaEsScraper(Scraper):

  def __init__(self):
    print('Init Conforama ES scraper')
    self.marketplace = 'conforama_es'
    self.root_url = 'https://www.conforama.es'
    self.sitemap_urls = ['/']
    self.with_proxy = False

  def scrape_section_urls(self, raw_response):
    urls = []
    sitemap_div = raw_response.find('nav', {'id': 'menuV4'})
    for section in sections_to_scrape:
      link = sitemap_div.find('a', text=section)
      if link:
        urls.append(link['href'])
      else:
        print(f"Section {section} not found")
    return urls
  
  def scrape_total_pages(self, raw_response):
    pagination = raw_response.find('div', {'class': 'paginationV2'})
    n_products = int(pagination.find('span', {'class': 'to'}).text.strip())
    return math.ceil(n_products / 30)

  def scrape_new_products(self, raw_response):
    def format_product(product):
      picture_url = product.find('img')['src']
      return {
        'reference': str(product['data-itemreference']),
        'product_url': product.find('a')['href'].replace('https://www.conforama.es', ''),
        'picture_url': picture_url
      }
    section = raw_response.find('section', {'id': 'productlist-listing'}).find('section')
    products = section.find_all('article')
    return map(lambda product: format_product(product), products)

  def scrape_product_info(self, raw_response):
    # Breadcrumbs info
    breadcrumbs = raw_response.find('section', {'class': 'breadcrumbs'})
    product_family = breadcrumbs.find_all('a')[-2].text.strip()
    product_type = breadcrumbs.find_all('a')[-1].text.strip()
    title = breadcrumbs.find_all('span')[-1].text.strip()

    # Crossed out price
    crossed_out_price_span = raw_response.find('div', {'class': 'price-before'}).find('span')
    if crossed_out_price_span:
      crossed_out_price = float(crossed_out_price_span.text.strip().replace('.', '').replace(' €', '').replace(',', '.'))
    else:
      crossed_out_price = None
  
    brand_name = isolate_uppercase(title)

    # Product specs
    product_specs = raw_response.find('section', {'id': 'info'}).find('div', {'class': 'content'})
    product_specifications = {}

    for index, spec_key in enumerate(specs_headers):
      try:
        header = product_specs.find(lambda item: item.name == 'dt' and item.text in specs_headers[spec_key])
        if spec_key in ['width', 'depth', 'height']:
          product_specifications[spec_key] = float(header.find_next_sibling('dd').text.strip().replace(' cm', '').replace(',', '.'))
        else:
          product_specifications[spec_key] = header.find_next_sibling('dd').text.strip()
      except:
        product_specifications[spec_key] = None

    if raw_response.find('div', {'class': 'configurables-colors'}):
      colors_div = raw_response.find('div', {'class': 'configurables-colors'})
      colors = map(lambda figure: figure['data-gtm-detail-variant'], colors_div.find_all('figure'))
      color = ', '.join(colors)
    else:
      try:
        color = raw_response.find('div', {'class': 'right'}).find('div', {'class': 'simple'}).find('div', {'class': 'desc'})['data-dimension']
      except:
        color = None

    return {
      'product_family': product_family,
      'product_type': product_type,
      'title': title,
      'brand_name': brand_name,
      'crossed_out_price': crossed_out_price,
      'width': product_specifications['width'],
      'depth': product_specifications['depth'],
      'height': product_specifications['height'],
      'color': color,
      'material': product_specifications['material'],
      'finish': product_specifications['finish']
    }

  def scrape_product_price(self, raw_response):
    try:
      price_div = raw_response.find('div', {'class': 'price-after'})
      return float(price_div.text.strip().replace('.', '').replace(' €', '').replace(',', '.'))
    except:
      return None

  def format_product_list_url(self, url):
    return f"{url}?attribute=businesslinecode%7cCONFO"

  def format_url_with_pagination(self, url, page):
    return url + f"&page={page}"
