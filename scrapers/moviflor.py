import math
import json
from .scraper import Scraper
from static.moviflor import sections_to_scrape

class MoviflorScraper(Scraper):

  def __init__(self):
    print('Init Moviflor scraper')
    self.marketplace = 'moviflor'
    self.root_url = 'https://www.moviflor.pt'
    self.sitemap_urls = ['/']
    self.with_proxy = False

  def scrape_section_urls(self, raw_response):
    urls = []
    sitemap_div = raw_response.find('div', {'class': 'submenu'})
    for section in sections_to_scrape:
      section_label = sitemap_div.find('a', title=section[0])
      if section_label:
        if section[1]:
          link = section_label.find_next_sibling('ul').find('a', title=section[1])
          if link:
            urls.append(link['href'].replace('https://www.moviflor.pt', '').split('&')[0])
          else:
            print(f"Section {section} not found")
        else:
          urls.append(section_label['href'].replace('https://www.moviflor.pt', '').split('&')[0])
    return urls
  
  def scrape_total_pages(self, raw_response):
    try:
      n_products = int(json.loads(raw_response.text)['response']['products_count'])
      return math.ceil(n_products / 12)
    except:
      return None

  def scrape_new_products(self, raw_response):
    def format_product(product):
      colors = product['available_colors']
      mapped_colors = map(lambda color: color[1]['short_name'], colors.items())

      try:
        crossed_out_price = float(product['previous_price']['value_original'])
      except:
        crossed_out_price = None
      
      try:
        picture_url = f"https://www.moviflor.pt/{product['images'][0]['source']}"
      except:
        picture_url = None

      try:
        dimensions = product['dimension'][0]['size']
        width = float(dimensions.split('x')[0])
        height = float(dimensions.split('x')[1])
        depth = float(dimensions.split('x')[2])
      except:
        width = None
        height = None
        depth = None

      return {
        'reference': product['ean'],
        'product_url': product['url'].replace('https://www.moviflor.pt', ''),
        'product_family': product['family'],
        'product_type': product['sub_family'],
        'title': product['title'],
        'brand_name': None,
        'color': ', '.join(mapped_colors),
        'crossed_out_price': crossed_out_price,
        'picture_url': picture_url,
        'width': width,
        'depth': depth,
        'height': height
      }
    try:
      products = json.loads(raw_response.text)['response']['products']
      return map(lambda product: format_product(product), products)
    except:
      return []

  def scrape_product_info(self, raw_response):
    return {}
    # Breadcrumbs info
    # breadcrumbs = raw_response.find('div', {'class': 'breadcrumb'})
    # product_family = breadcrumbs.find_all('li')[-3].text.strip()
    # product_type = breadcrumbs.find_all('li')[-2].text.strip()
    # title = breadcrumbs.find_all('li')[-1].text.strip()

    # main_info = raw_response.find('div', {'class': 'column-desc'})
    
    # Crossed out price
    # prices = main_info.find('div', {'class': 'price'})
    # crossed_out_price_span = prices.find('span', {'class': 'old'})
    # if crossed_out_price_span:
    #   crossed_out_price = float(crossed_out_price_span.text.strip().replace(',', '.').replace('€', ''))
    # else:
    #   crossed_out_price = None

    # colors_div = main_info.find('div', {'class': 'colors'})
    # colors_list = map(lambda a: a['title'], colors_div.find_all('a'))
    # color = ', '.join(colors_list)

    # try:
    #   specifications_div = raw_response.find('div', {'class': 'container-tabs'})
    #   dimensions_label_p = specifications_div.find('p', text='Dimensões do produto (cm)')
    #   dimensions = dimensions_label_p.find_next_sibling('p').text.strip()
    #   width = float(dimensions.split(' x ')[0].replace('L', ''))
    #   height = float(dimensions.split(' x ')[1].replace('A', ''))
    #   depth = float(dimensions.split(' x ')[2].replace('P', ''))
    # except:
    #   width = None
    #   height = None
    #   depth = None    

    # return {
      # 'product_family': product_family,
      # 'product_type': product_type,
      # 'title': title,
      # 'brand_name': None,
      # 'crossed_out_price': crossed_out_price,
      # 'width': width,
      # 'depth': depth,
      # 'height': height,
      # 'color': color
    # }

  def scrape_product_price(self, raw_response):
    try:
      main_info = raw_response.find('div', {'class': 'column-desc'})
      prices = main_info.find('div', {'class': 'price'})
      price_span = prices.find('span', {'class': 'current'})
      return float(price_span.text.strip().replace(',', '.').replace('€', ''))
    except:
      return None

  def format_product_list_url(self, url):
    return url

  def format_url_with_pagination(self, url, page):
    params = url.split('_')[1].split('.')[0].split('-')
    data_id = params[0]
    data_cat = params[1]
    if page == 1:
      return f"/api/api.php/getProducts/{data_id}/{data_cat}/0/1/1"
    else:
      return f"/api/api.php/getProducts/{data_id}/{data_cat}/{12*(page - 1)}/1/{page}"
