import requests

def isolate_uppercase(string=''):
  string_items = string.split(' ')
  string_items = sorted(string_items, key=len, reverse=True)
  uppercase_items = list(filter(lambda x: x.isupper(), string_items))
  try:
    return uppercase_items[0]
  except:
    return None

def check_image_url(url):
  response = requests.head(url)
  return response.status_code == 200