import json

try:
    with open('BWW_Menu.json', 'r', encoding='utf-8') as file:
        data = json.load(file)
        # Process your data here
except UnicodeDecodeError:
    print("Error: Unable to decode the file. Please check the file's encoding.")
    
    
import csv

menu_items = []
with open("BWW_Menu.csv", 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        menu_items.append(row)