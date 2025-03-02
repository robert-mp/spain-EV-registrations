#!/usr/bin/env python3
"""
DGT Data Downloader - Downloads vehicle registration data from DGT.
"""

import argparse
import io
import logging
import os
import sys
import zipfile
from datetime import datetime
from pathlib import Path

import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class DGTDownloader:
    """Handles downloading and extracting DGT registration data."""
    
    def __init__(self):
        """Initialize with data directory."""
        self.data_dir = Path('data')
        self.data_dir.mkdir(exist_ok=True)
        
        # Base URLs for DGT data
        self.base_url = "https://www.dgt.es/microdatos/salida"
        self.monthly_pattern = "{base}/{year}/{month}/vehiculos/matriculaciones/export_mensual_mat_{year}{month:02d}.zip"
        self.daily_pattern = "{base}/{year}/{month}/vehiculos/matriculaciones/export_mat_{year}{month:02d}{day:02d}.zip"
    
    def download_file(self, url, is_zip=False):
        """Download a file from URL and return its content."""
        try:
            logging.debug(f"Attempting to download: {url}")
            response = requests.get(url, timeout=30)
            
            # Check if the request was successful
            if response.status_code == 404:
                logging.debug(f"File not found: {url}")
                return None
                
            response.raise_for_status()
            
            if is_zip:
                # Extract text file from zip
                try:
                    with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
                        # Get the first file in the zip
                        first_file = zf.namelist()[0]
                        return zf.read(first_file)
                except zipfile.BadZipFile:
                    logging.error(f"Received response is not a valid ZIP file from {url}")
                    return None
            else:
                return response.content
                
        except requests.exceptions.RequestException as e:
            logging.error(f"Error downloading {url}: {str(e)}")
            return None
    
    def save_data(self, content, filename):
        """Save content to file in data directory."""
        if not content:
            return False
            
        try:
            filepath = self.data_dir / filename
            with open(filepath, 'wb') as f:
                f.write(content)
            logging.info(f"Saved data to {filepath}")
            return True
        except Exception as e:
            logging.error(f"Error saving file {filename}: {str(e)}")
            return False
    
    def get_monthly_data(self, year, month):
        """Download monthly data for specified year and month."""
        url = self.monthly_pattern.format(
            base=self.base_url,
            year=year,
            month=month
        )
        
        logging.info(f"Attempting to download monthly data for {year}-{month:02d}")
        content = self.download_file(url, is_zip=True)
        
        if content:
            filename = f"export_mat_{year}{month:02d}.txt"
            return self.save_data(content, filename)
        return False
    
    def get_daily_data(self, year, month, day):
        """Download daily data for specified date."""
        url = self.daily_pattern.format(
            base=self.base_url,
            year=year,
            month=month,
            day=day
        )
        
        logging.debug(f"Attempting to download daily data for {year}-{month:02d}-{day:02d}")
        content = self.download_file(url, is_zip=True)
        
        if content:
            filename = f"export_mat_{year}{month:02d}{day:02d}.txt"
            success = self.save_data(content, filename)
            if success:
                logging.info(f"Successfully downloaded data for {year}-{month:02d}-{day:02d}")
            return success
        return False
    
    def download_data(self, year, month):
        """Download data for specified year and month.
        First tries to download monthly data, if not available, downloads daily data.
        """
        # Try to get monthly data first
        if self.get_monthly_data(year, month):
            logging.info(f"Successfully downloaded monthly data for {year}-{month:02d}")
            return True
            
        # If monthly data not available, try daily data
        logging.info(f"Monthly data not available for {year}-{month:02d}, trying daily data...")
        
        days_in_month = {
            1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30,
            7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31
        }
        
        # Handle leap years
        if month == 2 and (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)):
            days_in_month[2] = 29
            
        # Try each day in the month
        success_count = 0
        for day in range(1, days_in_month[month] + 1):
            if self.get_daily_data(year, month, day):
                success_count += 1
                
        if success_count > 0:
            logging.info(f"Successfully downloaded {success_count} daily files for {year}-{month:02d}")
            return True
        else:
            logging.error(f"No data available for {year}-{month:02d}")
            return False


def main():
    """Main function to parse arguments and download data."""
    parser = argparse.ArgumentParser(description='Download DGT registration data')
    parser.add_argument('--year', type=int, required=True, help='Year to download data for')
    parser.add_argument('--month', type=int, required=True, help='Month to download data for (1-12)')
    parser.add_argument('--data-dir', type=str, default='data', help='Directory to save data files')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if not 1 <= args.month <= 12:
        logging.error("Month must be between 1 and 12")
        return 1
        
    # Create downloader and get data
    downloader = DGTDownloader()
    success = downloader.download_data(args.year, args.month)
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main()) 