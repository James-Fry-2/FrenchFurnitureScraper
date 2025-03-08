from .scraper import Scraper
from static.leroy_merlin import sections_to_scrape, specs_headers

class LeroyMerlinScraper(Scraper):

  def __init__(self):
    print('Init Leroy Merlin scraper')
    self.marketplace = 'leroy_merlin'
    self.root_url = 'http://www.leroymerlin.fr'
    self.sitemap_urls = [
      '/produits/meuble/meuble-de-salon/',
      '/produits/meuble/meuble-de-chambre/',
      '/produits/meuble/meuble-de-bureau/',
      '/produits/meuble/meuble-entree/',
      '/produits/meuble/meuble-de-salle-a-manger/',
      '/produits/meuble/meuble-de-cuisine/',
      '/produits/salle-de-bains/meuble-de-salle-de-bains/',
      '/produits/salle-de-bains/meuble-wc/'
    ]
    self.with_proxy = False

  def scrape_section_urls(self, raw_response):
    urls = []
    sitemap_div = raw_response.find('div', {'id': 'component-childrencategories'})
    for section in sections_to_scrape:
      link = sitemap_div.find('a', text=section)
      if link:
        urls.append(link['href'])
    return urls
  
  def scrape_total_pages(self, raw_response):
    nav_element = raw_response.find('nav', {'aria-label': 'pagination'})
    return int(nav_element['data-max-page'])

  def scrape_new_products(self, raw_response):
    def format_product(product):
      picture = product.find('picture')
      if picture.has_attr('data-default'):
        picture_url = picture['data-default']
      else:
        picture_url = picture.find('img')['src']
      product_url = product.find('a', {'class': 'kl-tile-link'})['href']
      return {
        'reference': product['data-product-list-id'],
        'product_url': product_url,
        'picture_url': picture_url
      }
    products = raw_response.find_all('li', {'class': 'l-resultsList__item'})
    return map(lambda product: format_product(product), products)

  def scrape_product_info(self, raw_response):
    # Breadcrumbs info
    breadcrumbs = raw_response.find('ul', {'class': 'mc-breadcrumb__container'})
    product_family = breadcrumbs.find_all('a')[-3].text.strip()
    product_type = breadcrumbs.find_all('a')[-2].text.strip()
    title = breadcrumbs.find('span', {'class': 'mc-breadcrumb__current'}).text.strip()

    # Crossed out price
    price_container = raw_response.find('div', {'class': 'o-productoffer__price-container'})
    crossed_out_price_span = price_container.find('span', {'class': 'km-price__from-without-offer'})
    if crossed_out_price_span:
      crossed_out_price = float(crossed_out_price_span.text.strip().replace(' €', ''))
    else:
      crossed_out_price = None

    # Product specs
    product_specs = raw_response.find('table', class_='o-product-features')
    product_specifications = {}

    for index, spec_key in enumerate(specs_headers):
      try:
        header = product_specs.find(lambda item: item.name == 'th' and item.text in specs_headers[spec_key])
        if spec_key in ['width', 'depth', 'height']:
          product_specifications[spec_key] = float(header.find_next_sibling('td').text.strip())
        else:
          product_specifications[spec_key] = header.find_next_sibling('td').text.strip()
      except:
        product_specifications[spec_key] = None

    return {
      'product_family': product_family,
      'product_type': product_type,
      'title': title,
      'crossed_out_price': crossed_out_price,
      'brand_name': product_specifications['brand_name'],
      'width': product_specifications['width'],
      'depth': product_specifications['depth'],
      'height': product_specifications['height'],
      'color': product_specifications['color'],
      'shade': product_specifications['shade'],
      'material': product_specifications['material'],
      'country': product_specifications['country']
    }

  def scrape_product_price(self, raw_response):
    try:
      price_container = raw_response.find('div', {'class': 'o-productoffer__price-container'})
      price_span = price_container.find('span', {'class': 'js-main-price'})
      return float(price_span.text.strip().replace(' €', ''))
    except:
      return None

  def format_product_list_url(self, url):
    return url + '?filters=%7B"vendu-par"%3A"LEROY+MERLIN"%7D'

  def format_url_with_pagination(self, url, page):
    return url + f"&p={page}"