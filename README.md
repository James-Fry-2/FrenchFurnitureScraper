# Furniture Marketplace Scraper Documentation

## Overview

This repository contains a Flask application for scraping product information from various furniture marketplaces and e-commerce websites. The application systematically crawls through marketplace sections, collects product details, and stores them in a MongoDB database. It also includes functionality to export the collected data to Excel spreadsheets.

## Architecture

The application follows a modular structure:

- **Scrapers**: Individual scraper classes for each marketplace
- **Static Configuration**: Marketplace-specific settings like section names and product specification headers
- **Utils**: Helper functions for database connection, image storage, and other utilities
- **Exporter**: Data export capabilities

## Key Components

### Scraper Base Class

The `Scraper` class in `scrapers/scraper.py` provides the foundation for all marketplace-specific scrapers. It implements common functionality:

- Adding and validating section URLs
- Collecting product listings
- Updating product information
- Handling proxy connections
- Image storage in Google Cloud

### Marketplace Scrapers

Each marketplace has a dedicated scraper class (e.g., `CastoramaScraper`, `IkeaScraper`) that inherits from the base `Scraper` class and implements marketplace-specific methods:

- `scrape_section_urls`: Extracts section URLs from the marketplace sitemap
- `scrape_total_pages`: Determines the total number of pages to scrape
- `scrape_new_products`: Extracts product information from listing pages
- `scrape_product_info`: Extracts detailed product information from product pages
- `scrape_product_price`: Extracts product pricing information
- `format_product_list_url`: Formats URLs for product listing pages
- `format_url_with_pagination`: Formats URLs for pagination

### Static Configuration

Each marketplace has a corresponding static configuration file that defines:

- `sections_to_scrape`: List of section names to target
- `specs_headers`: Mapping of standardized specification fields to marketplace-specific labels

### Database Integration

The application uses MongoDB to store:

- Section URLs with their validation status and scraping history
- Products with detailed specifications and price history

### Export Functionality

The `Exporter` class in `exporter/exporter.py` generates Excel reports with:

- Product details (dimensions, materials, colors, etc.)
- Price history (current and historical prices)
- Product images
- Hyperlinks to product pages

## Usage

### Environment Setup

```
source venv/bin/activate
export FLASK_ENV=production  # or development
export FLASK_APP=main.py
export DB_CONNECTION_STRING=your_mongodb_connection_string
```

### Scraping Process

The typical scraping workflow consists of these sequential steps:

1. **Add section URLs**: `http://127.0.0.1:5000/add_new_section_urls/[marketplace]`
   - Collects section URLs from the marketplace sitemap

2. **Validate section URLs**: `http://127.0.0.1:5000/check_section_urls/[marketplace]`
   - Validates that section URLs are accessible and contain products

3. **Add new products**: `http://127.0.0.1:5000/add_new_products/[marketplace]`
   - Collects product listings from section pages

4. **Update product details**: `http://127.0.0.1:5000/update_products/[marketplace]`
   - Collects detailed product information from product pages

5. **Export data**: `http://127.0.0.1:5000/export_data/[marketplace]`
   - Exports collected data to an Excel spreadsheet

### Supported Marketplaces

The application supports scraping from these marketplaces:

- Brico Dépôt
- Brico Marché
- But
- Castorama
- Conforama (France)
- Conforama (Spain)
- Ikea
- Kitea
- Leen Bakker
- Leroy Merlin
- Moviflor

## Technical Details

### Dependencies

Key dependencies include:

- Flask: Web application framework
- BeautifulSoup4: HTML parsing
- Requests: HTTP requests
- PyMongo: MongoDB integration
- XlsxWriter: Excel file generation
- Pillow: Image processing
- Google Cloud Storage: Cloud storage for product images

### Data Model

The application uses two main MongoDB collections:

1. **section_urls**:
   - `marketplace`: Marketplace identifier
   - `link`: Section URL
   - `is_valid`: Validation status
   - `last_scraped_at`: Last scraping timestamp
   - `error`: Error information
   - `products_count`: Number of products in the section

2. **products**:
   - `reference`: Product reference/ID
   - `marketplace`: Marketplace identifier
   - `product_url`: URL to product page
   - `product_family`: Product category
   - `product_type`: Product type
   - `title`: Product title
   - `brand_name`: Brand name
   - `width`, `depth`, `height`: Product dimensions
   - `color`, `shade`, `material`, `finish`: Product characteristics
   - `country`: Country of manufacture
   - `picture_url`: URL to product image
   - `picture_bucket_path`: Path to stored image
   - `price_ts`: Price history with timestamps
   - `last_scraped_at`: Last update timestamp

## Notes

- The application uses proxy services for sites that may block scrapers
- Images are stored in Google Cloud Storage for reliability
- Price history is maintained for trend analysis
- The code includes protection for rate limiting through random delays
