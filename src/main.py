import re
from collections import defaultdict
import csv

# Path to the data file (update this to your actual file location)
file_path = 'data/export_mat_20250228.txt'

# Dictionary to store counts of EVs by make and model
ev_counts = defaultdict(int)

# Open and process the file with ISO-8859-1 encoding
with open(file_path, 'r', encoding='ISO-8859-1') as file:
    for line in file:
        # Skip empty lines or header lines
        if not line.strip() or 'Vehículos matriculados' in line:
            continue
        
        # Check if the line starts with an 8-digit date (e.g., '28022025')
        if len(line) >= 8 and line[0:8].isdigit():
            # Extract make and model using fixed positions
            make = line[8:38].strip()  # Positions 8 to 38 for make
            model = line[38:68].strip()  # Positions 38 to 68 for model
            
            # Check if 'BEV' is in the line to identify electric vehicles
            if 'BEV' in line:
                # Remove leading '0' or '6' followed by a space from make, if present
                make = re.sub(r'^[06]\s+', '', make)
                # Increment the count for this make-model pair
                ev_counts[(make, model)] += 1

# Sort the results alphabetically by make and model
sorted_ev_counts = sorted(ev_counts.items())

# Print the table header with aligned columns
print("\nElectric Vehicle Registrations:")
print("-" * 50)
print(f"{'Make':<20} {'Model':<20} {'Count':<5}")
print("-" * 50)

# Print each row of the table with aligned columns
for (make, model), count in sorted_ev_counts:
    print(f"{make:<20} {model:<20} {count:<5}")

# Save the results to a CSV file
with open('ev_sales_by_model.csv', 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['Make', 'Model', 'Count'])  # Write header
    for (make, model), count in sorted_ev_counts:
        writer.writerow([make, model, count])  # Write data rows

# Print summary statistics
total_evs = sum(ev_counts.values())
print("\nSummary:")
print(f"Total EV registrations: {total_evs}")
print(f"Unique make-model combinations: {len(ev_counts)}")