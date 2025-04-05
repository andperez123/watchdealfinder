"""
Main script for finding watch deals on eBay.
"""
import os
import time
from datetime import datetime
from typing import List, Dict
import pandas as pd
from ebaysdk.finding import Connection as Finding
from ebaysdk.trading import Connection as Trading
from dotenv import load_dotenv
import config
from database import WatchDatabase
from notifications import NotificationManager

# Load environment variables
load_dotenv()

class WatchDealFinder:
    def __init__(self):
        """Initialize the WatchDealFinder with eBay API credentials."""
        self.app_id = os.getenv('EBAY_APP_ID')
        self.cert_id = os.getenv('EBAY_CERT_ID')
        self.dev_id = os.getenv('EBAY_DEV_ID')
        
        if not all([self.app_id, self.cert_id, self.dev_id]):
            raise ValueError("Missing eBay API credentials. Please check your .env file.")
        
        self.finding_api = Finding(
            appid=self.app_id,
            config_file=None
        )
        
        self.db = WatchDatabase(config.DB_PATH)
        self.notifier = NotificationManager()
        
    def build_search_query(self, brand: str) -> str:
        """Build the search query for a specific brand."""
        keywords = " OR ".join(config.KEYWORDS)
        return f"{brand} ({keywords})"

    def search_listings(self, brand: str) -> List[Dict]:
        """Search eBay for listings matching the criteria."""
        try:
            api_request = {
                'keywords': self.build_search_query(brand),
                'itemFilter': [
                    {'name': 'Condition', 'value': 'Used'},
                    {'name': 'ListingType', 'value': 'Auction'},
                    {'name': 'MaxPrice', 'value': str(config.MAX_PRICE)},
                    {'name': 'MinPrice', 'value': str(config.MIN_PRICE)}
                ],
                'sortOrder': 'TimeLeftSort',
                'outputSelector': ['PictureURLLarge'],
                'paginationInput': {
                    'pageNumber': '1',
                    'entriesPerPage': '100'
                }
            }
            
            response = self.finding_api.execute('findItemsAdvanced', api_request)
            
            if response.dict().get('ack') == 'Success':
                return response.dict().get('searchResult', {}).get('item', [])
            return []
            
        except Exception as e:
            print(f"Error searching listings for {brand}: {str(e)}")
            return []

    def filter_listings(self, listings: List[Dict]) -> List[Dict]:
        """Filter listings based on time remaining and other criteria."""
        filtered_listings = []
        current_time = datetime.now()
        
        for listing in listings:
            # Convert time left to hours
            time_left = listing.get('timeLeft', '')
            if not time_left:
                continue
                
            # Parse time left (format: P3DT2H30M)
            days = int(time_left.split('DT')[0].replace('P', ''))
            hours = int(time_left.split('DT')[1].split('H')[0])
            total_hours = (days * 24) + hours
            
            if total_hours <= config.MAX_TIME_REMAINING:
                filtered_listings.append(listing)
                
        return filtered_listings

    def process_listings(self) -> pd.DataFrame:
        """Process all listings and return as DataFrame."""
        all_listings = []
        
        for brand in config.BRANDS:
            print(f"Searching for {brand}...")
            listings = self.search_listings(brand)
            filtered_listings = self.filter_listings(listings)
            
            for listing in filtered_listings:
                listing_data = {
                    'title': listing.get('title', ''),
                    'brand': brand,
                    'price': float(listing.get('sellingStatus', {}).get('currentPrice', {}).get('value', 0)),
                    'time_left': listing.get('timeLeft', ''),
                    'url': listing.get('viewItemURL', ''),
                    'image_url': listing.get('pictureURLLarge', ''),
                    'item_id': listing.get('itemId', ''),
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                # Store in database
                self.db.update_listing(listing_data)
                all_listings.append(listing_data)
            
            # Rate limiting
            time.sleep(1)
        
        return pd.DataFrame(all_listings)

    def check_for_deals(self):
        """Check for potential deals based on price history and activity."""
        deals_df = self.db.get_potential_deals()
        
        for _, deal in deals_df.iterrows():
            if deal['price_drop_percent'] >= config.MIN_PRICE_DROP_PERCENT:
                self.notifier.notify_deal(deal)
        
        return deals_df

    def save_listings(self, df: pd.DataFrame):
        """Save listings to CSV file."""
        if config.SAVE_TO_CSV:
            df.to_csv(config.CSV_FILENAME, index=False)
            print(f"Saved {len(df)} listings to {config.CSV_FILENAME}")

def main():
    """Main function to run the watch deal finder."""
    try:
        finder = WatchDealFinder()
        print("Starting watch deal finder...")
        
        df = finder.process_listings()
        
        if not df.empty:
            print(f"\nFound {len(df)} listings!")
            
            # Check for deals
            deals_df = finder.check_for_deals()
            if not deals_df.empty:
                print("\nPotential Deals Found:")
                print(deals_df.to_string())
            
            finder.save_listings(df)
        else:
            print("No listings found matching the criteria.")
            
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main() 