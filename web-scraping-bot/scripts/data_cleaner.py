#!/usr/bin/env python3
"""
Data cleaning and validation utilities
"""
import pandas as pd
import re
import os
from datetime import datetime

class DataCleaner:
    def __init__(self):
        self.price_patterns = [
            r'\$?([0-9,]+\.?[0-9]*)',  # $123.45 or 123.45
            r'([0-9,]+\.?[0-9]*)\s*USD',  # 123.45 USD
            r'Price:\s*\$?([0-9,]+\.?[0-9]*)'  # Price: $123.45
        ]
    
    def clean_price(self, price_text):
        """Extract and clean price from text"""
        if pd.isna(price_text) or price_text in ['N/A', 'Error', '']:
            return None
        
        price_text = str(price_text).strip()
        
        # Try different price patterns
        for pattern in self.price_patterns:
            match = re.search(pattern, price_text)
            if match:
                price_str = match.group(1).replace(',', '')
                try:
                    return float(price_str)
                except ValueError:
                    continue
        
        return None
    
    def clean_availability(self, availability_text):
        """Standardize availability status"""
        if pd.isna(availability_text) or availability_text in ['N/A', 'Error', '']:
            return 'Unknown'
        
        availability_text = str(availability_text).lower().strip()
        
        if any(word in availability_text for word in ['in stock', 'available', 'ready']):
            return 'In Stock'
        elif any(word in availability_text for word in ['out of stock', 'unavailable', 'sold out']):
            return 'Out of Stock'
        elif any(word in availability_text for word in ['limited', 'few left', 'low stock']):
            return 'Limited Stock'
        else:
            return 'Unknown'
    
    def clean_dataset(self, df):
        """Clean entire dataset"""
        cleaned_df = df.copy()
        
        # Clean prices
        cleaned_df['price_cleaned'] = cleaned_df['price'].apply(self.clean_price)
        
        # Clean availability
        cleaned_df['availability_cleaned'] = cleaned_df['availability'].apply(self.clean_availability)
        
        # Add cleaning timestamp
        cleaned_df['cleaned_at'] = datetime.now()
        
        return cleaned_df
    
    def clean_all_data(self, data_dir='data/raw', output_dir='data/processed'):
        """Clean all raw data files"""
        os.makedirs(output_dir, exist_ok=True)
        
        for filename in os.listdir(data_dir):
            if filename.endswith('.csv'):
                print(f"Cleaning {filename}...")
                
                df = pd.read_csv(os.path.join(data_dir, filename))
                cleaned_df = self.clean_dataset(df)
                
                output_filename = f"cleaned_{filename}"
                output_path = os.path.join(output_dir, output_filename)
                cleaned_df.to_csv(output_path, index=False)
                
                print(f"✅ Cleaned data saved to {output_path}")

if __name__ == "__main__":
    cleaner = DataCleaner()
    cleaner.clean_all_data()
