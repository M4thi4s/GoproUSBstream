import psutil
import socket
import requests
import time
import cv2
import numpy as np
import random
import av
from fractions import Fraction
from pyzbar import pyzbar
import re
import pandas as pd
from datetime import datetime, timedelta
import warnings
import os
from configs import output_gopro_folder

av.logging.set_level(av.logging.ERROR)

# Fonctions
def get_gopro_ip_addresse():
    #gopro_ip_addresses = []
    for interface, addrs in psutil.net_if_addrs().items():
        if interface.startswith('usb'):
            for addr in addrs:
                if addr.family == socket.AF_INET:
                    ip_parts = addr.address.split('.')
                    ip_parts[-1] = '51'
                    return '.'.join(ip_parts)
                    # gopro_ip_addresses.append('.'.join(ip_parts))
    raise Exception("No GoPro found")
    # return gopro_ip_addresses

def send_gopro_request(ip, path, params, timeout=10):
    response = requests.get(f"http://{ip}/gp/{path}", params=params, timeout=timeout)
    if response.status_code != 200 or response.json().get("error") != 0:
        return False
    return True

def start_and_set_gopro_resolutionand_fov(ip, resolution, fov):
    return send_gopro_request(ip, 'gpWebcam/START', {'res': resolution, 'fov': fov})

def stop_gopro(ip):
    print ("Arrêt de la GoPro à l'adresse : ", ip)
    random_sleep_time = random.randint(1, 5)
    time.sleep(random_sleep_time)
    return send_gopro_request(ip, 'gpWebcam/STOP', {})

def stop_all_gopro(gopro_ip_addresses):
    for gopro_ip in gopro_ip_addresses:
        if stop_gopro(gopro_ip):
            time.sleep(3)

def decode_qr_code(image):
    decoded_objects = pyzbar.decode(image)
    for obj in decoded_objects:
        qr_data = obj.data.decode('utf-8')
        if re.match(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z', qr_data):
            qr_time = datetime.strptime(qr_data, '%Y-%m-%dT%H:%M:%S.%fZ')
            return qr_time.timestamp()
    return None

def add_to_spreadsheet(photo_file_name, output_folder, exact_datetime):
    file_path = os.path.join(output_folder, 'tps_data.csv')
    df = pd.DataFrame([[photo_file_name, exact_datetime]], columns=['Photo file name', 'Exact datetime'])
    header = not os.path.exists(file_path)
    df.to_csv(file_path, mode='a', index=False, header=header)
    
def wait_for_initial_qr_code(ip, resolution_id):
    width_resolution, height_resolution = get_resolution_width_and_height(resolution_id)
    fifo_size = int(width_resolution * height_resolution * 1.5 * 3)
    stream_url = f'udp://{ip}:8554?overrun_nonfatal=1&fifo_size={fifo_size}'

    qrCodeDetected = False

    while not qrCodeDetected:
        with av.open(stream_url, options={'analyzeduration': '500000', 'probesize': '500000'}) as input_container:
            found_frame = False
            while not found_frame:
                packet = next(input_container.demux(), None)
                if packet is None:
                    break
                for frame in packet.decode():
                    if isinstance(frame, av.VideoFrame):
                        found_frame = True
                        break
                if found_frame:
                    break

        if not found_frame:
            continue

        qr_code_time = decode_qr_code(np.array(frame.to_image()))
        if qr_code_time:
            print("QR code time: ", frame.pts)
            return qr_code_time, frame.pts

def record_images(ip, output_folder, last_qr_code_time, last_qr_code_tps, video_duration, shared_output_dict):
    stream_url = f'udp://{ip}:8554?overrun_nonfatal=1&fifo_size=50000000'
    input_container = av.open(stream_url, options={'analyzeduration': '10000000', 'probesize': '10000000'})
    input_stream = input_container.streams.video[0]
    time_base = input_stream.time_base

    # S'assurer que le dossier de sortie existe
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    first_pts = None
    frame_count = 0
    
    shared_output_dict["number_of_picture"] = 0
    shared_output_dict["buffer_late"] = 0
    output_refresh_delay = 30  # secondes
    output_refresh_last_time = datetime.now().timestamp()

    for packet in input_container.demux(input_stream):
        if packet.stream.type != 'video':
            continue

        for frame in packet.decode():
            if first_pts is None:
                first_pts = frame.pts
                start_time = datetime.now().timestamp()

            tps_time_in_video = (frame.pts - first_pts) * time_base
            
            # Vérifier si la durée spécifiée est dépassée
            if tps_time_in_video > video_duration:
                input_container.close()
                return

            if frame_count % 6 == 0:  # Ne traiter qu'une image sur deux
                photo_file_name = f"Image_{frame_count//2:04d}_{frame.pts}.jpg"
                photo_file_path = os.path.join(output_folder, photo_file_name)

                # Calculer l'heure exacte de la photo en utilisant le temps du dernier QR code détecté
                exact_datetime = datetime.fromtimestamp(last_qr_code_time + (frame.pts - last_qr_code_tps) * float(time_base))

                # Sauvegarder l'image
                frame.to_image().save(photo_file_path)

                # Ajouter l'information au CSV
                add_to_spreadsheet(photo_file_name, output_folder, exact_datetime.isoformat())

                # Mise à jour du shared_output_dict
                current_time = datetime.now().timestamp()
                if current_time - output_refresh_last_time > output_refresh_delay:
                    shared_output_dict["number_of_picture"] = frame_count // 2
                    shared_output_dict["buffer_late"] = ((current_time - start_time) - tps_time_in_video)
                    output_refresh_last_time = current_time  # Réinitialiser le timer pour le prochain rafraîchissement

            frame_count += 1

    input_container.close()
    shared_output_dict["total_images_captured"] = frame_count // 2


def start_and_set_fov(resolution, fov):
    gopro_ip_addresse = get_gopro_ip_addresse()
    if start_and_set_gopro_resolutionand_fov(gopro_ip_addresse, resolution, fov):
        time.sleep(5) 
    return gopro_ip_addresse

# Set width and height using the table above and with the resolution_id
def get_resolution_width_and_height(resolution_id):
    resolutions = {
        4: (640, 480),
        7: (1280, 720),
        12: (1920, 1080)
    }
    if resolution_id in resolutions:
        return resolutions[resolution_id]
    else :
        raise Exception("Invalid resolution ID")

def startRecord(outputFolder, shared_output_dict, resolution_id, number_of_videos, video_duration, fov_id = 0):
    try:
        shared_output_dict["state"] = 0
        shared_output_dict["output_string"] = "Début du processus\n"

        gopro_ip = start_and_set_fov(resolution_id, fov_id)
        shared_output_dict["state"] = 1

        shared_output_dict["output_string"] += "En attente du QRCode\n"
        last_qr_code_time, last_qr_code_tps = wait_for_initial_qr_code(gopro_ip, resolution_id)  # Commenté pour les tests
        # last_qr_code_time = time.time()
        # last_qr_code_tps = 0
        shared_output_dict["state"] = 2
        
        shared_output_dict["output_string"] += "QR code détecté\n"
        shared_output_dict["output_string"] += "Début de l'enregistrement\n"

        shared_output_dict["start_time"] = time.time()

        # Creation du dossier output
        shared_output_dict["output_folder"] = outputFolder

        for i in range(number_of_videos):
            shared_output_dict["video_number"] = i + 1
            record_images(gopro_ip, outputFolder, last_qr_code_time, last_qr_code_tps, video_duration, shared_output_dict)

        shared_output_dict["state"] = 3
        stop_gopro(gopro_ip)
        shared_output_dict["state"] = 4
        shared_output_dict["output_string"] += "Capture terminée\n"

    except Exception as e:
        print(e)
        
        shared_output_dict["state"] = -1
        shared_output_dict["error"] = str(e)
        shared_output_dict["output_string"] += "Une erreur est survenue\n"

        if gopro_ip:
            stop_gopro(gopro_ip)
            shared_output_dict["output_string"] += "GoPro arrêtée\n"

    finally:
        shared_output_dict["end_time"] = time.time()
        shared_output_dict["output_string"] += "Fin du processus\n"


def shutdown_gopro():
    gopro_ip_addresses = get_gopro_ip_addresse()
    stop_all_gopro(gopro_ip_addresses)
