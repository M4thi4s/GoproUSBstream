import os
import pandas as pd
from datetime import datetime
import numpy as np

def start_extract_images_and_match_coordinates(input_folder, coordinates, shared_parsing_info):
    try:
        extract_images_and_match_coordinates(input_folder, coordinates, shared_parsing_info)
    except Exception as e:
        shared_parsing_info['state'] = '-1'
        shared_parsing_info['error'] = str(e)

def extract_images_and_match_coordinates(input_folder, coordinates, shared_parsing_info):
    shared_parsing_info['state'] = '1'

    final_data_csv_path = os.path.join(input_folder, 'photos_time_and_position.csv')
    pd.DataFrame(columns=['Image file name', 'Exact Time', 'Latitude', 'Longitude', 'Altitude', 'Satellites', 'HDOP', 'True Heading', 'Time Diff']).to_csv(final_data_csv_path, index=False)

    df = pd.read_csv(os.path.join(input_folder, 'tps_data.csv'))

    for _, row in df.iterrows():
        image_file_name = row['Photo file name']
        datetime_str = row['Exact datetime']
        try:
            exact_time = datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M:%S.%f')
        except ValueError:
            exact_time = datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M:%S')

        # Trouver les coordonnées et informations supplémentaires les plus proches
        closest_coords, altitude, satellites, hdop, true_heading, time_diff = find_closest_coordinates_np(exact_time, coordinates)

        # Ajouter les données à final_data_csv
        current_data = pd.DataFrame([{
            'Image file name': image_file_name,
            'Exact Time': exact_time,
            'Latitude': closest_coords[0],
            'Longitude': closest_coords[1],
            'Altitude': altitude,
            'Satellites': satellites,
            'HDOP': hdop,
            'True Heading': true_heading,
            'Time Diff': time_diff
        }])
        current_data.to_csv(final_data_csv_path, mode='a', header=False, index=False)

    shared_parsing_info['state'] = '2'

def find_closest_coordinates_np(time, coords_array):
    timestamps = coords_array[:, 0]
    target_timestamp = time.timestamp()
    index = np.searchsorted(timestamps, target_timestamp, side="left")
    if index > 0 and (index == len(timestamps) or np.fabs(target_timestamp - timestamps[index-1]) < np.fabs(target_timestamp - timestamps[index])):
        closest_index = index-1
    else:
        closest_index = index
    closest_data = coords_array[closest_index, 1:]
    time_diff = np.abs(target_timestamp - timestamps[closest_index])
    return closest_data[0], closest_data[1], closest_data[2], closest_data[3], closest_data[4], closest_data[5], time_diff

# Assurez-vous que le tableau `coordinates` est mis à jour avec les nouvelles colonnes
