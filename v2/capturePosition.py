import os
import csv
import datetime
import serial
import serial.tools.list_ports
import pandas as pd
import datetime
from datetime import datetime
import time 

def convert_gps_time_to_datetime(gps_time):
    # gps_time est une chaîne sous la forme 'hhmmss.sss'
    hour = int(gps_time[0:2])
    minute = int(gps_time[2:4])
    second = int(gps_time[4:6])
    microsecond = int(float(gps_time[6:]) * 1000000)  # Conversion des millisecondes en microsecondes

    # Utilisez datetime.now() pour obtenir la date actuelle
    now = datetime.now()

    # Créez un objet datetime avec la date actuelle et l'heure GPS
    date_time_obj = datetime(now.year, now.month, now.day, hour, minute, second, microsecond)

    # Convertir en timestamp Unix (en secondes)
    timestamp = date_time_obj.timestamp()
    return timestamp


def parse_gpgga(gpgga_message):
    print (gpgga_message)
    parts = gpgga_message.split(',')

    if len(parts) < 15 or parts[0] != '$GPGGA' or not parts[2] or not parts[4]:
        print("Message GPGGA invalide.")
        return None
    else :
        print("Message GPGGA valide.")

    latitude = float(parts[2])
    latitude_degrees = int(latitude / 100)
    latitude_minutes = latitude - latitude_degrees * 100
    latitude_decimal = latitude_degrees + latitude_minutes / 60
    if parts[3] == 'S':
        latitude_decimal *= -1

    longitude = float(parts[4])
    longitude_degrees = int(longitude / 100)
    longitude_minutes = longitude - longitude_degrees * 100
    longitude_decimal = longitude_degrees + longitude_minutes / 60
    if parts[5] == 'W':
        longitude_decimal *= -1

    time_utc = convert_gps_time_to_datetime(parts[1])
    altitude = parts[9]
    satellites = parts[7]
    hdop = parts[8]

    return {
        'Time (UTC)': time_utc,
        'Latitude': latitude_decimal,
        'Longitude': longitude_decimal,
        'Altitude': altitude,
        'Satellites': satellites,
        'HDOP': hdop
    }

def detect_gps_port():
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if "Eos GNSS" in port.description:
            print (f"Capteur GPS 'Eos Tools Pro' détecté sur le port {port.device}.")
            return port.device
    raise Exception("Capteur GPS 'Eos Tools Pro' non détecté.")

def main(port=None):
    if port is None:
        port = detect_gps_port()
    baud_rate = 19200
    output_folder = os.path.join('output', datetime.now().strftime('%Y-%m-%d'))
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    positions_folder = os.path.join(output_folder, 'positions')
    if not os.path.exists(positions_folder):
        os.makedirs(positions_folder)
    csv_file_path = os.path.join(positions_folder, 'gps_data.csv')
    file_exists = os.path.isfile(csv_file_path)
        
    ser = serial.Serial(port, baud_rate)

    with open(csv_file_path, mode='a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(['Time (UTC)', 'Latitude', 'Longitude', 'Altitude', 'Satellites', 'HDOP'])

        last_flush_time = time.time()
        try:
            while True:
                line = ser.readline().decode('utf-8').strip()
                if line.startswith('$GPGGA'):
                    data = parse_gpgga(line)
                    if data:
                        writer.writerow([data['Time (UTC)'], data['Latitude'], data['Longitude'], data['Altitude'], data['Satellites'], data['HDOP']])
                        if time.time() - last_flush_time > 10:
                            file.flush()
                            last_flush_time = time.time()
        except KeyboardInterrupt:
            print("Arrêt du script par l'utilisateur.")
        finally:
            ser.close()
            print("Connexion série fermée.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Erreur: {e}")
