from .scraper import Scraper
from static.leen_bakker import sections_to_scrape

class LeenBakkerScraper(Scraper):

  def __init__(self):
    print('Init Leen Bakker scraper')
    self.marketplace = 'leen_bakker'
    self.root_url = 'https://www.leenbakker.be'
    self.sitemap_urls = ['/']
    self.with_proxy = False

  def scrape_section_urls(self, raw_response):
    urls = []
    sitemap_div = raw_response.find('div', {'class': 'css-rmj6h2'})
    for section in sections_to_scrape:
      link = sitemap_div.find('a', text=section)
      if link:
        urls.append(link['href'].split('?')[0])
      else:
        print(f"Section {section} not found")
    return urls
  
  def scrape_total_pages(self, raw_response):
    pagination_div = raw_response.find('div', {'data-layer-meta': '%7B%22component%22%3A%22paging%22%7D'})
    if pagination_div:
      return int(pagination_div.find('div').text.split(' sur ')[1])
    else:
      return 1

  def scrape_new_products(self, raw_response):
    def format_product(product):
      picture_url = product.find('img')['src']
      reference = picture_url.split('/')[-1].split('.')[0]
      return {
        'reference': reference,
        'product_url': product.find('a', {'class': 'chakra-linkbox__overlay'})['href'],
        'picture_url': product.find('img')['src']
      }
    products = raw_response.find_all('div', {'class': 'css-1x9tuir'})
    return map(lambda product: format_product(product), products)

  def scrape_product_info(self, raw_response):
    # Breadcrumbs info
    breadcrumbs = raw_response.find('nav', {'data-layer-meta': '%7B%22component%22%3A%22breadcrumb%22%7D'})
    product_family = breadcrumbs.find_all('li')[-2].text.strip()
    product_type = breadcrumbs.find_all('li')[-1].text.strip()
    
    title = raw_response.find('h1', {'class': 'chakra-text'}).text.strip()

    # Crossed out price
    crossed_out_price_span = raw_response.find('span', {'class': 'css-wrkc26'})
    if crossed_out_price_span:
      crossed_out_price = float(crossed_out_price_span.text.strip().replace(',', '.'))
    else:
      crossed_out_price = None

    # Product specs
    product_specs = raw_response.find('div', {'data-layer-meta': '%7B%22title%22%3A%22Sp%C3%A9cifications%22%7D'})

    try:
      dimensions_label = product_specs.find('p', text='Dimensions article (cm)')
      dimensions = dimensions_label.find_next_sibling('span').text.strip().split('x')
      width = float(dimensions[1].strip().replace(' cm', '').replace(',', '.'))
      depth = float(dimensions[2].strip().replace(' cm', '').replace(',', '.'))
      height = float(dimensions[0].strip().replace(' cm', '').replace(',', '.'))
    except:
      width = None
      depth = None
      height = None

    color_label = product_specs.find('p', text='Couleur')
    if color_label:
      color = color_label.find_next_sibling('span').text.strip()
    else:
      color = None
    
    material_label = product_specs.find('p', text='Matériel')
    if material_label:
      material = material_label.find_next_sibling('span').text.strip()
    else:
      material = None

    return {
      'product_family': product_family,
      'product_type': product_type,
      'title': title,
      'brand_name': None,
      'crossed_out_price': crossed_out_price,
      'width': width,
      'depth': depth,
      'height': height,
      'color': color,
      'material': material
    }

  def scrape_product_price(self, raw_response):
    try:
      price_span = raw_response.find('span', {'class': 'css-cssveg'})
      return float(price_span.text.strip().replace(',', '.'))
    except:
      return None

  def format_product_list_url(self, url):
    return url

  def format_url_with_pagination(self, url, page):
    return f"{url}?page={page}&facets=6164735f6631303032305f6e746b5f63733a224f756922-6164735f6631303032305f6e746b5f63733a224e6f6e22&items=96"