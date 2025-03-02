import re
from collections import defaultdict
import csv

# Specify the path to your data file
file_path = 'data/export_mat_20250228.txt'

# Dictionary to store counts of EVs by make and model
ev_counts = defaultdict(int)

# Open and process the file with ISO-8859-1 encoding
with open(file_path, 'r', encoding='ISO-8859-1') as file:
    for line in file:
        # Skip empty lines or header lines
        if not line.strip() or 'Vehículos matriculados' in line:
            continue
        
        # Check if this is a vehicle data line (they typically start with a date)
        if len(line) >= 9 and line[0:8].isdigit():
            # Extract make and model using fixed positions
            make = line[8:38].strip()
            model = line[38:68].strip()
            
            # Look for the BEV pattern in the drivetrain field
            # The pattern is typically a number followed by '1000BEV' and more digits
            if re.search(r'\d+1000BEV\s+\d+', line):
                # Remove any leading "0" or "6" that might appear in the make field
                make = re.sub(r'^[06]\s+', '', make)
                ev_counts[(make, model)] += 1

# Sort the results alphabetically by make and model
sorted_ev_counts = sorted(ev_counts.items())

# Print the table header
print("\nElectric Vehicle Registrations:")
print("-" * 50)
print(f"{'Make':<30} {'Model':<30} {'Count':<5}")
print("-" * 50)

# Print each row of the table
for (make, model), count in sorted_ev_counts:
    print(f"{make:<30} {model:<30} {count:<5}")

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