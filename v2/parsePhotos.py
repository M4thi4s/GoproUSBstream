import os
import pandas as pd
from datetime import datetime
import numpy as np

def convert_to_timestamp(dt_str):
    date_formats = [
        '%Y-%m-%d %H:%M:%S.%f',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%dT%H:%M:%S.%f',
        '%Y-%m-%dT%H:%M:%S'
    ]
    for fmt in date_formats:
        try:
            return datetime.strptime(dt_str, fmt).timestamp()
        except ValueError:
            continue
    raise ValueError(f"Date format not recognized for {dt_str}")

def prepare_coordinates_data(coordinates):
    # Convertir la première colonne (dates) en timestamps
    timestamps = np.array([convert_to_timestamp(dt) for dt in coordinates[:, 0]])
    # Remplacer la première colonne par les timestamps
    coordinates[:, 0] = timestamps
    return coordinates

def find_closest_coordinates_np(timestamp, coords_array):
    timestamps = coords_array[:, 0].astype(float)
    index = np.searchsorted(timestamps, timestamp, side="left")
    closest_index = index - 1 if index > 0 and (index == len(timestamps) or abs(timestamp - timestamps[index-1]) < abs(timestamp - timestamps[index])) else index
    closest_data = coords_array[closest_index, 1:]
    time_diff = abs(timestamp - timestamps[closest_index])
    return closest_data, time_diff

def extract_images_and_match_coordinates(input_folder, coordinates, shared_parsing_info):
    shared_parsing_info['state'] = '1'
    final_data_path = os.path.join(input_folder, 'photos_time_and_position.csv')
    output_cols = ['Image file name', 'Exact Time', 'Latitude', 'Longitude', 'Altitude', 'Satellites', 'HDOP', 'True Heading', 'Time Diff']
    pd.DataFrame(columns=output_cols).to_csv(final_data_path, index=False)

    photo_df = pd.read_csv(os.path.join(input_folder, 'tps_data.csv'))
    photo_df['Exact datetime'] = photo_df['Exact datetime'].apply(convert_to_timestamp)

    for _, photo_row in photo_df.iterrows():
        image_file_name = photo_row['Photo file name']
        photo_timestamp = photo_row['Exact datetime']

        closest_data, time_diff = find_closest_coordinates_np(photo_timestamp, coordinates)
        exact_time_str = datetime.fromtimestamp(photo_timestamp).strftime('%Y-%m-%d %H:%M:%S.%f')

        current_data = {
            'Image file name': image_file_name,
            'Exact Time': exact_time_str,
            'Latitude': closest_data[0],
            'Longitude': closest_data[1],
            'Altitude': closest_data[2],
            'Satellites': closest_data[3],
            'HDOP': closest_data[4],
            'True Heading': closest_data[5],
            'Time Diff': time_diff
        }
        pd.DataFrame([current_data]).to_csv(final_data_path, mode='a', header=False, index=False)

    shared_parsing_info['state'] = '2'

def start_extract_images_and_match_coordinates(input_folder, raw_coordinates, shared_parsing_info):
    try:
        coordinates = prepare_coordinates_data(raw_coordinates)
        extract_images_and_match_coordinates(input_folder, coordinates, shared_parsing_info)
    except Exception as e:
        shared_parsing_info['state'] = '-1'
        shared_parsing_info['error'] = str(e)