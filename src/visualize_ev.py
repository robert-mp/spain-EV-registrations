import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import logging
import os
import sys

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_ev_data(year: int, month: int) -> pd.DataFrame:
    """Load EV data from CSV file."""
    file_path = f"ev_data_{year}_{month:02d}.csv"
    if not Path(file_path).exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")
    
    # Read CSV and parse dates
    try:
        data = pd.read_csv(file_path, parse_dates=['registration_date'])
        
        # Validate required columns
        required_columns = ['MARCA', 'MODELO', 'registration_date']
        for col in required_columns:
            if col not in data.columns:
                raise ValueError(f"Required column '{col}' not found in the data")
        
        logger.info(f"Loaded {len(data)} records from {file_path}")
        return pd.DataFrame(data)
    except Exception as e:
        logger.error(f"Error loading data from {file_path}: {str(e)}")
        raise

def plot_brand_distribution(data: pd.DataFrame, output_dir: str = 'plots'):
    """Create a pie chart of EV registrations by brand."""
    plt.figure(figsize=(12, 8))
    
    # Get top 10 brands, group others
    brand_counts = data['MARCA'].value_counts()
    
    if brand_counts.empty:
        logger.warning("No brand data to visualize")
        return
    
    top_brands = brand_counts.head(10)
    others = pd.Series({'Others': brand_counts[10:].sum()})
    brands_plot = pd.concat([top_brands, others])
    
    # Create pie chart
    plt.pie(brands_plot.values, labels=brands_plot.index, autopct='%1.1f%%')
    plt.title('EV Registrations by Brand')
    
    # Save plot
    Path(output_dir).mkdir(exist_ok=True)
    plt.savefig(f"{output_dir}/brand_distribution_pie.png")
    plt.close()
    
    logger.info(f"Saved brand distribution pie chart to {output_dir}/brand_distribution_pie.png")

def plot_daily_registrations(data: pd.DataFrame, output_dir: str = 'plots'):
    """Create a line plot of daily registrations."""
    plt.figure(figsize=(12, 6))
    
    # Group by date and count
    try:
        daily_counts = data.groupby('registration_date').size()
        daily_counts.index = pd.to_datetime(daily_counts.index)
        daily_counts = daily_counts.sort_index()
        
        # Create line plot
        plt.plot(daily_counts.index, daily_counts.values, marker='o')
        plt.title('Daily EV Registrations')
        plt.xlabel('Date')
        plt.ylabel('Number of Registrations')
        plt.xticks(rotation=45)
        plt.grid(True)
        
        # Adjust layout and save
        plt.tight_layout()
        Path(output_dir).mkdir(exist_ok=True)
        plt.savefig(f"{output_dir}/daily_registrations.png")
        plt.close()
        
        logger.info(f"Saved daily registrations plot to {output_dir}/daily_registrations.png")
    except Exception as e:
        logger.error(f"Error creating daily registrations plot: {str(e)}")

def plot_top_models(data: pd.DataFrame, output_dir: str = 'plots'):
    """Create a horizontal bar chart of top 15 models."""
    try:
        plt.figure(figsize=(12, 8))
        
        # Combine make and model
        data['FULL_MODEL'] = data['MARCA'] + ' ' + data['MODELO']
        model_counts = data['FULL_MODEL'].value_counts().head(15)
        
        # Ensure we have at least one model
        if model_counts.empty:
            logger.warning("No model data to visualize")
            return
        
        # Reverse the order so highest values are at the top
        model_counts = model_counts.iloc[::-1]
        
        # Create horizontal bar chart with sorted data
        plt.barh(range(len(model_counts)), model_counts.values)
        plt.yticks(range(len(model_counts)), model_counts.index)
        plt.title('Top 15 EV Models')
        plt.xlabel('Number of Registrations')
        
        # Add value labels to the end of each bar
        for i, v in enumerate(model_counts.values):
            plt.text(v, i, f' {v}', va='center')
        
        # Adjust layout and save
        plt.tight_layout()
        Path(output_dir).mkdir(exist_ok=True)
        plt.savefig(f"{output_dir}/top_models.png")
        plt.close()
        
        logger.info(f"Saved top models plot to {output_dir}/top_models.png")
    except Exception as e:
        logger.error(f"Error creating top models plot: {str(e)}")

def plot_top_brands(data: pd.DataFrame, output_dir: str = 'plots'):
    """Create a horizontal bar chart of top 15 brands."""
    try:
        plt.figure(figsize=(12, 8))
        
        # Get brand counts
        brand_counts = data['MARCA'].value_counts().head(15)
        
        # Ensure we have at least one brand
        if brand_counts.empty:
            logger.warning("No brand data to visualize")
            return
        
        # Reverse the order so highest values are at the top
        brand_counts = brand_counts.iloc[::-1]
        
        # Create horizontal bar chart with sorted data
        plt.barh(range(len(brand_counts)), brand_counts.values)
        plt.yticks(range(len(brand_counts)), brand_counts.index)
        plt.title('Top 15 EV Brands')
        plt.xlabel('Number of Registrations')
        
        # Add value labels to the end of each bar
        for i, v in enumerate(brand_counts.values):
            plt.text(v, i, f' {v}', va='center')
        
        # Adjust layout and save
        plt.tight_layout()
        Path(output_dir).mkdir(exist_ok=True)
        plt.savefig(f"{output_dir}/top_brands.png")
        plt.close()
        
        logger.info(f"Saved top brands plot to {output_dir}/top_brands.png")
    except Exception as e:
        logger.error(f"Error creating top brands plot: {str(e)}")

def plot_brand_trends(data: pd.DataFrame, output_dir: str = 'plots'):
    """Create a stacked area chart of top brands over time."""
    try:
        plt.figure(figsize=(12, 6))
        
        # Get top 5 brands
        top_brands = data['MARCA'].value_counts().head(5).index
        
        if len(top_brands) == 0:
            logger.warning("No brand data for trends visualization")
            return
        
        # Ensure registration_date is datetime
        data = data.copy()
        data['registration_date'] = pd.to_datetime(data['registration_date'])
        
        # Create pivot table
        brand_daily = pd.pivot_table(
            data[data['MARCA'].isin(top_brands)],
            index='registration_date',
            columns='MARCA',
            aggfunc='size',
            fill_value=0
        )
        
        # Sort by date
        brand_daily = brand_daily.sort_index()
        
        # Create stacked area plot
        brand_daily.plot(kind='area', stacked=True)
        plt.title('Daily Registrations by Top Brands')
        plt.xlabel('Date')
        plt.ylabel('Number of Registrations')
        plt.legend(title='Brand', bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid(True)
        
        # Adjust layout and save
        plt.tight_layout()
        Path(output_dir).mkdir(exist_ok=True)
        plt.savefig(f"{output_dir}/brand_trends.png", bbox_inches='tight')
        plt.close()
        
        logger.info(f"Saved brand trends plot to {output_dir}/brand_trends.png")
    except Exception as e:
        logger.error(f"Error creating brand trends plot: {str(e)}")

def main():
    # Set style - use ggplot as a fallback if seaborn style fails
    try:
        plt.style.use('ggplot')
    except Exception as e:
        logger.warning(f"Could not set ggplot style: {str(e)}. Using default style.")
    
    try:
        # Load February 2025 data
        data = load_ev_data(2025, 2)
        
        if len(data) == 0:
            logger.error("No data available for visualization")
            sys.exit(1)
        
        # Create all plots
        plot_brand_distribution(data)
        plot_daily_registrations(data)
        plot_top_models(data)
        plot_top_brands(data)
        plot_brand_trends(data)
        
        logger.info("All plots generated successfully")
        
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error generating plots: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 