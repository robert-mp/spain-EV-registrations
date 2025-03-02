import os
import requests
from datetime import datetime, timedelta
import calendar
import zipfile
import io
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from retry import retry
import pandas as pd
import logging
from typing import List, Tuple, Set

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@retry(tries=3, delay=2, backoff=2)
def download_single_file(url: str, date_str: str, output_dir: str, timeout: int = 30) -> Tuple[str, bool, str]:
    """
    Download a single DGT file with retry mechanism.
    
    Args:
        url (str): URL to download from
        date_str (str): Date string for the file
        output_dir (str): Directory to save the file
        timeout (int): Request timeout in seconds
    
    Returns:
        Tuple[str, bool, str]: (date_str, success status, error message if any)
    """
    txt_filename = f"export_mat_{date_str}.txt"
    local_path = os.path.join(output_dir, txt_filename)
    
    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            z = zipfile.ZipFile(io.BytesIO(response.content))
            z.extract(txt_filename, output_dir)
            return date_str, True, ""
        return date_str, False, f"Status code: {response.status_code}"
    except Exception as e:
        return date_str, False, str(e)

def process_ev_data(file_path: str) -> pd.DataFrame:
    """
    Process a single registration file to extract EV data.
    
    Args:
        file_path (str): Path to the registration file
    
    Returns:
        pd.DataFrame: Processed EV data
    """
    # Read fixed-width file
    df = pd.read_fwf(file_path, encoding='latin1')
    
    # Filter for EVs (using the pattern identified in previous analysis)
    ev_mask = df['COMBUSTIBLE'].str.contains(r'\d+1000BEV\s+\d+', na=False)
    ev_data = df[ev_mask]
    
    return ev_data

def download_dgt_files(year: int, month: int, force_download: bool = False,
                      parallel: bool = True, workers: int = 4,
                      process_data: bool = False, timeout: int = 30) -> Tuple[List[str], List[str], List[str]]:
    """
    Download DGT vehicle registration files with enhanced features.
    
    Args:
        year (int): The year to download files for
        month (int): The month to download files for (1-12)
        force_download (bool): If True, download files even if they already exist locally
        parallel (bool): Whether to use parallel downloads
        workers (int): Number of parallel workers
        process_data (bool): Whether to process downloaded files for EV data
        timeout (int): Download timeout in seconds
    
    Returns:
        Tuple[List[str], List[str], List[str]]: Lists of downloaded, skipped, and failed files
    """
    # Create data directory if it doesn't exist
    data_dir = 'data'
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    # Base URL for DGT files
    base_url = f"https://www.dgt.es/microdatos/salida/{year}/{month}/vehiculos/matriculaciones/export_mat_"
    
    # Get the number of days in the specified month
    _, num_days = calendar.monthrange(year, month)
    
    # Prepare download tasks
    tasks = []
    skipped_files = []
    
    for day in range(1, num_days + 1):
        date_str = f"{year}{month:02d}{day:02d}"
        txt_filename = f"export_mat_{date_str}.txt"
        local_path = os.path.join(data_dir, txt_filename)
        
        if os.path.exists(local_path) and not force_download:
            logger.info(f"Skipping {txt_filename} (already exists)")
            skipped_files.append(txt_filename)
            continue
        
        url = f"{base_url}{date_str}.zip"
        tasks.append((url, date_str))
    
    downloaded_files = []
    failed_files = []
    
    if parallel and tasks:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_url = {
                executor.submit(download_single_file, url, date_str, data_dir, timeout): date_str
                for url, date_str in tasks
            }
            
            with tqdm(total=len(tasks), desc="Downloading files") as pbar:
                for future in as_completed(future_to_url):
                    date_str, success, error = future.result()
                    if success:
                        downloaded_files.append(f"export_mat_{date_str}.txt")
                    else:
                        failed_files.append(f"{date_str} ({error})")
                    pbar.update(1)
    else:
        for url, date_str in tqdm(tasks, desc="Downloading files"):
            date_str, success, error = download_single_file(url, date_str, data_dir, timeout)
            if success:
                downloaded_files.append(f"export_mat_{date_str}.txt")
            else:
                failed_files.append(f"{date_str} ({error})")
    
    if process_data and downloaded_files:
        logger.info("Processing downloaded files for EV data...")
        all_ev_data = []
        for file in downloaded_files:
            file_path = os.path.join(data_dir, file)
            try:
                ev_data = process_ev_data(file_path)
                all_ev_data.append(ev_data)
            except Exception as e:
                logger.error(f"Error processing {file}: {str(e)}")
        
        if all_ev_data:
            combined_ev_data = pd.concat(all_ev_data, ignore_index=True)
            output_file = f"ev_data_{year}_{month:02d}.csv"
            combined_ev_data.to_csv(output_file, index=False)
            logger.info(f"EV data saved to {output_file}")
    
    return downloaded_files, skipped_files, failed_files

def parse_args():
    parser = argparse.ArgumentParser(description='Download DGT vehicle registration files')
    parser.add_argument('--year', type=int, help='Year to download files for (default: current year)',
                      default=datetime.now().year)
    parser.add_argument('--month', type=int, help='Month to download files for (1-12)',
                      default=datetime.now().month)
    parser.add_argument('--months', type=int, nargs='+', help='Multiple months to download (1-12)')
    parser.add_argument('--force', action='store_true', help='Force download even if files exist locally')
    parser.add_argument('--parallel', action='store_true', help='Enable parallel downloads')
    parser.add_argument('--workers', type=int, default=4, help='Number of parallel workers')
    parser.add_argument('--process', action='store_true', help='Process downloaded files for EV data')
    parser.add_argument('--timeout', type=int, default=30, help='Download timeout in seconds')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    
    # Handle multiple months
    months_to_process = args.months if args.months else [args.month]
    
    # Validate months
    invalid_months = [m for m in months_to_process if not 1 <= m <= 12]
    if invalid_months:
        logger.error(f"Invalid months: {invalid_months}")
        exit(1)
    
    total_downloaded = []
    total_skipped = []
    total_failed = []
    
    for month in months_to_process:
        logger.info(f"\nProcessing {calendar.month_name[month]} {args.year}")
        downloaded, skipped, failed = download_dgt_files(
            args.year, month, args.force,
            args.parallel, args.workers,
            args.process, args.timeout
        )
        total_downloaded.extend(downloaded)
        total_skipped.extend(skipped)
        total_failed.extend(failed)
    
    logger.info("\nDownload Summary:")
    logger.info(f"Successfully downloaded: {len(total_downloaded)} files")
    logger.info(f"Skipped (already exist): {len(total_skipped)} files")
    logger.info(f"Failed to download: {len(total_failed)} files")
    
    if total_downloaded:
        logger.info("\nDownloaded files:")
        for file in total_downloaded:
            logger.info(f"- {file}")
    
    if total_skipped:
        logger.info("\nSkipped files:")
        for file in total_skipped:
            logger.info(f"- {file}")
    
    if total_failed:
        logger.info("\nFailed downloads:")
        for error in total_failed:
            logger.info(f"- {error}") 