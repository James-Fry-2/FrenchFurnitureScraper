from .scraper import Scraper
from static.kitea import sections_to_scrape, specs_classes
from utils.helpers import isolate_uppercase

class KiteaScraper(Scraper):

  def __init__(self):
    print('Init Kitea scraper')
    self.marketplace = 'kitea'
    self.root_url = 'https://www.kitea.com'
    self.sitemap_urls = ['/']
    self.with_proxy = False

  def scrape_section_urls(self, raw_response):
    urls = []
    sitemap_div = raw_response.find('nav', {'class': 'sm_megamenu_wrapper_vertical_menu'})
    for section in sections_to_scrape:
      section_label = sitemap_div.find('span', {'class': 'sm_megamenu_title'}, text=section[0])
      if section_label:
        section_list = section_label.parent.parent.find_next_sibling('div')
        link = section_list.find('span', text=section[1])
        if link:
          urls.append(link.parent['href'].replace('https://www.kitea.com', ''))
        else:
          print(f"Section {' - '.join(section)} not found")
    return urls
  
  def scrape_total_pages(self, raw_response):
    pagination_ul = raw_response.find('ul', {'class': 'pages-items'})
    if pagination_ul:
      return len(pagination_ul.find_all('li')) - 1
    else:
      return 1

  def scrape_new_products(self, raw_response):
    def format_product(product):
      product_url = product.find('a')['href'].replace('https://www.kitea.com', '')
      picture_url = product.find('img', {'class': 'product-image-photo'})['data-src']
      reference = product['value']
      return {
        'reference': reference,
        'product_url': product_url,
        'picture_url': picture_url
      }
    products_grid = raw_response.find('div', {'class': 'products-grid'})
    products = products_grid.find_all('li', {'class': 'product-item'})
    return map(lambda product: format_product(product), products)

  def scrape_product_info(self, raw_response):
    # Breadcrumbs info
    breadcrumbs = raw_response.find('div', {'class': 'breadcrumbs'})
    product_family = breadcrumbs.find_all('li')[-3].text.strip()
    product_type = breadcrumbs.find_all('li')[-2].text.strip()
    title = breadcrumbs.find_all('li')[-1].text.strip()

    # Brand name
    try:
      brand_name = isolate_uppercase(title)
    except:
      brand_name = None

    # Crossed out price
    price_div = raw_response.find('div', {'class': 'product-info-price'})
    crossed_out_price_span = price_div.find('span', {'data-price-type': 'oldPrice'})
    if crossed_out_price_span:
      crossed_out_price = round(float(crossed_out_price_span['data-price-amount']), 2)
    else:
      crossed_out_price = None

    # Product specs
    product_specs = raw_response.find('div', {'class': 'description-products'})
    product_specifications = {}

    for index, spec_key in enumerate(specs_classes):
      try:
        if spec_key in ['width', 'depth', 'height']:
          product_specifications[spec_key] = float(product_specs.find('span', {'class': specs_classes[spec_key]}).text.strip().replace(',', '.').replace(' cm', ''))
        else:
          product_specifications[spec_key] = product_specs.find('span', {'class': specs_classes[spec_key]}).text.strip()
      except:
        product_specifications[spec_key] = None

    return {
      'product_family': product_family,
      'product_type': product_type,
      'title': title,
      'brand_name': brand_name,
      'crossed_out_price': crossed_out_price,
      'width': product_specifications['width'],
      'depth': product_specifications['depth'],
      'height': product_specifications['height'],
      'color': product_specifications['color'],
      'material': product_specifications['material'],
      'finish': product_specifications['finish'],
    }

  def scrape_product_price(self, raw_response):
    try:
      price_div = raw_response.find('div', {'class': 'product-info-price'})
      price_span = price_div.find('span', {'data-price-type': 'finalPrice'})
      return round(float(price_span['data-price-amount']), 2)
    except:
      return None

  def format_product_list_url(self, url):
    return url

  def format_url_with_pagination(self, url, page):
    return f"{url}?p={page}"
