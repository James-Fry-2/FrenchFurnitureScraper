This Flask application allows scraping of production information for a list of ecommerce websites & marketplaces.

In order to update the data :

source venv/bin/activate

export FLASK_ENV=production
export FLASK_APP=main.py
flask run --debug

http://127.0.0.1:5000/add_new_section_urls/[marketplace]
http://127.0.0.1:5000/check_section_urls/[marketplace]
http://127.0.0.1:5000/add_new_products/[marketplace]
http://127.0.0.1:5000/update_products/[marketplace]

Then
http://127.0.0.1:5000/export_data/[marketplace]

Then shut down the database cluster