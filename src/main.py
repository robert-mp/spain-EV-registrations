#!/usr/bin/env python
"""
EV Registration Data Processor - Main Entry Point
------------------------------------------------

A streamlined application for processing electric vehicle registration data.
"""
import sys
import logging
from pathlib import Path
from ev_processor import EVProcessor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """
    Main entry point for EV data processing.
    Simplified interface following first principles approach.
    """
    import argparse
    
    # Simple command-line interface with defaults
    parser = argparse.ArgumentParser(description="EV Registration Data Processor")
    parser.add_argument("--year", type=int, default=2025, help="Year to process")
    parser.add_argument("--month", type=int, default=2, help="Month to process")
    parser.add_argument("--data-dir", default="data", help="Directory containing raw data files")
    parser.add_argument("--report-dir", default="report", help="Directory for saving processed data")
    parser.add_argument("--force", action="store_true", help="Force reprocessing existing data")
    parser.add_argument("--visualize", action="store_true", help="Generate visualizations")
    args = parser.parse_args()
    
    # Create directories
    for directory in [args.data_dir, args.report_dir, "plots"]:
        Path(directory).mkdir(exist_ok=True)
    
    logger.info(f"Processing EV registration data for {args.year}-{args.month:02d}")
    
    # Process data
    try:
        # Create processor with specified directories
        processor = EVProcessor(data_dir=args.data_dir, report_dir=args.report_dir)
        
        # Process data for specified year/month
        output_file = processor.process_month(args.year, args.month, args.force)
        
        if not output_file:
            logger.error("Processing failed or no data available")
            return 1
        
        logger.info(f"Successfully saved processed data to {output_file}")
        
        # Generate visualizations if requested
        if args.visualize:
            logger.info("Generating visualizations...")
            success = processor.visualize(args.year, args.month)
            if success:
                logger.info("Visualizations created successfully")
            else:
                logger.warning("Error generating visualizations")
        
        logger.info("Processing completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Error processing data: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())