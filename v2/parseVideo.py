import os
import pandas as pd
from datetime import datetime
import av
import time 
import numpy as np
import cv2
import concurrent.futures

BLUR_THRESHOLD = 200

def start_extract_images_and_match_coordinates(input_folder, output_folder, coordinates, shared_parsing_info):
    try :
        extract_images_and_match_coordinates(input_folder, output_folder, coordinates, shared_parsing_info)
    except Exception as e:
        shared_parsing_info['state'] = '-1'
        shared_parsing_info['error'] = str(e)

def save_image(img_array, output_path):
    """Fonction pour enregistrer l'image avec OpenCV."""
    cv2.imwrite(output_path, img_array)

def extract_images_and_match_coordinates(input_folder, output_folder, coordinates, shared_parsing_info):
    shared_parsing_info['state'] = '1'

    output_photos_folder = output_folder
    if not os.path.exists(output_photos_folder):
        os.makedirs(output_photos_folder)

    final_data_csv_path = os.path.join(output_photos_folder, 'final_data.csv')
    pd.DataFrame(columns=['Image file name', 'Exact Time', 'Latitude', 'Longitude', 'Time Diff']).to_csv(final_data_csv_path, index=False)

    df = pd.read_csv(os.path.join(input_folder, 'tps_data.csv'))

    grouped = df.groupby('Video file name')
    for video_name, group in grouped:
        shared_parsing_info['output_string'] = f"Processing video {video_name}"

        frame_time_dict = {row['frame time']: row for _, row in group.iterrows()}

        video_path = os.path.join(input_folder, video_name)

        if not os.path.isfile(video_path) or not video_path.endswith('.mp4'):
            continue

        input_container = av.open(video_path)
        input_stream = input_container.streams.video[0]
        time_base = input_stream.time_base

        output_delay_time = 10
        output_last_time = time.time()
        frame_time_dict_last_value = frame_time_dict[next(reversed(frame_time_dict))]
        shared_parsing_info['Max_frame_time_in_video'] = frame_time_dict_last_value['frame time']

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:

            for packet in input_container.demux(input_stream):
                for frame in packet.decode():
                    start_time_frame = time.time()  # Début du traitement d'une frame

                    tps_time_in_video = float(frame.pts * time_base)

                    nearest_time = find_nearest_time(frame_time_dict, tps_time_in_video, tolerance)
                    if nearest_time is not None:
                        row = frame_time_dict[nearest_time]

                        datetime_str = row['Datetime']
                        try:
                            exact_time = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S.%f')
                        except ValueError:
                            exact_time = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')

                        image_file_name = exact_time.strftime('%Y-%m-%d_%H-%M-%S-%f') + '.png'

                        start_time_img = time.time()  # Début de la création de l'image

                        img_array = frame.to_ndarray(format='bgr24')
                        output_image_path = os.path.join(output_photos_folder, image_file_name)
                        executor.submit(save_image, img_array, output_image_path)

                        end_time_img = time.time()  # Fin de la création de l'image

                        start_time_coords = time.time()  # Début de la recherche des coordonnées
                        closest_coords = find_closest_coordinates_np(exact_time, coordinates)
                        end_time_coords = time.time()  # Fin de la recherche des coordonnées

                        current_data = pd.DataFrame([{
                            'Image file name': image_file_name,
                            'Exact Time': exact_time,
                            'Latitude': closest_coords[0],
                            'Longitude': closest_coords[1],
                            'Time Diff': closest_coords[2]
                        }])

                        current_data.to_csv(final_data_csv_path, mode='a', header=False, index=False)

                        end_time_frame = time.time()

                        if output_last_time + output_delay_time < time.time():
                            shared_parsing_info['actual_frame_time_in_video'] = tps_time_in_video
                            output_last_time = time.time()

                        print(f"Image {image_file_name} saved in {end_time_frame - start_time_frame:.2f}s (Img: {end_time_img - start_time_img:.2f}s, Coords: {end_time_coords - start_time_coords:.2f}s)")
                    else:
                        print(f"Image at time {tps_time_in_video} not saved")
            input_container.close()

    shared_parsing_info['state'] = '2'

def find_closest_coordinates_np(time, coords_array):
    timestamps = coords_array[:, 0]
    target_timestamp = time.timestamp()
    index = np.searchsorted(timestamps, target_timestamp, side="left")
    if index > 0 and (index == len(timestamps) or np.fabs(target_timestamp - timestamps[index-1]) < np.fabs(target_timestamp - timestamps[index])):
        closest_index = index-1
    else:
        closest_index = index
    closest_coords = coords_array[closest_index, 1:]
    time_diff = np.abs(target_timestamp - timestamps[closest_index])
    return *closest_coords, time_diff

def find_nearest_time(time_dict, target_time, tolerance):
    """
    Trouve la clé la plus proche dans le dictionnaire time_dict, 
    en respectant une tolérance donnée.
    """
    nearest_time = None
    min_diff = float('inf')
    for time in time_dict.keys():
        diff = abs(time - target_time)
        if diff <= tolerance and diff < min_diff:
            nearest_time = time
            min_diff = diff

    return nearest_time if nearest_time is not None else None

tolerance = 0.001  # Tolérance de 0.01 secondes

