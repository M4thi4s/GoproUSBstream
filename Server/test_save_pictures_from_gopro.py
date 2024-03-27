import av
import os
import time
from datetime import datetime
from fractions import Fraction
import psutil
import socket

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

def record_images(ip, output_folder, num_images=20):
    stream_url = f'udp://{ip}:8554?overrun_nonfatal=1&fifo_size=50000000'
    input_container = av.open(stream_url, options={'analyzeduration': '10000000', 'probesize': '10000000'})
    input_stream = input_container.streams.video[0]
    
    # S'assurer que le dossier de sortie existe
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        
    frame_count = 0
    for packet in input_container.demux(input_stream):
        if packet.stream.type != 'video':
            continue

        for frame in packet.decode():
            if not frame:
                continue
            
            frame_count += 1
            output_file_path = os.path.join(output_folder, f'image_{frame_count:03d}.jpg')
            frame.to_image().save(output_file_path)
            
            if frame_count >= num_images:
                break
        
        if frame_count >= num_images:
            break

    input_container.close()

# Exemple d'utilisation :
record_images('172.26.110.51', 'output/test')
