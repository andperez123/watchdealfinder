"""
Database operations for the watch deal finder.
"""
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import pandas as pd

class WatchDatabase:
    def __init__(self, db_path: str = "watches.db"):
        """Initialize database with the given path."""
        self.db_path = db_path
        self.init_db()

    def _validate_listing_data(self, listing_data: Dict) -> Tuple[bool, str]:
        """Validate required fields in listing data."""
        required_fields = ['item_id', 'title', 'brand', 'price', 'time_left', 'url']
        missing_fields = [field for field in required_fields if field not in listing_data]
        
        if missing_fields:
            return False, f"Missing required fields: {', '.join(missing_fields)}"
            
        if not isinstance(listing_data['price'], (int, float)):
            return False, "Price must be a number"
            
        return True, ""

    def init_db(self):
        """Initialize the database with required tables and indexes."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Create listings table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS listings (
                        item_id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        brand TEXT NOT NULL,
                        current_price REAL NOT NULL,
                        buy_it_now_price REAL,
                        time_left TEXT,
                        url TEXT NOT NULL,
                        image_url TEXT,
                        first_seen TIMESTAMP NOT NULL,
                        last_updated TIMESTAMP NOT NULL
                    )
                """)
                
                # Create price history table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS price_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        item_id TEXT NOT NULL,
                        price REAL NOT NULL,
                        timestamp TIMESTAMP NOT NULL,
                        FOREIGN KEY (item_id) REFERENCES listings (item_id)
                            ON DELETE CASCADE
                    )
                """)
                
                # Create sold items table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS sold_items (
                        item_id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        brand TEXT NOT NULL,
                        final_price REAL NOT NULL,
                        sold_date TIMESTAMP NOT NULL,
                        condition TEXT,
                        original_listing_id TEXT,
                        FOREIGN KEY (original_listing_id) REFERENCES listings (item_id)
                    )
                """)
                
                # Create indexes for better performance
                conn.execute("CREATE INDEX IF NOT EXISTS idx_price_history_item_id ON price_history (item_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_listings_brand ON listings (brand)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_listings_price ON listings (current_price)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_sold_items_brand ON sold_items (brand)")
                
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to initialize database: {str(e)}")

    def update_listing(self, listing_data: Dict):
        """Update or insert a listing with validation."""
        is_valid, error_msg = self._validate_listing_data(listing_data)
        if not is_valid:
            raise ValueError(f"Invalid listing data: {error_msg}")
            
        current_time = datetime.now()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Check if listing exists
                existing = conn.execute(
                    "SELECT current_price FROM listings WHERE item_id = ?",
                    (listing_data['item_id'],)
                ).fetchone()
                
                if existing:
                    # Update existing listing
                    conn.execute("""
                        UPDATE listings 
                        SET current_price = ?, 
                            time_left = ?, 
                            last_updated = ?,
                            buy_it_now_price = COALESCE(?, buy_it_now_price)
                        WHERE item_id = ?
                    """, (
                        listing_data['price'],
                        listing_data['time_left'],
                        current_time,
                        listing_data.get('buy_it_now_price'),
                        listing_data['item_id']
                    ))
                    
                    # If price changed, add to price history
                    if existing[0] != listing_data['price']:
                        conn.execute("""
                            INSERT INTO price_history (item_id, price, timestamp)
                            VALUES (?, ?, ?)
                        """, (listing_data['item_id'], listing_data['price'], current_time))
                else:
                    # Insert new listing
                    conn.execute("""
                        INSERT INTO listings (
                            item_id, title, brand, current_price, buy_it_now_price,
                            time_left, url, image_url, first_seen, last_updated
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        listing_data['item_id'],
                        listing_data['title'],
                        listing_data['brand'],
                        listing_data['price'],
                        listing_data.get('buy_it_now_price'),
                        listing_data['time_left'],
                        listing_data['url'],
                        listing_data.get('image_url'),
                        current_time,
                        current_time
                    ))
                    
                    # Add initial price to history
                    conn.execute("""
                        INSERT INTO price_history (item_id, price, timestamp)
                        VALUES (?, ?, ?)
                    """, (listing_data['item_id'], listing_data['price'], current_time))
                    
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to update listing: {str(e)}")

    def get_price_history(self, item_id: str) -> pd.DataFrame:
        """Get price history for an item."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                return pd.read_sql_query(
                    """
                    SELECT 
                        price,
                        timestamp,
                        price - LAG(price) OVER (ORDER BY timestamp) as price_change
                    FROM price_history 
                    WHERE item_id = ? 
                    ORDER BY timestamp
                    """,
                    conn,
                    params=(item_id,)
                )
        except (sqlite3.Error, pd.io.sql.DatabaseError) as e:
            raise DatabaseError(f"Failed to get price history: {str(e)}")

    def get_potential_deals(self) -> pd.DataFrame:
        """Find listings with significant price drops or unusual activity."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                return pd.read_sql_query("""
                    WITH price_changes AS (
                        SELECT 
                            l.item_id,
                            l.title,
                            l.brand,
                            l.current_price,
                            l.buy_it_now_price,
                            l.url,
                            l.time_left,
                            (
                                SELECT MAX(price) 
                                FROM price_history ph 
                                WHERE ph.item_id = l.item_id
                            ) as max_price,
                            (
                                SELECT COUNT(*) 
                                FROM price_history ph 
                                WHERE ph.item_id = l.item_id
                            ) as price_changes,
                            (
                                SELECT AVG(final_price)
                                FROM sold_items s
                                WHERE s.brand = l.brand
                                AND s.title LIKE '%' || l.title || '%'
                                AND s.sold_date >= date('now', '-30 days')
                            ) as avg_sold_price
                        FROM listings l
                        WHERE l.time_left IS NOT NULL
                    )
                    SELECT 
                        *,
                        ROUND((max_price - current_price) / max_price * 100, 2) as price_drop_percent,
                        CASE 
                            WHEN avg_sold_price IS NOT NULL 
                            THEN ROUND((avg_sold_price - current_price) / current_price * 100, 2)
                            ELSE NULL
                        END as potential_profit_percent
                    FROM price_changes
                    WHERE price_drop_percent > 10 
                        OR price_changes > 5
                        OR (avg_sold_price IS NOT NULL AND current_price < avg_sold_price * 0.8)
                    ORDER BY 
                        COALESCE(potential_profit_percent, 0) DESC,
                        price_drop_percent DESC
                """, conn)
        except (sqlite3.Error, pd.io.sql.DatabaseError) as e:
            raise DatabaseError(f"Failed to get potential deals: {str(e)}")

    def add_sold_item(self, sold_data: Dict):
        """Add a sold item to the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO sold_items (
                        item_id, title, brand, final_price, 
                        sold_date, condition, original_listing_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    sold_data['item_id'],
                    sold_data['title'],
                    sold_data['brand'],
                    sold_data['final_price'],
                    sold_data.get('sold_date', datetime.now()),
                    sold_data.get('condition'),
                    sold_data.get('original_listing_id')
                ))
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to add sold item: {str(e)}")

    def get_brand_statistics(self, brand: str, days: int = 30) -> Dict:
        """Get statistics for a specific brand."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                stats = {}
                
                # Active listings stats
                active_df = pd.read_sql_query("""
                    SELECT 
                        COUNT(*) as count,
                        AVG(current_price) as avg_price,
                        MIN(current_price) as min_price,
                        MAX(current_price) as max_price
                    FROM listings
                    WHERE brand = ? AND time_left IS NOT NULL
                """, conn, params=(brand,))
                
                stats['active_listings'] = active_df.to_dict('records')[0]
                
                # Sold items stats
                sold_df = pd.read_sql_query("""
                    SELECT 
                        COUNT(*) as count,
                        AVG(final_price) as avg_price,
                        MIN(final_price) as min_price,
                        MAX(final_price) as max_price
                    FROM sold_items
                    WHERE brand = ? 
                    AND sold_date >= date('now', ?)
                """, conn, params=(brand, f'-{days} days'))
                
                stats['sold_items'] = sold_df.to_dict('records')[0]
                
                return stats
        except (sqlite3.Error, pd.io.sql.DatabaseError) as e:
            raise DatabaseError(f"Failed to get brand statistics: {str(e)}")

class DatabaseError(Exception):
    """Custom exception for database operations."""
    pass 