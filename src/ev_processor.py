import pandas as pd
import os
import re
import glob
import logging
from datetime import datetime
import matplotlib.pyplot as plt
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class EVProcessor:
    """Streamlined EV data processor following first principles."""
    
    def __init__(self, data_dir='data', report_dir='report'):
        """Initialize with data and report directories."""
        self.data_dir = data_dir
        self.report_dir = report_dir
        
        # Ensure directories exist
        for directory in [data_dir, report_dir, 'plots']:
            os.makedirs(directory, exist_ok=True)
    
    def is_ev(self, line):
        """Determine if a line contains true EV data using reliable patterns."""
        if len(line) < 200:
            return False
        
        # True EV patterns (avoiding hybrids)
        ev_patterns = [
            r'\d+BEV\s+\d+',       # Standard pattern (e.g., "1000BEV 123456")
            r'BEV\s+\d{5,}',        # BEV followed by longer numbers
            r'\d{3,}BEV',           # Multi-digit number followed by BEV
        ]
        
        # Check for definitive EV patterns
        for pattern in ev_patterns:
            if re.search(pattern, line):
                # Make sure it's not a hybrid (which often has just 'BEV' in the COMBUSTIBLE field)
                if not re.search(r'\bBEV\b\s*$', line):
                    return True
        
        # Secondary check for electric indicators + absence of hybrid indicators
        if (('ELECTRIC' in line.upper() or re.search(r'E-[A-Z]+', line)) and 
            'HYBRID' not in line.upper()):
            return True
            
        return False
    
    def extract_vehicle_info(self, line):
        """Extract vehicle information from a registration line using defined positions."""
        if len(line) < 200:
            return {}
        
        try:
            # Field positions (simplified from original)
            fields = {
                'date': (0, 9),
                'make': (9, 39),
                'model': (39, 69),
                'vin': (69, 92),
                'fuel_info': (200, 220)
            }
            
            # Extract basic fields
            record = {
                'date': line[fields['date'][0]:fields['date'][1]].strip(),
                'MARCA': line[fields['make'][0]:fields['make'][1]].strip(),
                'MODELO': line[fields['model'][0]:fields['model'][1]].strip(),
                'VIN': line[fields['vin'][0]:fields['vin'][1]].strip()
            }
            
            # Extract fuel info / BEV pattern
            for pattern in [r'(\d+BEV\s+\d+)', r'(BEV\s+\d{5,})', r'(\d{3,}BEV)']:
                match = re.search(pattern, line)
                if match:
                    record['COMBUSTIBLE'] = match.group(1).strip()
                    break
            else:
                # Fallback for vehicles clearly marked as electric
                if 'ELECTRIC' in line.upper() and 'HYBRID' not in line.upper():
                    record['COMBUSTIBLE'] = 'ELECTRIC'
                elif re.search(r'E-[A-Z]+', line) and 'HYBRID' not in line.upper():
                    record['COMBUSTIBLE'] = 'E-VEHICLE'
            
            # Validate record has essential fields
            if (not record.get('MARCA') or not record.get('MODELO') or 
                'COMBUSTIBLE' not in record or record.get('COMBUSTIBLE') == 'BEV'):
                return {}
                
            return record
        except Exception as e:
            logger.debug(f"Error parsing line: {str(e)}")
            return {}
    
    def process_file(self, file_path):
        """Process a single registration file extracting only true EVs."""
        logger.info(f"Processing {file_path}")
        
        # Extract date from filename
        date_match = re.search(r'export_mat_(\d{8})\.txt', os.path.basename(file_path))
        if not date_match:
            logger.error(f"Invalid filename format: {file_path}")
            return pd.DataFrame()
        
        file_date = datetime.strptime(date_match.group(1), '%Y%m%d')
        records = []
        
        # Single-pass processing: read, filter, parse
        try:
            with open(file_path, 'r', encoding='latin1', errors='replace') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Only process lines that are EVs
                    if self.is_ev(line):
                        record = self.extract_vehicle_info(line)
                        if record:
                            # Add date information
                            record['registration_date'] = file_date
                            record['year'] = file_date.year
                            record['month'] = file_date.month
                            record['day'] = file_date.day
                            records.append(record)
        except Exception as e:
            logger.error(f"Error processing {file_path}: {str(e)}")
            # Try alternate encoding as fallback
            try:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    for line in f:
                        if self.is_ev(line.strip()):
                            record = self.extract_vehicle_info(line.strip())
                            if record:
                                record['registration_date'] = file_date
                                record['year'] = file_date.year
                                record['month'] = file_date.month
                                record['day'] = file_date.day
                                records.append(record)
            except Exception as e2:
                logger.error(f"Processing with UTF-8 also failed: {str(e2)}")
        
        if not records:
            logger.warning(f"No EVs found in {file_path}")
            return pd.DataFrame()
        
        df = pd.DataFrame(records)
        logger.info(f"Found {len(df)} EVs in {file_path}")
        return df
    
    def process_month(self, year, month, force=False):
        """Process all registration files for a specific month."""
        output_file = f"{self.report_dir}/ev_data_{year}_{month:02d}.csv"
        
        # Skip if output exists and not forced
        if os.path.exists(output_file) and not force:
            logger.info(f"Output already exists: {output_file}")
            return output_file
        
        # Get all files for the month
        pattern = f"{self.data_dir}/export_mat_{year}{month:02d}*.txt"
        files = glob.glob(pattern)
        
        if not files:
            logger.warning(f"No files found for {year}-{month:02d}")
            return ""
        
        # Process all files
        all_data = []
        total_evs = 0
        
        for file in files:
            try:
                ev_data = self.process_file(file)
                if not ev_data.empty:
                    all_data.append(ev_data)
                    total_evs += len(ev_data)
            except Exception as e:
                logger.error(f"Error processing {file}: {str(e)}")
        
        if not all_data:
            logger.warning("No data to save")
            return ""
        
        # Combine data and remove duplicates (using VIN)
        combined_data = pd.concat(all_data, ignore_index=True)
        
        # Deduplicate
        if 'VIN' in combined_data.columns:
            combined_data = combined_data.drop_duplicates(subset=['VIN', 'registration_date'])
        else:
            combined_data = combined_data.drop_duplicates(subset=['MARCA', 'MODELO', 'registration_date'])
        
        # Save to report directory
        os.makedirs(self.report_dir, exist_ok=True)
        combined_data.to_csv(output_file, index=False)
        
        # Print summary
        self._print_summary(combined_data, year, month, total_evs)
        return output_file
    
    def _print_summary(self, data, year, month, total_evs):
        """Print summary statistics about the processed data."""
        logger.info(f"\nSummary for {year}-{month:02d}:")
        logger.info(f"Total records: {len(data)}")
        logger.info(f"Total EVs found: {total_evs}")
        logger.info(f"Unique manufacturers: {data['MARCA'].nunique()}")
        logger.info(f"Unique models: {data['MODELO'].nunique()}")
        
        # Top manufacturers
        logger.info("\nTop manufacturers:")
        for manufacturer, count in data['MARCA'].value_counts().head(5).items():
            logger.info(f"- {manufacturer}: {count}")
        
        # Top models
        logger.info("\nTop models:")
        for model, count in (data['MARCA'] + ' ' + data['MODELO']).value_counts().head(5).items():
            logger.info(f"- {model}: {count}")
    
    def visualize(self, year, month):
        """Generate key visualizations for processed data."""
        csv_file = f"{self.report_dir}/ev_data_{year}_{month:02d}.csv"
        
        if not os.path.exists(csv_file):
            logger.error(f"Data file not found: {csv_file}")
            return False
        
        try:
            # Load data
            data = pd.read_csv(csv_file, parse_dates=['registration_date'])
            logger.info(f"Loaded {len(data)} records for visualization")
            
            # Set plot style
            plt.style.use('ggplot')
            
            # Create year/month directory structure for plots
            plots_dir = Path(f"plots/{year}/{month:02d}")
            plots_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Saving visualizations to {plots_dir}")
            
            # 1. Brand distribution pie chart
            self._plot_brand_distribution(data, year, month)
            
            # 2. Top models bar chart
            self._plot_top_models(data, year, month)
            
            # 3. Daily registrations line chart
            self._plot_daily_registrations(data, year, month)
            
            # 4. Brand trends stacked area chart
            self._plot_brand_trends(data, year, month)
            
            logger.info("All visualizations created successfully")
            return True
        except Exception as e:
            logger.error(f"Error generating visualizations: {str(e)}")
            return False
    
    def _plot_brand_distribution(self, data, year, month):
        """Create pie chart of top brands."""
        plt.figure(figsize=(10, 8))
        brand_counts = data['MARCA'].value_counts()
        top_brands = brand_counts.head(10)
        others = pd.Series({'Others': brand_counts[10:].sum()})
        brands_plot = pd.concat([top_brands, others])
        
        plt.pie(brands_plot.values, labels=brands_plot.index, autopct='%1.1f%%')
        plt.title(f'EV Registrations by Brand - {year}/{month:02d}')
        
        # Save to year/month directory
        output_path = f"plots/{year}/{month:02d}/brand_distribution_pie.png"
        plt.savefig(output_path)
        plt.close()
        logger.info(f"Created brand distribution pie chart: {output_path}")
    
    def _plot_top_models(self, data, year, month):
        """Create horizontal bar chart of top models."""
        plt.figure(figsize=(12, 8))
        data['FULL_MODEL'] = data['MARCA'] + ' ' + data['MODELO']
        model_counts = data['FULL_MODEL'].value_counts().head(15).iloc[::-1]
        
        plt.barh(range(len(model_counts)), model_counts.values)
        plt.yticks(range(len(model_counts)), model_counts.index)
        plt.title(f'Top 15 EV Models - {year}/{month:02d}')
        plt.xlabel('Number of Registrations')
        
        # Add value labels
        for i, v in enumerate(model_counts.values):
            plt.text(v, i, f' {v}', va='center')
        
        plt.tight_layout()
        
        # Save to year/month directory
        output_path = f"plots/{year}/{month:02d}/top_models.png"
        plt.savefig(output_path)
        plt.close()
        logger.info(f"Created top models bar chart: {output_path}")
    
    def _plot_daily_registrations(self, data, year, month):
        """Create line chart of daily registrations."""
        plt.figure(figsize=(12, 6))
        daily_counts = data.groupby('registration_date').size()
        daily_counts.index = pd.to_datetime(daily_counts.index)
        daily_counts = daily_counts.sort_index()
        
        plt.plot(daily_counts.index, daily_counts.values, marker='o')
        plt.title(f'Daily EV Registrations - {year}/{month:02d}')
        plt.xlabel('Date')
        plt.ylabel('Number of Registrations')
        plt.xticks(rotation=45)
        plt.grid(True)
        plt.tight_layout()
        
        # Save to year/month directory
        output_path = f"plots/{year}/{month:02d}/daily_registrations.png"
        plt.savefig(output_path)
        plt.close()
        logger.info(f"Created daily registrations line chart: {output_path}")
    
    def _plot_brand_trends(self, data, year, month):
        """Create stacked area chart of top brands over time."""
        plt.figure(figsize=(12, 6))
        top_brands = data['MARCA'].value_counts().head(5).index
        
        # Create pivot table
        brand_daily = pd.pivot_table(
            data[data['MARCA'].isin(top_brands)],
            index='registration_date',
            columns='MARCA',
            aggfunc='size',
            fill_value=0
        )
        
        brand_daily = brand_daily.sort_index()
        brand_daily.plot(kind='area', stacked=True)
        plt.title(f'Daily Registrations by Top Brands - {year}/{month:02d}')
        plt.xlabel('Date')
        plt.ylabel('Number of Registrations')
        plt.legend(title='Brand', bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid(True)
        plt.tight_layout()
        
        # Save to year/month directory
        output_path = f"plots/{year}/{month:02d}/brand_trends.png"
        plt.savefig(output_path, bbox_inches='tight')
        plt.close()
        logger.info(f"Created brand trends stacked area chart: {output_path}")

def main():
    """Main entry point with simplified command-line interface."""
    import argparse
    
    parser = argparse.ArgumentParser(description="EV registration data processor")
    parser.add_argument("--year", type=int, default=2025, help="Year to process")
    parser.add_argument("--month", type=int, default=2, help="Month to process")
    parser.add_argument("--force", action="store_true", help="Force reprocessing")
    parser.add_argument("--visualize", action="store_true", help="Generate visualizations")
    args = parser.parse_args()
    
    # Create processor
    processor = EVProcessor(data_dir='data', report_dir='report')
    
    # Process data
    output_file = processor.process_month(args.year, args.month, args.force)
    
    if not output_file:
        logger.error("Processing failed")
        return 1
    
    logger.info(f"Data saved to {output_file}")
    
    # Generate visualizations if requested
    if args.visualize:
        processor.visualize(args.year, args.month)
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main()) 