import logging
import argparse
import sys
import os
from pathlib import Path
from process_ev import process_month_data, clean_project_structure

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Process EV registration data')
    parser.add_argument('--year', type=int, default=2025, help='Year to process')
    parser.add_argument('--month', type=int, default=2, help='Month to process')
    parser.add_argument('--data-dir', default='data', help='Directory containing data files')
    parser.add_argument('--force', action='store_true', help='Force reprocessing even if output exists')
    parser.add_argument('--visualize', action='store_true', help='Generate visualizations')
    return parser.parse_args()

def main():
    """Main entry point for the EV registration data processing and visualization."""
    args = parse_args()
    
    # Validate args
    if args.month < 1 or args.month > 12:
        logger.error(f"Invalid month: {args.month}. Month must be between 1 and 12.")
        sys.exit(1)
    
    # Make sure data directory exists
    if not os.path.isdir(args.data_dir):
        logger.error(f"Data directory not found: {args.data_dir}")
        sys.exit(1)
    
    # Clean project structure
    clean_project_structure()
    
    # Process data
    logger.info(f"Processing EV registration data for {args.year}-{args.month:02d}")
    output_file = process_month_data(args.year, args.month, args.data_dir, args.force)
    
    if not output_file or not os.path.exists(output_file):
        logger.error("Data processing failed")
        sys.exit(1)
    
    logger.info(f"Successfully processed data to {output_file}")
    
    # Generate visualizations if requested
    if args.visualize:
        try:
            logger.info("Generating visualizations...")
            from visualize_ev import load_ev_data, plot_brand_distribution, plot_daily_registrations, plot_top_models, plot_top_brands, plot_brand_trends
            
            # Load the data
            data = load_ev_data(args.year, args.month)
            
            # Create output directory
            Path('plots').mkdir(exist_ok=True)
            
            # Generate all plots
            plot_brand_distribution(data)
            plot_daily_registrations(data)
            plot_top_models(data)
            plot_top_brands(data)
            plot_brand_trends(data)
            
            logger.info("Visualizations generated successfully")
        except Exception as e:
            logger.error(f"Error generating visualizations: {str(e)}")
            sys.exit(1)
    
    logger.info("EV registration data processing completed successfully")

if __name__ == "__main__":
    main()