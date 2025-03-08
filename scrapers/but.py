import json
import math
from .scraper import Scraper
from static.but import sections_to_scrape, specs_headers
from utils.helpers import isolate_uppercase, check_image_url

class ButScraper(Scraper):

  def __init__(self):
    print('Init But scraper')
    self.marketplace = 'but'
    self.root_url = 'https://www.but.fr'
    self.sitemap_urls = [
      '/mobilier/index-a10316.html',
      '/chambre-literie/index-a10317.html'
    ]
    self.with_proxy = False

  def scrape_section_urls(self, raw_response):
    # The 'baby' pages are not visible on the sitemap because of a display error, the links are set here for now
    urls = [
      '/puericulture/chambre-bebe/lit-bebe/index-c11408.html',
      '/puericulture/chambre-bebe/commode-commode-table-a-langer/index-c11415.html',
      '/puericulture/chambre-bebe/coffre-a-jouets/index-c11417.html'
    ]
    sitemap_div = raw_response.find('section', {'class': 'niveaux'})
    for section in sections_to_scrape:
      link = sitemap_div.find('li', text=f"{section}")
      if link:
        urls.append(link.find('a')['href'])
    return urls

  def scrape_total_pages(self, raw_response):
    n_products = int(raw_response.find('p', {'class': 'dp__content__numberProducts'}).text.strip().split(' ')[0])
    return math.ceil(n_products / 60)

  def scrape_new_products(self, raw_response):
    def format_product(product):
      product_data = json.loads(product.find('a')['data-gtm-product'])
      return {
        'reference': str(product_data['product_ean']),
        'product_url': product.find('a')['href']
      }
    products = raw_response.find_all('div', {'class': 'product'})
    return map(lambda product: format_product(product), products)  

  def scrape_product_info(self, raw_response):
    # Picture
    try:
      picture_url = raw_response.find('div', {'class': 'product-image-grid'}).find('source')['srcset']
    except:
      picture_url = None
    
    # Breadcrumbs info
    breadcrumbs = raw_response.find('p', {'class': 'breadcrumb-product'})
    try:
      product_family = breadcrumbs.find_all('a')[-2].text.strip()
      product_type = breadcrumbs.find_all('a')[-1].text.strip()
    except:
      product_family = None
      product_type = None

    title = raw_response.find('h1', {'class': 'product-title'}).text.strip()

    brand_name = isolate_uppercase(title)

    # Crossed out price
    try:
      crossed_out_price_p = raw_response.find('p', {'class': 'old-price'})
      crossed_out_price = float(crossed_out_price_p.text.strip().replace('€', '').replace(',', '.'))
    except:
      crossed_out_price = None

    # Product specs
    product_specs = raw_response.find('div', {'class': 'features'})
    product_specifications = {}

    for index, spec_key in enumerate(specs_headers):
      try:
        header = product_specs.find(lambda item: item.text in specs_headers[spec_key])
        if spec_key in ['width', 'depth', 'height']:
          product_specifications[spec_key] = float(header.find_next_sibling('div').text.strip().replace(' cm', ''))
        else:
          product_specifications[spec_key] = header.find_next_sibling('div').text.strip()
      except:
        product_specifications[spec_key] = None

    # Country
    made_in_france = raw_response.find('img', {'alt': 'Picto Fabrication française'})
    if made_in_france:
      country = 'France'
    else:
      country = None

    return {
      'picture_url': picture_url,
      'product_family': product_family,
      'product_type': product_type,
      'title': title,
      'brand_name': brand_name,
      'crossed_out_price': crossed_out_price,
      'width': product_specifications['width'],
      'depth': product_specifications['depth'],
      'height': product_specifications['height'],
      'color': product_specifications['color'],
      'shade': product_specifications['shade'],
      'material': product_specifications['material'],
      'finish': product_specifications['finish'],
      'country': country
    }

  def scrape_product_price(self, raw_response):
    try:
      price_div = raw_response.find('div', {'class': 'price-eco'}).find('div', {'class': 'price'})
      return float(price_div.text.strip().replace('€', '').replace(',', '.'))
    except:
      return None

  def format_product_list_url(self, url):
    return f"{url.replace('.html', '')}/NW-12099-vendu-par~but"

  def format_url_with_pagination(self, url, page):
    return f"{url}?PageSize=60&PageIndex={page}"
