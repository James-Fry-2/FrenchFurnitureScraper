from .scraper import Scraper
from static.brico_depot import sections_to_scrape, specs_headers

class BricoDepotScraper(Scraper):

  def __init__(self):
    print('Init Brico Depot scraper')
    self.marketplace = 'brico_depot'
    self.root_url = 'https://www.bricodepot.fr'
    self.sitemap_urls = ['/']
    self.with_proxy = False

  def scrape_section_urls(self, raw_response):
    urls = []
    sitemap_div = raw_response.find('nav', {'class': 'bd-Menu'})
    for section in sections_to_scrape:
      link = sitemap_div.find('span', text=section)
      if link:
        urls.append(link.parent['href'])
      else:
        print(f"Section {section} not found")
    return urls
  
  def scrape_total_pages(self, raw_response):
    pagination_div = raw_response.find('div', {'class': 'bd-Box-paging'})
    if pagination_div:
      last_page_link = pagination_div.find_all('div', {'class': 'bd-Paging-link-box--bordered'})[-1]
      return int(last_page_link.text)
    else:
      return 1

  def scrape_new_products(self, raw_response):
    def format_product(product):
      price_span = product.find('span', {'class': 'bd-Price-current'})
      if price_span and price_span.text.strip() != '':
        visual_div = product.find('div', {'class': 'bd-ProductsListItem-visual'})
        sources = visual_div.find_all('source')
        picture_url = f"{self.root_url}{sources[-1]['data-srcset']}"
        return {
          'reference': str(product.find('div')['data-sku-id']),
          'product_url': product.find('div', {'class': 'bd-ProductsListItem-link'})['data-href'],
          'picture_url': picture_url
        }
      else:
        return None
    products = raw_response.find_all('div', {'class': 'jsbd-Product-item'})
    return filter(lambda product: product, map(lambda product: format_product(product), products))

  def scrape_product_info(self, raw_response):
    # Breadcrumbs info
    breadcrumbs = raw_response.find('ul', {'class': 'bd-Breadcrumbs'})
    try:
      product_family = breadcrumbs.find_all('li', {'itemprop': 'itemListElement'})[-4].text.strip()
    except:
      product_family = None
    
    try:
      product_type = breadcrumbs.find_all('li', {'itemprop': 'itemListElement'})[-2].text.strip()
    except:
      product_type = None

    title = breadcrumbs.find_all('li')[-1].text.strip()

    # Crossed out price
    try:
      crossed_out_price_span = raw_response.find('span', {'class': 'bd-Price-current'})
      crossed_out_price = float(crossed_out_price_span.text.strip().replace('€', '.'))
    except:
      crossed_out_price = None

    # Product specs
    product_specs = raw_response.find('ul', {'class': 'bd-ProductDetails-list'})
    product_specifications = {}

    for index, spec_key in enumerate(specs_headers):
      try:
        header = product_specs.parent.find(lambda item: item.name == 'div' and item.text in specs_headers[spec_key])
        if spec_key in ['width', 'depth', 'height']:
          product_specifications[spec_key] = float(header.find_next_sibling('div').text.strip().replace('cm', '').replace(',', '.'))
        else:
          product_specifications[spec_key] = header.find_next_sibling('div').text.strip()
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
      'color': product_specifications['color']
    }

  def scrape_product_price(self, url):
    response = self.get_url(f"{url}?frz-smartcache-fragment=true&frz-timeout=5000&frz-smartcache-v=2&frz-smartcache-placeholders-number=19")
    price = response.text.split("'prix':")[1].split(',')[0]
    return float(price)

  def format_product_list_url(self, url):
    return url

  def format_url_with_pagination(self, url, page):
    return f"{url}{page}/50/?requestChainToken=17936229825&sort=relevancy&listOnly=true"
