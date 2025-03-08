import json
import re
from .scraper import Scraper
from static.ikea import sections_to_scrape, specs_headers

class IkeaScraper(Scraper):

  def __init__(self):
    print('Init Ikea scraper')
    self.marketplace = 'ikea'
    self.root_url = 'https://www.ikea.com'
    self.sitemap_urls = [
      '/fr/fr/cat/meubles-fu001/',
      '/fr/fr/cat/rangement-st001/',
      '/fr/fr/cat/travailler-de-la-maison-700291/',
      '/fr/fr/cat/cuisine-et-electromenager-ka001/',
      '/fr/fr/cat/salle-de-bain-ba001/'
    ]
    self.with_proxy = False

  def scrape_section_urls(self, raw_response):
    urls = []
    section_links = raw_response.find_all('a', {'class': 'vn-link'})
    for section_link in section_links:
      section_title = section_link.find('span', {'class': 'vn__nav__title'}).text.strip()
      if section_title in sections_to_scrape:
        section_href = section_link['href']
        sub_raw_response = self.get_url(section_href)
        sub_section_links = sub_raw_response.find_all('a', {'class': 'vn-link'})
        for sub_section_link in sub_section_links:
          sub_section_href = sub_section_link['href'].replace('https://www.ikea.com', '')
          urls.append(sub_section_href)
    return urls
  
  def scrape_total_pages(self, raw_response):
    return 1

  def scrape_new_products(self, raw_response):
    def format_product(product):
      product_div = product.find('div', {'class': 'pip-product-compact'})
      return {
        'reference': str(product_div['data-product-number']),
        'product_url': product_div.find('a')['href'].replace('https://www.ikea.com', '')
      }
    products = raw_response.find_all('div', {'class': 'plp-fragment-wrapper'})
    return map(lambda product: format_product(product), products)

  def scrape_product_info(self, raw_response):

    # Breadcrumbs info
    breadcrumbs = raw_response.find('ol', {'class': 'bc-breadcrumb__list'})
    try:
      product_family = breadcrumbs.find_all('a')[-3].text.strip()
      product_type = breadcrumbs.find_all('a')[-2].text.strip()
    except:
      product_family = None
      product_type = None

    title = raw_response.find('span', {'class': 'pip-header-section__description-text'}).string.split(',')[0].strip()
    try:
      color = raw_response.find('span', {'class': 'pip-header-section__description-text'}).string.split(',')[1].strip()
    except:
      color = None

    product_data = json.loads(raw_response.find('div', {'class': 'pip-product__subgrid'})['data-hydration-props'])
    brand_name = product_data['buyModule']['productName']
    try:
      crossed_out_price = float(product_data['pipPriceModule']['price']['previousPriceProps']['price']['integer'].replace(' ',''))
    except:
      crossed_out_price = None

    picture_button = raw_response.find('button', {'class': 'pip-product-gallery__thumbnail--active'})
    picture_url = picture_button.find('span').find('img')['src']

    dimensions_container = raw_response.find('div', {'class': 'pip-product-dimensions__dimensions-container'})
    dimensions = dimensions_container.find_all('p', {'class': 'pip-product-dimensions__measurement-wrapper'})
    dimensions_formatted = list(map(lambda dim: dim.text.strip().replace(u'\xa0', '').split(':'), dimensions))

    # Product specs
    product_specifications = {}
    for index, spec_key in enumerate(specs_headers):
      product_specifications[spec_key] = None
      try:
        for dimension in dimensions_formatted:
          if dimension[0] in specs_headers[spec_key]:
            product_specifications[spec_key] = float(dimension[1].split(' ')[0])
      except:
        pass
    
    material_header = raw_response.find('span', {'class': 'pip-product-details__material-header'})
    if material_header:
      material = material_header.next_sibling.find('dd').text.strip()
    else:
      material = None

    # Super custom stuff, only for Ikea
    if raw_response.find('ul', {'id': 'product-style-picker-COLOUR'}):
      color_variants = raw_response.find('div', {'class': 'pip-product-styles__items'}).find_all('a', {'class': 'pip-product-styles__link'})
      for variant in color_variants:
        sub_div = variant.find('div', {'class': 'pip-product-styles__item'})
        if 'pip-product-styles__item--selected' in sub_div['class']:
          continue
        product_url = variant['href'].replace('https://www.ikea.com', '').replace('#content', '')
        self.create_product({
          'reference': str(re.sub('[^0-9]', '', product_url.split('-')[-1])),
          'product_url': product_url
        })

    return {
      'product_family': product_family,
      'product_type': product_type,
      'title': title,
      'brand_name': brand_name,
      'crossed_out_price': crossed_out_price,
      'picture_url': picture_url,
      'width': product_specifications['width'],
      'depth': product_specifications['depth'],
      'height': product_specifications['height'],
      'color': color,
      'shade': None,
      'material': material,
      'finish': None,
      'country': None
    }

  def scrape_product_price(self, raw_response):
    product_json = raw_response.find('div', {'class': 'pip-product__subgrid'})
    if product_json:
      product_data = json.loads(product_json['data-hydration-props'])
      price_data = product_data['pipPriceModule']['price']['mainPriceProps']['price']
      return float(price_data['integer'].replace(' ','') + '.' + price_data['decimals'])
    else:
      return None

  def format_product_list_url(self, url):
    return url

  def format_url_with_pagination(self, url, page):
    return f"{url}?page=5000"
