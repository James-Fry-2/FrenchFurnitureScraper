import pandas as pd
import numpy as np
import requests
import xlsxwriter
#from googleapiclient.http import MediaIoBaseUpload
from io import BytesIO
from datetime import datetime
from PIL import Image
#from utils.google_cloud_service import GoogleCloudService
from utils.db import scraping_db
#from utils.google_drive_service import GoogleDriveService

MARKETPLACES_DICT = {
  'brico_depot': {
    'display_name': 'Brico Dépôt',
    'root_url': 'https://www.bricodepot.fr'
  },
  'but': {
    'display_name': 'But',
    'root_url': 'https://www.but.fr'
  },
  'castorama': {
    'display_name': 'Castorama',
    'root_url': 'https://www.castorama.fr'
  },
  'conforama_es': {
    'display_name': 'Conforama ES',
    'root_url': 'https://www.conforama.es'
  },
  'conforama': {
    'display_name': 'Conforama',
    'root_url': 'https://www.conforama.fr'
  },
  'ikea': {
    'display_name': 'Ikea',
    'root_url': 'https://www.ikea.com'
  },
  'kitea': {
    'display_name': 'Kitea',
    'root_url': 'https://www.kitea.com'
  },
  'leen_bakker': {
    'display_name': 'Leen Bakker',
    'root_url': 'https://www.leenbakker.be'
  },
  'leroy_merlin': {
    'display_name': 'Leroy Merlin',
    'root_url': 'https://www.leroymerlin.fr'
  },
  'moviflor': {
    'display_name': 'Moviflor',
    'root_url': 'https://www.moviflor.pt'
  },
}

COLUMNS_DICT = {
  'Famille de produit': lambda product: product['product_family'],
  'Type de produit': lambda product: product['product_type'],
  'Nom de gamme': lambda product: product['brand_name'],
  'Libellé': lambda product: product['title'],
  'Photo': lambda product: product['picture_url'],
  'Prix mini constaté': lambda product: get_minimum_price(product),
  'Prix fond de gamme': lambda product: product['crossed_out_price'],
  'Prix actuel': lambda product: get_period_price(product, -1),
  'Larg': lambda product: get_product_width(product),
  'Haut': lambda product: product['height'],
  'Prof': lambda product: get_product_depth(product),
  #'Enseigne': lambda product: MARKETPLACES_DICT[product['marketplace']]['display_name'],
  'Coloris': lambda product: product['color'],
  'Teinte': lambda product: product['shade'],
  'Pays de fabrication': lambda product: product['country'],
  'Matière principale': lambda product: product['material'],
  'Finition': lambda product: product['finish'],
  'Prix m-1': lambda product: get_period_price(product, -2),
  'Prix m-2': lambda product: get_period_price(product, -3),
  'Prix m-3': lambda product: get_period_price(product, -4),
  'Prix m-4': lambda product: get_period_price(product, -5),
  'Prix m-5': lambda product: get_period_price(product, -6),
  'Prix m-6': lambda product: get_period_price(product, -7)
}

def get_minimum_price(product):
  valid_prices = list(filter(lambda item: item['value'], product['price_ts']))
  if len(valid_prices) > 0:
    return min(map(lambda item: item['value'], valid_prices))
  else:
    return None

def get_period_price(product, delta):
  valid_prices = list(filter(lambda item: item['value'], product['price_ts']))
  try:
    return valid_prices[delta]['value']
  except:
    return None

def get_product_depth(product):
  if np.isnan(product['depth']):
    return product['width']
  else:
    return product['depth']

def get_product_width(product):
  if np.isnan(product['width']):
    return product['depth']
  else:
    return product['width']

class Exporter:
  def __init__(self, marketplace):
    self.marketplace = marketplace

  def export_to_gdrive(self):
    print(f"Marketplace {self.marketplace}: Export starting")
    products_to_export = scraping_db.products.find({
      'marketplace': self.marketplace,
      'last_scraped_at': {'$ne': None}
    }).sort('last_scraped_at', -1)#.limit(100)

    df = pd.DataFrame(products_to_export)

    file_name = f"{datetime.now().strftime('%d-%m-%Y')} - Export {MARKETPLACES_DICT[self.marketplace]['display_name']}.xlsx"

    workbook = xlsxwriter.Workbook(file_name)
    worksheet = workbook.add_worksheet()

    header_format = workbook.add_format({
      'bold': True,
      'bg_color': '#DEDEDE',
      'valign': 'vcenter',
      'text_wrap': True,
      'border': 1,
      'border_color': '#303030'
    })
    default_format = workbook.add_format({
      'align': 'center',
      'valign': 'vcenter',
      'text_wrap': True,
      'border': 1,
      'border_color': '#303030'
    })
    currency_format = workbook.add_format({
      'valign': 'vcenter',
      'text_wrap': True,
      'num_format': '#,##0.00"DH"' if self.marketplace == 'kitea' else '#,##0.00€',
      'border': 1,
      'border_color': '#303030'
    })

    max_picture_width = 0

    # Write column headers
    for col_idx, col in enumerate(COLUMNS_DICT):
      worksheet.write(0, col_idx, col, header_format)

    # Write data rows
    for product_idx, product in df.iterrows():
      for col_idx, col in enumerate(COLUMNS_DICT):
        cell_value = COLUMNS_DICT[col](df.iloc[product_idx])

        if 'Prix' in col:
          try:
            worksheet.write(product_idx + 1, col_idx, cell_value, currency_format)
          except:
            worksheet.write(product_idx + 1, col_idx, None, currency_format)
        elif col != 'Photo':
          try:
            worksheet.write(product_idx + 1, col_idx, cell_value, default_format)
          except:
            worksheet.write(product_idx + 1, col_idx, None, default_format)
        else:
          try:
            if product['picture_bucket_path']:
              pass
              #url = GoogleCloudService().load_picture(product)
            else:
              url = product['picture_url']
            image_bytes = requests.get(url).content
            image_data = BytesIO(image_bytes)
            image = Image.open(image_data)
            width, height = image.size
            scale = 75 / height
            new_height = height * scale
            max_picture_width = max(max_picture_width, width*scale)
            hyperlink = f"{MARKETPLACES_DICT[product['marketplace']]['root_url']}{product['product_url']}"
            worksheet.insert_image(product_idx + 1, col_idx, url, {
              'url': hyperlink,
              'image_data': image_data,
              'object_position': 1,
              'x_offset': 10,
              'y_offset': 10,
              'x_scale': scale,
              'y_scale': scale
            })
            worksheet.write(product_idx + 1, col_idx, None, default_format)
            worksheet.set_row_pixels(product_idx + 1, new_height + 20)
          except Exception as error:
            # worksheet.write(product_idx + 1, col_idx, cell_value, default_format)
            print(f"Can't insert picture : {error}")
    
    worksheet.freeze_panes(1, 5)

    worksheet.set_column_pixels(0, 2, 65)
    worksheet.set_column_pixels(0, 3, 100)
    worksheet.set_column_pixels(4, 4, max_picture_width + 20)
    worksheet.set_column_pixels(5, 7, 70)
    worksheet.set_column_pixels(8, 10, 35)
    worksheet.set_column_pixels(11, 22, 80)

    workbook.close()

    #service = GoogleDriveService().build_service()
    #if service:
    #  body = {'name': file_name, 'parents': ['1ip5OrUYKEcaWoOwNsrdixccUdImrxo2n']}
    #  mime_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    #  media_body = MediaIoBaseUpload(open(file_name, 'rb'), mimetype=mime_type)
    #  service.files().create(body=body, media_body=media_body, fields='id, webViewLink').execute()
