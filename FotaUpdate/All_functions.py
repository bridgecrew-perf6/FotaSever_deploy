import csv
from .Azurefunctions import *
from .models import ScomoID

def Read_csv(csv_data):
    vin_number_list = []
    reader = csv.DictReader(csv_data)
    for row in reader:
        vin_number_list.append(row['VIN NUMBER'])
    return vin_number_list





