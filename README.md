# DGT Vehicle Registration Data Processor

This project automates the download and processing of vehicle registration data from Spain's Dirección General de Tráfico (DGT). It includes tools for downloading daily registration files and analyzing electric vehicle (EV) registrations.

## Features

- Automated download of DGT vehicle registration files
- Parallel downloading for improved performance
- Automatic processing of downloaded files for EV analysis
- Support for downloading multiple months at once
- Error retry mechanism for failed downloads
- Detailed download summaries and statistics

## Requirements

- Python 3.6+
- Required packages are listed in `requirements.txt`

## Installation

1. Clone this repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

Download current month's registration files:
```bash
python src/download_dgt.py
```

### Advanced Options

Download files for a specific year and month:
```bash
python src/download_dgt.py --year 2025 --month 2
```

Force re-download of existing files:
```bash
python src/download_dgt.py --year 2025 --month 2 --force
```

Download multiple months:
```bash
python src/download_dgt.py --year 2025 --months 1 2 3
```

### Additional Parameters

- `--parallel`: Enable parallel downloads (default: 4 workers)
- `--workers N`: Set number of parallel workers
- `--retry N`: Number of retry attempts for failed downloads
- `--process`: Automatically process downloaded files for EV analysis
- `--timeout N`: Set download timeout in seconds

## Data Processing

The project includes functionality to:
1. Download registration data files
2. Extract and process vehicle information
3. Identify electric vehicles (EVs)
4. Generate statistics and reports

## File Structure

```
.
├── data/                  # Downloaded registration files
├── src/
│   ├── download_dgt.py   # Download script
│   └── process_ev.py     # EV data processing script
└── requirements.txt      # Project dependencies
```

## Output

The script generates:
- Daily registration files in the `data/` directory
- Download summary reports
- EV registration statistics (when processing is enabled)

## Error Handling

- Automatically retries failed downloads
- Skips existing files unless forced to re-download
- Handles network timeouts and connection errors
- Provides detailed error reporting

## License

This project is open source and available under the MIT License. 