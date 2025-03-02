# EV Registration Data Processor

A streamlined application for processing electric vehicle (EV) registration data following Elon Musk's first principles approach.

## First Principles Approach

This project is built around three core principles:

1. **Core Problem Focus**: Accurate identification of true battery electric vehicles (BEVs) in registration data while filtering out hybrids and other non-BEVs.
2. **Pattern Matching**: Using reliable regex patterns to identify BEVs with minimal false positives.
3. **Efficiency**: Single-pass processing of data files with optimized code organization.

## Project Structure

The project is organized as follows:

```
EV_Registrations/
├── data/                 # Raw registration data files
├── report/               # Processed CSV output files
├── plots/                # Visualizations organized by year/month
│   └── YYYY/             # Year directory (e.g., 2025)
│       └── MM/           # Month directory (e.g., 02 for February)
│           ├── brand_distribution_pie.png
│           ├── top_models.png
│           ├── daily_registrations.png
│           └── brand_trends.png
└── src/                  # Source code
    ├── ev_processor.py   # Core processing logic (class-based)
    ├── main.py           # Entry point for the application
    └── migrate_data.py   # Utility to migrate existing CSV files
```

## Key Features

- **Accurate EV Detection**: Reliable identification of battery electric vehicles using specific patterns
- **Hybrid Filtering**: Excludes hybrid vehicles that are often misidentified as EVs
- **Organized Output**: Data saved to report directory and visualizations organized by year/month
- **Comprehensive Visualization**: Multiple chart types to analyze the EV market

## Usage

### Basic Usage

```bash
python src/main.py
```

This will process the default month (February 2025) and generate visualizations.

### Command-line Options

```bash
python src/main.py --year 2025 --month 2 --force --visualize
```

Options:
- `--year`: Year to process (default: 2025)
- `--month`: Month to process (default: 2)
- `--data-dir`: Directory containing raw data files (default: "data")
- `--report-dir`: Directory for saving processed data (default: "report")
- `--force`: Force reprocessing existing data
- `--visualize`: Generate visualizations (saved to plots/YYYY/MM/)

## Visualizations

The application generates the following visualizations:

1. **Brand Distribution Pie Chart**: Market share of EV brands
2. **Top Models Bar Chart**: Most popular EV models
3. **Daily Registrations Line Chart**: Registration trends over time
4. **Brand Trends Stacked Area Chart**: Brand performance over time

## Data Processing

The data processing follows these steps:

1. **Read Registration Files**: Parse fixed-width registration data files
2. **Identify EVs**: Use regex patterns to identify true BEVs and filter out hybrids
3. **Extract Vehicle Info**: Extract make, model, VIN, and other details
4. **Deduplicate**: Remove duplicate entries based on VIN and registration date
5. **Save Data**: Store processed data in CSV format in the report directory
6. **Generate Visualizations**: Create charts and save them to year/month folders

## Requirements

- Python 3.6+
- pandas
- matplotlib
- pathlib

## License

MIT 