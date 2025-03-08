from .scraper import Scraper
from static.brico_marche import sections_to_scrape, specs_headers

class BricoMarcheScraper(Scraper):

  def __init__(self):
    print('Init Brico Marche scraper')
    self.marketplace = 'brico_marche'
    self.root_url = 'https://www.bricomarche.com'
    self.sitemap_urls = ['/']
    self.with_proxy = True

  def scrape_section_urls(self, raw_response):
    urls = [
      '/c/rangement-dressing/kit-dressing/kasea-le-systeme-de-rangement-a-case/131235',
      '/c/salle-de-bain/meuble-de-salle-de-bain/armoire-de-toilette/129537',
      '/c/salle-de-bain/meuble-de-salle-de-bain/armoire-salle-de-bain/129538',
      '/c/salle-de-bain/meuble-de-salle-de-bain/colonne-de-salle-de-bain/129539',
      '/c/salle-de-bain/meuble-de-salle-de-bain/meuble-de-rangement/129540',
      '/c/salle-de-bain/meuble-de-salle-de-bain/meuble-vasque/129543',
      '/c/cuisine/meuble-de-cuisine/meuble-de-cuisine-a-composer/129949'
    ]
    # site_nav = raw_response.find('nav', {'class': 'Nav'})
    # for section in sections_to_scrape:
    #   link = site_nav.find('a', text=section)
    #   if link:
    #     urls.append(link['href'])
    #   else:
    #     print(f"Section {section} not found")
    return urls
  
  def scrape_total_pages(self, raw_response):
    print(raw_response)
    pagination_ul = raw_response.find('ul', {'class': 'PaginationList'})
    print(pagination_ul)
    pagination_lis = pagination_ul.find_all('li')
    if len(pagination_lis) == 1:
      return 1
    else:
      last_page_link = pagination_lis[-2]
      return int(last_page_link.text.strip())

  def scrape_new_products(self, raw_response):
    def format_product(product):
      picture_url = product.find('img', {'class': 'ProductTile-thumbImg'})['src']
      product_url = product.find('a', {'class': 'ProductTile-link'})['href']
      return {
        'reference': product['id'],
        'product_url': product_url,
        'picture_url': picture_url
      }
    products = raw_response.find_all('article', {'class': 'ProductListPage-listTile'})
    return map(lambda product: format_product(product), products)

  # def scrape_product_info(self, raw_response):
  #   # Breadcrumbs info
  #   breadcrumbs = raw_response.find('div', {'data-test-id': 'bread-crumbs'})
  #   product_family = breadcrumbs.find_all('a')[-3].text.strip()
  #   product_type = breadcrumbs.find_all('a')[-1].text.strip()
  
  #   title = raw_response.find('h1', {'id': 'product-title'}).text.strip()

  #   # Product specs
  #   product_specs = raw_response.find('div', {'id': 'product-details'})

  #   product_specifications = {}
  #   for index, spec_key in enumerate(specs_headers):
  #     try:
  #       header = product_specs.find(lambda item: item.name == 'th' and item.text in specs_headers[spec_key])
  #       if spec_key in ['width', 'depth', 'height']:
  #         product_specifications[spec_key] = float(header.find_next_sibling('td').text.strip().replace('cm', '').replace('mm', ''))
  #       else:
  #         product_specifications[spec_key] = header.find_next_sibling('td').text.strip()
  #     except:
  #       product_specifications[spec_key] = None

  #   return {
  #     'product_family': product_family,
  #     'product_type': product_type,
  #     'title': title,
  #     'crossed_out_price': None,
  #     'brand_name': product_specifications['brand_name'],
  #     'width': product_specifications['width'],
  #     'depth': product_specifications['depth'],
  #     'height': product_specifications['height'],
  #     'color': product_specifications['color'],
  #     'material': product_specifications['material']
  #   }

  # def scrape_product_price(self, raw_response):
  #   try:
  #     price_div = raw_response.find('div', {'data-test-id': 'product-primary-price'})
  #     return float(price_div.find('div').text.strip())
  #   except:
  #     return None

  def format_product_list_url(self, url):
    return f'{url}?refinementList%5Bbuybox.not_contextualized.seller%5D%5B0%5D=Bricomarché'

  def format_url_with_pagination(self, url, page):
    return url + f"&page={page}"