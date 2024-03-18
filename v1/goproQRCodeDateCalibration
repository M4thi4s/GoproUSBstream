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

# Ignorer les avertissements spécifiques par leur message texte
# warnings.filterwarnings("ignore", message="deprecated pixel format used")
# warnings.filterwarnings("ignore", message="illegal short term buffer state detected")

# Paramètres de la caméra GoPro
FOV = 0  # Field of View
RESOLUTION = 7  # ID de la résolution (720p)
WIDTH_RESOLUTION = 1280
HEIGHT_RESOLUTION = 720

# Paramètres de streaming
NUMBER_OF_STREAMS = 3
STREAM_DURATION = 30  # Durée de chaque flux en secondes

# Variables de contrôle
last_qr_code_time = None
last_qr_code_tps = None
stop_stream = False

# Fonctions
def get_gopro_ip_addresses():
    gopro_ip_addresses = []
    for interface, addrs in psutil.net_if_addrs().items():
        if interface.startswith('usb'):
            for addr in addrs:
                if addr.family == socket.AF_INET:
                    ip_parts = addr.address.split('.')
                    ip_parts[-1] = '51'
                    gopro_ip_addresses.append('.'.join(ip_parts))
    return gopro_ip_addresses

def send_gopro_request(ip, path, params, timeout=10):
    response = requests.get(f"http://{ip}/gp/{path}", params=params, timeout=timeout)
    if response.status_code != 200 or response.json().get("error") != 0:
        return False
    return True

def start_and_set_gopro_resolutionand_fov(ip):
    return send_gopro_request(ip, 'gpWebcam/START', {'res': RESOLUTION, 'fov': FOV})

def stop_gopro(ip):
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
            return datetime.strptime(qr_data, '%Y-%m-%dT%H:%M:%S.%fZ')
    return None

def add_to_spreadsheet(output_video_file_name, frame_tps, real_time):
    file_path = 'tps_data.csv'
    df = pd.DataFrame([[output_video_file_name, frame_tps, real_time]], columns=['Video file name', 'TPS value', 'Datetime'])
    header = not pd.io.common.file_exists(file_path)
    df.to_csv(file_path, mode='a', index=False, header=header)

def wait_for_initial_qr_code():
    global last_qr_code_time, last_qr_code_tps
    fifo_size = int(WIDTH_RESOLUTION * HEIGHT_RESOLUTION * 1.5 * 3)
    ip = get_gopro_ip_addresses()[0]
    stream_url = f'udp://{ip}:8554?overrun_nonfatal=1&fifo_size={fifo_size}'

    while not last_qr_code_time:
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
            last_qr_code_time = qr_code_time
            last_qr_code_tps = frame.pts
            print("QR code time: ", last_qr_code_time)
            return

def record_video(ip):
    global last_qr_code_time, last_qr_code_tps
    stream_url = f'udp://{ip}:8554?overrun_nonfatal=1&fifo_size=50000000'
    input_container = av.open(stream_url, options={'analyzeduration': '10000000', 'probesize': '10000000'})
    input_stream = input_container.streams.video[0]
    time_base = input_stream.time_base
    output_file = f"Sortie_{ip}_{time.strftime('%Y-%m-%d_%H-%M-%S-%f')}.mp4"

    with av.open(output_file, mode='w') as output_container:
        out_stream = output_container.add_stream('libx264', str(input_stream.codec_context.rate or Fraction(30, 1)))
        out_stream.width = input_stream.codec_context.width
        out_stream.height = input_stream.codec_context.height
        out_stream.pix_fmt = 'yuv420p'
        out_stream.time_base = time_base
        out_stream.codec_context.options = {
            'preset': 'ultrafast',
            'tune': 'zerolatency',
            'crf': '30',
            'profile': 'baseline'
        }

        start_time = time.time()
        first_pts = None
        frame_count = 0
        last_frame = None
        last_time = None
        for packet in input_container.demux(input_stream):
            if packet.stream.type == 'video':
                frame = packet.decode()[0] if packet.decode() else None
                if not frame:
                    continue
                if time.time() - start_time > STREAM_DURATION:
                    break
                if first_pts is None:
                    first_pts = frame.pts
                if frame_count % 2 == 0:
                    add_to_spreadsheet(output_file, float((frame.pts - first_pts) * time_base), last_qr_code_time + timedelta(seconds=float((frame.pts - last_qr_code_tps) * time_base)))
                    frame.pts -= first_pts
                    out_packet = out_stream.encode(frame)
                    output_container.mux(out_packet) 

                    last_frame = frame
                    last_time = time.time()

                frame_count += 1

        print("Temps réel : ", float(last_time - start_time))
        print("Dernière heure de capture : {0:0.1f}".format(float(last_frame.pts * time_base)))    
    input_container.close()

def start_and_set_fov():
    gopro_ip_addresses = get_gopro_ip_addresses()
    for gopro_ip in gopro_ip_addresses:
        if start_and_set_gopro_resolutionand_fov(gopro_ip):
            time.sleep(5)
    return gopro_ip_addresses

def main():
    if stop_stream:
        stop_all_gopro(get_gopro_ip_addresses())
    else:
        gopro_ip_addresses = start_and_set_fov()
        wait_for_initial_qr_code()
        for _ in range(NUMBER_OF_STREAMS):
            for gopro_ip in gopro_ip_addresses:
                record_video(gopro_ip)
        stop_all_gopro(gopro_ip_addresses)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Processus arrêté manuellement.")
