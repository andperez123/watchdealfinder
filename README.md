# Watch Deal Finder

A Python tool to find undervalued watch deals on eBay, focusing on Seiko and Omega watches.

## Features

- Scrapes eBay for watch listings matching specified criteria
- Filters for auctions under $300 with less than 24 hours remaining
- Focuses on Seiko and Omega watches
- Calculates potential profit margins based on sold listings

## Setup

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your eBay API credentials:
   ```
   EBAY_APP_ID=your_app_id
   EBAY_CERT_ID=your_cert_id
   EBAY_DEV_ID=your_dev_id
   ```

## Usage

Run the main script:
```bash
python watch_finder.py
```

## Configuration

Edit `config.py` to modify:
- Target brands
- Price thresholds
- Time remaining filters
- Other search criteria 