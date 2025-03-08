from .scraper import Scraper
from static.conforama import sections_to_scrape, specs_headers
from utils.helpers import isolate_uppercase

class ConforamaScraper(Scraper):

  def __init__(self):
    print('Init Conforama scraper')
    self.marketplace = 'conforama'
    self.root_url = 'https://www.conforama.fr'
    self.sitemap_urls = ['/plan-du-site']
    self.with_proxy = True

  def scrape_section_urls(self, raw_response):
    urls = []
    sitemap_div = raw_response.find('div', {'class': 'sitemap'})
    for section in sections_to_scrape:
      link = sitemap_div.find('a', text=f" {section}")
      if link:
        urls.append(link['href'])
      else:
        print(f"Section {section} not found")
    return urls
  
  def scrape_total_pages(self, raw_response):
    pagination_div = raw_response.find('div', {'id': 'c-r_pagination'})
    pagination_ul = pagination_div.find('ul')
    if pagination_ul:
      last_page_link = pagination_ul.find_all('a')[-1]
      return int(last_page_link.text)
    else:
      return 1

  def scrape_new_products(self, raw_response):
    def format_product(product):
      picture = product.find('div', {'class': 'imageProductRef'}).find('img')
      if picture.has_attr('data-frz-src'):
        picture_url = picture['data-frz-src']
      elif picture.has_attr('src'):
        picture_url = picture['src']
      else:
        picture_url = None
      return {
        'reference': str(product.find('a', {'class': 'extendLink'})['tcproductclick']),
        'product_url': product.find('a', {'class': 'extendLink'})['href'].replace('https://www.conforama.fr', ''),
        'picture_url': picture_url
      }
    products = raw_response.find_all('article', {'class': 'box-product'})
    return map(lambda product: format_product(product), products)

  def scrape_product_info(self, raw_response):
    # Breadcrumbs info
    breadcrumbs = raw_response.find('div', {'id': 'breadcrumb'})
    product_family = breadcrumbs.find_all('a')[-3].text.strip()
    product_type = breadcrumbs.find_all('a')[-2].text.strip()
    title = breadcrumbs.find('span', {'class': 'last'}).text.strip()

    # Brand name
    try:
      brand_name = isolate_uppercase(raw_response.find('li', {'class': 'accrocheProduitFicheProduit'}).text.strip())
    except:
      brand_name = None

    # Crossed out price
    crossed_out_price_span = raw_response.find('span', {'class': 'typo-prix-barre'})
    if crossed_out_price_span:
      crossed_out_price = float(crossed_out_price_span.text.strip().replace('\xa0', '').replace('€', '.'))
    else:
      crossed_out_price = None

    # Product specs
    product_specs = raw_response.find('div', {'class': 'detailCaracts'})
    product_specifications = {}

    for index, spec_key in enumerate(specs_headers):
      try:
        header = product_specs.parent.find(lambda item: item.name == 'td' and item.text in specs_headers[spec_key])
        if spec_key in ['width', 'depth', 'height']:
          product_specifications[spec_key] = float(header.find_next_sibling('td').text.strip().replace(' cm', ''))
        else:
          product_specifications[spec_key] = header.find_next_sibling('td').text.strip()
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
      'shade': product_specifications['shade'],
      'material': product_specifications['material'],
      'finish': product_specifications['finish'],
      'country': product_specifications['country']
    }

  def scrape_product_price(self, raw_response):
    try:
      price_div = raw_response.find('div', {'class': 'currentPrice'})
      return float(price_div.text.strip().replace('€', '.'))
    except:
      return None

  def format_product_list_url(self, url):
    return f"{url}/NW-12689-vendu-par~conforama"

  def format_url_with_pagination(self, url, page):
    return f"{url}?p={page}"
