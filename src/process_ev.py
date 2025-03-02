import pandas as pd
import os
from pathlib import Path
import logging
from datetime import datetime
import re
import glob

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Field positions in the fixed-width format (based on data inspection)
# These are approximate and may need adjustment
FIELDS = {
    'date': (0, 9),
    'make': (9, 39),
    'model': (39, 69),
    'vin': (69, 92),
    'fuel_info': (200, 220),  # Approximate position where BEV info appears
}

def is_ev_line(line: str) -> bool:
    """
    Check if a line contains EV-related information.
    Looking for various BEV patterns.
    """
    # The line must be long enough to contain the fields
    if len(line) < 200:
        return False
    
    # Check for specific BEV patterns - these are more reliable
    # than general electric indicators for identifying true EVs
    bev_patterns = [
        r'\d+BEV\s+\d+',          # Standard BEV pattern (e.g., "1000BEV 123456")
        r'BEV\s+\d{5,}',           # BEV followed by a longer number
        r'\d{3,}BEV'               # Multi-digit number followed by BEV
    ]
    
    for pattern in bev_patterns:
        if re.search(pattern, line):
            return True
    
    # Electric vehicle secondary indicators - less reliable
    # Used only if there's a strong signal from multiple indicators
    indicators = [
        'BEV',                    # Battery Electric Vehicle marker
        'ELECTRIC',               # Electric in model name
    ]
    
    # Count how many indicators are present
    indicator_count = sum(1 for ind in indicators if ind in line.upper())
    
    # If multiple indicators or a strong specific indicator like "100% ELECTRIC"
    if indicator_count > 1 or "100% ELECTRIC" in line.upper() or "FULLY ELECTRIC" in line.upper():
        return True
    
    return False

def parse_fixed_width_line(line: str) -> dict:
    """
    Parse a line from the fixed-width format into a dictionary.
    
    Args:
        line (str): A line from the registration file
        
    Returns:
        dict: Extracted fields or empty dict if not a valid entry
    """
    if len(line) < 200:  # Skip short lines
        return {}
    
    try:
        record = {}
        
        # Basic fields
        record['date'] = line[FIELDS['date'][0]:FIELDS['date'][1]].strip()
        record['MARCA'] = line[FIELDS['make'][0]:FIELDS['make'][1]].strip()
        record['MODELO'] = line[FIELDS['model'][0]:FIELDS['model'][1]].strip()
        
        # VIN (for deduplication) - may be partially masked with asterisks
        record['VIN'] = line[FIELDS['vin'][0]:FIELDS['vin'][1]].strip()
        
        # Find fuel type/BEV information
        fuel_section = line[FIELDS['fuel_info'][0]:FIELDS['fuel_info'][1]]
        
        # Look for BEV pattern in the line
        bev_patterns = [
            r'(\d+BEV\s+\d+)',           # Standard pattern like "1000BEV 123456"
            r'(BEV\s+\d{5,})',           # BEV followed by longer numbers
            r'(\d{3,}BEV)',              # Multiple digits followed by BEV
        ]
        
        found_pattern = False
        for pattern in bev_patterns:
            match = re.search(pattern, line)
            if match:
                record['COMBUSTIBLE'] = match.group(1).strip()
                found_pattern = True
                break
        
        # Only assign generic BEV if we're very confident it's a true EV
        # Look for stronger evidence in model name or other fields
        if not found_pattern:
            if 'ELECTRIC' in line.upper() and 'HYBRID' not in line.upper():
                # Look for "ELECTRIC" but exclude "HYBRID" to avoid including hybrids
                # Capture the specific section containing 'ELECTRIC'
                elec_match = re.search(r'([^\s]+\s*ELECTRIC[^\s]*)', line.upper())
                if elec_match:
                    record['COMBUSTIBLE'] = elec_match.group(1)
                else:
                    record['COMBUSTIBLE'] = "ELECTRIC"
            elif re.search(r'E-[A-Z]+', line) and 'HYBRID' not in line.upper():
                # Electric model names often start with E-
                record['COMBUSTIBLE'] = "E-VEHICLE"
            elif 'BEV' in line.upper() and re.search(r'\d{3,}', fuel_section):
                # Only include BEV if there are substantial numbers nearby
                record['COMBUSTIBLE'] = "BEV-PATTERN"
        
        # Validate: must have make, model and be an EV with specific combustible value
        if (not record.get('MARCA') or not record.get('MODELO') or 
            'COMBUSTIBLE' not in record or record['COMBUSTIBLE'] == "BEV"):
            return {}
            
        return record
        
    except Exception as e:
        logger.debug(f"Error parsing line: {str(e)}")
        return {}

def process_registration_file(file_path: str) -> pd.DataFrame:
    """
    Process a single registration file and extract EV data.
    
    Args:
        file_path (str): Path to the registration file
        
    Returns:
        pd.DataFrame: Processed EV data
    """
    logger.info(f"Processing {file_path}")
    
    # Extract date from filename
    date_match = re.search(r'export_mat_(\d{8})\.txt', file_path)
    if not date_match:
        raise ValueError(f"Could not extract date from filename: {file_path}")
    
    date_str = date_match.group(1)
    file_date = datetime.strptime(date_str, '%Y%m%d')
    
    # Store processed EV records
    processed_data = []
    
    # Read the file line by line
    try:
        with open(file_path, 'r', encoding='latin1', errors='replace') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                # Check if this is an EV line
                if is_ev_line(line):
                    record = parse_fixed_width_line(line)
                    if record:
                        processed_data.append(record)
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {str(e)}")
        # Try with different encoding if latin1 fails
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Check if this is an EV line
                    if is_ev_line(line):
                        record = parse_fixed_width_line(line)
                        if record:
                            processed_data.append(record)
        except Exception as e2:
            logger.error(f"Also failed with UTF-8 encoding: {str(e2)}")
    
    if not processed_data:
        logger.warning(f"No EVs found in {file_path}")
        return pd.DataFrame()
    
    # Convert to DataFrame
    ev_data = pd.DataFrame(processed_data)
    
    # Additional filtering to exclude potential hybrids
    # Exclude entries with just 'BEV' as combustible (as identified by user)
    ev_data = ev_data[ev_data['COMBUSTIBLE'] != 'BEV']
    
    # Add date information based on the file name
    ev_data['registration_date'] = file_date
    ev_data['year'] = file_date.year
    ev_data['month'] = file_date.month
    ev_data['day'] = file_date.day
    
    logger.info(f"Found {len(ev_data)} EVs in {file_path}")
    return ev_data

def process_month_data(year: int, month: int, data_dir: str = 'data', force: bool = False) -> str:
    """
    Process all registration files for a specific month.
    
    Args:
        year (int): Year to process
        month (int): Month to process
        data_dir (str): Directory containing the data files
        force (bool): If True, reprocess even if output file exists
    
    Returns:
        str: Path to the output CSV file
    """
    output_file = f"ev_data_{year}_{month:02d}.csv"
    
    # Skip if output file exists and force is False
    if os.path.exists(output_file) and not force:
        logger.info(f"Output file {output_file} already exists. Skipping processing.")
        return output_file
    
    # Get all files for the specified month
    pattern = f"{data_dir}/export_mat_{year}{month:02d}*.txt"
    files = glob.glob(pattern)
    
    if not files:
        logger.warning(f"No files found matching pattern: {pattern}")
        return ""
    
    # Process each file
    all_data = []
    total_evs = 0
    
    for file in files:
        try:
            ev_data = process_registration_file(str(file))
            if not ev_data.empty:
                all_data.append(ev_data)
                total_evs += len(ev_data)
        except Exception as e:
            logger.error(f"Error processing {file}: {str(e)}")
    
    if not all_data:
        logger.warning("No data to save")
        return ""
    
    # Combine all data and remove duplicates
    combined_data = pd.concat(all_data, ignore_index=True)
    
    # More robust deduplication - use VIN where available
    if 'VIN' in combined_data.columns:
        combined_data = combined_data.drop_duplicates(subset=['VIN', 'registration_date'])
    else:
        combined_data = combined_data.drop_duplicates(subset=['MARCA', 'MODELO', 'registration_date'])
    
    # Save to CSV
    combined_data.to_csv(output_file, index=False)
    
    # Print summary
    logger.info(f"\nSummary for {year}-{month:02d}:")
    logger.info(f"Total records: {len(combined_data)}")
    logger.info(f"Total EVs found: {total_evs}")
    logger.info(f"Unique manufacturers: {combined_data['MARCA'].nunique()}")
    logger.info(f"Unique models: {combined_data['MODELO'].nunique()}")
    
    # Show top manufacturers
    top_manufacturers = combined_data['MARCA'].value_counts().head()
    logger.info("\nTop manufacturers:")
    for manufacturer, count in top_manufacturers.items():
        logger.info(f"- {manufacturer}: {count}")
    
    # Show top models
    top_models = (combined_data['MARCA'] + ' ' + combined_data['MODELO']).value_counts().head()
    logger.info("\nTop models:")
    for model, count in top_models.items():
        logger.info(f"- {model}: {count}")
    
    return output_file

def clean_project_structure():
    """Clean up the project structure."""
    # Create necessary directories
    for directory in ['data', 'plots', 'output']:
        os.makedirs(directory, exist_ok=True)
    
    # Remove temporary and old files
    patterns = ['*.tmp', '*.bak', '*.old']
    for pattern in patterns:
        for file in glob.glob(pattern):
            os.remove(file)
    
    logger.info("Project structure cleaned")

def main():
    # Clean up project structure
    clean_project_structure()
    
    # Process February 2025 data with improved parsing
    output_file = process_month_data(2025, 2, force=True)
    
    if output_file and os.path.exists(output_file):
        logger.info(f"Successfully created {output_file}")
    else:
        logger.error("Failed to process data")

if __name__ == "__main__":
    main() 