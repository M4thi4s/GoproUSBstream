import csv
import random

input_file = 'gps_data.csv'
output_file = 'gps_data_out.csv'

with open(input_file, 'r') as csvfile_in, open(output_file, 'w', newline='') as csvfile_out:
    csv_reader = csv.reader(csvfile_in)
    csv_writer = csv.writer(csvfile_out)

    # Copie de l'en-tête
    header = next(csv_reader)
    csv_writer.writerow(header)

    # Traitement de chaque ligne
    for row in csv_reader:
        timestamp = int(row[0])
        milliseconds = random.randint(0, 999)
        new_timestamp = f"{timestamp}.{milliseconds}"
        row[0] = new_timestamp
        csv_writer.writerow(row)