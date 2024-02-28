import psutil
import socket
import requests
import time
import cv2
import numpy as np
import random
import av
from fractions import Fraction

"""
ID 	FOV 	Supported Cameras
0 	Wide 	Hero 12 Black, Hero 9 Black, Hero 10 Black, Hero 11 Black
2 	Narrow 	Hero 12 Black, Hero 9 Black, Hero 10 Black, Hero 11 Black
3 	Superview 	Hero 12 Black, Hero 9 Black, Hero 10 Black, Hero 11 Black
4 	Linear 	Hero 12 Black, Hero 9 Black, Hero 10 Black, Hero 11 Black
"""
fov = 0
"""
ID 	Resolution 	Supported Cameras
4 	480p 	Hero 10 Black, Hero 9 Black
7 	720p 	Hero 12 Black, Hero 9 Black, Hero 10 Black, Hero 11 Black
12 	1080p 	Hero 12 Black, Hero 9 Black, Hero 10 Black, Hero 11 Black
"""
resolution = 7
width_resolution = 1280
height_resolution = 720

timeToStream = 30  # Durée totale du streaming en secondes
filmDuration = 5  # Durée de chaque film en secondes
stop_stream = False

def get_gopro_ip_addresses():
    gopro_ip_addresses = []
    for interface, addrs in psutil.net_if_addrs().items():
        if interface.startswith('usb'):
            for addr in addrs:
                if addr.family == socket.AF_INET:
                    ip_parts = addr.address.split('.')
                    ip_parts[-1] = '51'
                    modified_ip = '.'.join(ip_parts)
                    gopro_ip_addresses.append(modified_ip)
    return gopro_ip_addresses

def send_gopro_request(ip, path, params, timeout=10):
    response = requests.get(f"http://{ip}/gp/{path}", params=params, timeout=timeout)
    if response.status_code == 200:
        data = response.json()
        if data.get("error") != 0:
            print(f"Error with GoPro at {ip}: {data.get('error')}")
            return False
    else:
        print(f"Failed to connect to GoPro at {ip}, status code: {response.status_code}")
        return False
    return True

def start_and_set_gopro_resolutionand_fov(ip, resolution, fov):
    return send_gopro_request(ip, 'gpWebcam/START', {'res': resolution, 'fov': fov})

def stop_gopro(ip):
    print (f"Stopping GoPro at {ip}")
    random_sleep_time = random.randint(1, 5)
    time.sleep(random_sleep_time)
    return send_gopro_request(ip, 'gpWebcam/STOP', {})

def stop_all_gopro(gopro_ip_addresses):
    print ("Stopping all GoPro cameras")
    for gopro_ip in gopro_ip_addresses:
        if stop_gopro(gopro_ip):
            time.sleep(3)
        else:
            print(f"Failed to stop GoPro at {gopro_ip}")

def capture_image(ip, output_file):
    stream_url = f'udp://{ip}:8554?overrun_nonfatal=1&fifo_size=50000000'
    try:
        print (f"Capturing image from {ip}")
        container = av.open(stream_url, options={'analyzeduration': '5000000', 'probesize': '5000000'})
        for frame in container.decode(video=0):
            img = frame.to_image()
            img.save(output_file)
            break
        print (f"Image saved to {output_file}")
        container.close()
    except av.AVError as e:
        print(f"AVError occurred: {e}")
        return False
    return True

def record_video(ip, film_duration):
    stream_url = f'udp://{ip}:8554?overrun_nonfatal=1&fifo_size=50000000'
    
    # Ouvrir le flux vidéo
    input_container = av.open(stream_url)
    input_stream = input_container.streams.video[0]

    # Récupérer le time_base du flux vidéo
    time_base = input_stream.time_base
    print(f"Time Base: {time_base}")

    d = time.strftime("%Y-%m-%d_%H-%M-%S-%f")
    output_file = f"Sortie_{ip}_{d}.mp4"
    output_container = av.open(output_file, mode='w')

    # Créer le flux de sortie en se basant sur le flux d'entrée
    codec_name = input_stream.codec_context.name
    fps = input_stream.codec_context.rate if input_stream.codec_context.rate else Fraction(30, 1)  # Définir un taux de trame par défaut si nécessaire
    out_stream = output_container.add_stream(codec_name, str(fps))
    out_stream.width = input_stream.codec_context.width
    out_stream.height = input_stream.codec_context.height
    out_stream.pix_fmt = input_stream.codec_context.pix_fmt

    start_time = time.time()
    first_pts = None

    before_pts = None

    for frame in input_container.decode(input_stream):
        if time.time() - start_time > film_duration:
            break

        # Conserver le PTS original
        if first_pts is None:
            first_pts = frame.pts


        if before_pts is not None:
            print("DIFFERENCE PTS : ", float((frame.pts*frame.time_base) - (before_pts*frame.time_base)))
        before_pts = frame.pts

        frame.pts = frame.pts - first_pts
        
        print (f"FRAME TPS : {float(frame.pts*frame.time_base)}")
        
        out_packet = out_stream.encode(frame)
        output_container.mux(out_packet)
        print(out_packet)

    # Finaliser l'encodage
    try:
        out_packet = out_stream.encode(None)
        while out_packet:
            output_container.mux(out_packet)
            out_packet = out_stream.encode(None)
    except av.EOFError:
        # Fin de l'encodage, aucune action supplémentaire n'est nécessaire
        pass
    
    input_container.close()
    output_container.close()

def start_and_set_fov():
    print ("Starting GoPro cameras, setting resolution and fov...")
    global fov, resolution
    gopro_ip_addresses = get_gopro_ip_addresses()
    for gopro_ip in gopro_ip_addresses:
        if start_and_set_gopro_resolutionand_fov(gopro_ip, resolution, fov):
            time.sleep(5)
            print (f"GoPro at {gopro_ip} started and set to resolution {resolution} and fov {fov}")
    return gopro_ip_addresses

def main():
    print("Starting the process")
    try:
        gopro_ip_addresses = start_and_set_fov()
    except Exception as e:
        print(f"An error occurred: {e}")
        stop_all_gopro(get_gopro_ip_addresses())
        return

    start_time = time.time()
    while time.time() - start_time < timeToStream:
        print("recording videos...")
        for gopro_ip in gopro_ip_addresses:
            print (f"Recording videos from {gopro_ip}")
            d = time.strftime("%Y-%m-%d_%H-%M-%S")
            record_video(gopro_ip, filmDuration)

    stop_all_gopro(get_gopro_ip_addresses())

if __name__ == "__main__":
    try:
        if stop_stream:
            stop_all_gopro(get_gopro_ip_addresses())
        else:
            main()
    except KeyboardInterrupt:
        print("Process stopped manually.")
