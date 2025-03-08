from google.cloud import storage
from io import BytesIO
from PIL import Image
import os
import requests
import datetime

class GoogleCloudService:
    def __init__(self):
      self.client = storage.Client.from_service_account_json('service_account.json')

    def save_picture(self, marketplace, reference, url): 
      if os.environ.get('FLASK_ENV') == 'development':
        bucket_name = 'demeyere-scraping-dev'
      else:
        bucket_name = 'demeyere-scraping'
      bucket = self.client.bucket(bucket_name)
      response = requests.get(url)
      img_bytes = response.content

      try:
        with Image.open(BytesIO(img_bytes)) as img:
          jpeg_bytes = BytesIO()
          img.convert('RGB').save(jpeg_bytes, format='JPEG')
          jpeg_bytes = jpeg_bytes.getvalue()
        
        blob_name = f"products/{marketplace}/{reference}.jpg"
        blob = bucket.blob(blob_name)
        blob.upload_from_file(BytesIO(jpeg_bytes), content_type='image/jpeg')
        return blob_name
      except:
        return None
    
    def load_picture(self, product):
      if os.environ.get('FLASK_ENV') == 'development':
        bucket_name = 'demeyere-scraping-dev'
      else:
        bucket_name = 'demeyere-scraping'
      bucket = self.client.bucket(bucket_name)
      blob = bucket.blob(product['picture_bucket_path'])
      return blob.generate_signed_url(expiration=datetime.timedelta(minutes=15))