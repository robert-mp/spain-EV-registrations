import re

# List to store electric vehicle registrations
ev_registrations = []


import chardet

with open(r'C:\Projects\EV_Registrations\data\export_mat_20250228.txt', 'rb') as file:
    raw_data = file.read()
    result = chardet.detect(raw_data)
    encoding = result['encoding']
    print(f"Detected encoding: {encoding}")


with open(r'C:\Projects\EV_Registrations\data\export_mat_20250228.txt', 'r', encoding='ISO-8859-1') as file:
   for line in file:
        # Skip empty lines or headers
        if not line.strip() or 'Vehículos matriculados' in line:
            continue
        
        # Split the line into fields (assuming tabs; adjust if needed)
        fields = line.strip().split('\t')
        
        # Look for "BEV" in any field
        for field in fields:
            if re.search(r'\d+BEV', field):  # Matches "1361000BEV", etc.
                ev_registrations.append(line.strip())
                break

# Display results
print("Electric Vehicle Registrations on February 28, 2025:")
#for reg in ev_registrations:
#    print(reg)

# Save to a new file (optional)
#with open('ev_registrations.txt', 'w', encoding='ISO-8859-1') as outfile:
#    for reg in ev_registrations:
#        outfile.write(reg + '\n')

print(f"\nTotal electric vehicle registrations: {len(ev_registrations)}")
