# EV Registrations Analysis

This project processes and analyzes electric vehicle (EV) registration data from government registration files, extracting information about brands, models, and registration dates. It then generates visualizations to explore trends in the data.

## Project Structure

```
EV_Registrations/
├── data/                  # Raw registration data files
│   └── export_mat_*.txt   # Raw fixed-width data files by date
├── plots/                 # Generated visualization output
├── output/                # Additional output files
├── src/                   # Source code
│   ├── main.py            # Main entry point
│   ├── process_ev.py      # Data processing script
│   ├── visualize_ev.py    # Visualization script
│   └── ...                # Other utility scripts
├── ev_data_YYYY_MM.csv    # Processed data files (generated)
└── requirements.txt       # Python dependencies
```

## Installation

1. Ensure you have Python 3.8+ installed
2. Install dependencies: `pip install -r requirements.txt`

## Usage

### Processing Data

To process the registration data for a specific month:

```bash
python src/main.py --year 2025 --month 2 --data-dir data
```

Options:
- `--year`: Year to process (default: 2025)
- `--month`: Month to process (default: 2)
- `--data-dir`: Directory containing the raw data files (default: data)
- `--force`: Force reprocessing even if output file exists
- `--visualize`: Generate visualizations after processing

### Generating Visualizations

To generate visualizations from processed data:

```bash
python src/visualize_ev.py
```

This will create the following visualizations in the `plots/` directory:
1. `brand_distribution_pie.png` - Pie chart showing market share by brand
2. `daily_registrations.png` - Line chart of daily EV registrations
3. `top_models.png` - Bar chart of top 15 EV models
4. `top_brands.png` - Bar chart of top 15 EV brands
5. `brand_trends.png` - Stacked area chart showing brand trends over time

## Data Format

The raw data files (`export_mat_YYYYMMDD.txt`) are fixed-width format files containing vehicle registration information. The script extracts the following fields:

- Make (MARCA): The vehicle manufacturer
- Model (MODELO): The vehicle model
- VIN: Vehicle Identification Number
- Fuel Type (COMBUSTIBLE): Identifies electric vehicles (containing "BEV")
- Registration Date: Date of registration (extracted from filename)

## Data Processing

The data processing performs the following steps:
1. Reads fixed-width files with proper character encoding
2. Identifies electric vehicles based on fuel type patterns
3. Extracts vehicle make, model, and other information
4. Deduplicates entries using VIN or make+model+date combination
5. Saves processed data to CSV files

## Troubleshooting

If you encounter issues with data processing:

1. Check that raw data files exist in the `data/` directory
2. Ensure files follow the expected naming pattern: `export_mat_YYYYMMDD.txt`
3. Check logs for specific error messages
4. Try running with the `--force` flag to regenerate output files

## License

This project is licensed under the MIT License - see the LICENSE file for details. 