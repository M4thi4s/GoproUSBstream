import psutil
import socket
import requests
import time
import av

"""
Les variables fov et resolution sont conservées pour être utilisées dans les futures fonctionnalités si nécessaire.
"""
fov = 0
resolution = 7
numberOfIteration = 2
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

def send_gopro_request(ip, path, port = 8080, timeout=10):
    response = requests.get(f"http://{ip}:{port}/{path}", timeout=timeout)
    if response.status_code == 200:
        print(f"Request to {path} on {ip} successful.")
        return True
    else:
        print(f"Failed to send request to {path} on {ip}, status code: {response.status_code}")
        return False

def start_stream_gopro(ip):
    return send_gopro_request(ip, 'gopro/camera/stream/start')

def stop_stream_gopro(ip):
    return send_gopro_request(ip, 'gopro/camera/stream/stop')

def stop_all_gopro(gopro_ip_addresses):
    print("Stopping all GoPro cameras")
    for gopro_ip in gopro_ip_addresses:
        if stop_stream_gopro(gopro_ip):
            time.sleep(3)
        else:
            print(f"Failed to stop stream on GoPro at {gopro_ip}")

def capture_image(ip, output_file):
    stream_url = f'udp://{ip}:8554?overrun_nonfatal=1&fifo_size=50000000'
    try:
        print(f"Capturing image from {ip}")
        container = av.open(stream_url, options={'analyzeduration': '5000000', 'probesize': '5000000'})
        for frame in container.decode(video=0):
            img = frame.to_image()
            img.save(output_file)
            break
        print(f"Image saved to {output_file}")
        container.close()
    except av.AVError as e:
        print(f"AVError occurred: {e}")
        return False
    return True

def start_all_streams():
    print("Starting GoPro streams...")
    gopro_ip_addresses = get_gopro_ip_addresses()
    for gopro_ip in gopro_ip_addresses:
        if start_stream_gopro(gopro_ip):
            time.sleep(5)
            print(f"Stream started on GoPro at {gopro_ip}")
    return gopro_ip_addresses

def main():
    print("Starting the process")
    global numberOfIteration
    try:
        gopro_ip_addresses = start_all_streams()
    except Exception as e:
        print(f"An error occurred: {e}")
        time.sleep(5)
        stop_all_gopro(get_gopro_ip_addresses())
        time.sleep(5)
        main()
        return
    
    for gopro_ip in gopro_ip_addresses:
        date = time.strftime("%Y-%m-%d_%H-%M-%S")
        if not capture_image(gopro_ip, f"image_{gopro_ip}_{date}.jpg"):
            print(f"Failed to capture image from GoPro at {gopro_ip}")
            time.sleep(5)
            stop_all_gopro(get_gopro_ip_addresses())
            time.sleep(5)
            main()
            return
        
    if(numberOfIteration > 1):
        print(f"{numberOfIteration} => Restarting the process")
        numberOfIteration -= 1
        main()
    else:
        stop_all_gopro(get_gopro_ip_addresses())

if __name__ == "__main__":
    try:
        if stop_stream:
            stop_all_gopro(get_gopro_ip_addresses())
        else:
            main()
    except KeyboardInterrupt:
        print("Process stopped manually.")
