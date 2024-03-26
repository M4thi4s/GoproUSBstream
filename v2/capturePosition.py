import os
import csv
import serial
import serial.tools.list_ports
from datetime import datetime
import time
import traceback
import logging

log_file = "capturePosition.log"

if os.path.exists(log_file):
    os.remove(log_file)

logging.basicConfig(filename=log_file, 
                    level=logging.INFO, 
                    format='%(asctime)s: %(message)s')

def convert_gps_time_to_datetime(gps_time):
    hour = int(gps_time[:2])
    minute = int(gps_time[2:4])
    second = int(gps_time[4:6])
    microsecond = int(float(gps_time[6:]) * 1000000)
    now = datetime.now()
    return datetime(now.year, now.month, now.day, hour, minute, second, microsecond)

def parse_gpgga(gpgga_message):
    parts = gpgga_message.split(',')
    if len(parts) < 15 or parts[0] != '$GPGGA':
        return None

    time_utc = convert_gps_time_to_datetime(parts[1])
    latitude_decimal = convert_to_decimal(parts[2], parts[3])
    longitude_decimal = convert_to_decimal(parts[4], parts[5])
    altitude = parts[9]
    satellites = parts[7]
    hdop = parts[8]

    return {'time_utc': time_utc, 'latitude': latitude_decimal, 'longitude': longitude_decimal, 'altitude': altitude, 'satellites': satellites, 'hdop': hdop}

def parse_gprmc(gprmc_message):
    parts = gprmc_message.split(',')
    if len(parts) < 13 or parts[0] != '$GPRMC' or parts[2] != 'A':
        return None

    time_utc = convert_gps_time_to_datetime(parts[1])
    true_heading = parts[8]

    return {'time_utc': time_utc, 'true_heading': true_heading}

def convert_to_decimal(coord_str, direction):
    # Séparation des degrés et des minutes en fonction du format DDMM.MMMM
    d, m = divmod(float(coord_str), 100)
    decimal = d + (m / 60)

    # Inversion de la valeur pour les directions Sud et Ouest
    if direction in ['S', 'W']:
        decimal *= -1

    return decimal

def detect_gps_port():
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if "Eos GNSS" in port.description:
            return port.device
    raise Exception("GPS sensor not detected.")

def main(port=None):
    port = port or detect_gps_port()
    baud_rate = 19200
    output_folder = os.path.join('output', datetime.now().strftime('%Y-%m-%d'))
    os.makedirs(output_folder, exist_ok=True)
    positions_folder = os.path.join(output_folder, 'positions')
    os.makedirs(positions_folder, exist_ok=True)
    csv_file_path = os.path.join(positions_folder, 'gps_data.csv')
    file_exists = os.path.isfile(csv_file_path)

    last_message_time = time.time()
    time_between_messages = 15

    with serial.Serial(port, baud_rate) as ser, open(csv_file_path, mode='a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(['Time (UTC)', 'Latitude', 'Longitude', 'Altitude', 'Satellites', 'HDOP', 'True Heading'])

        gpgga_data = None
        try:
            while True:
                line = ser.readline().decode('utf-8', errors='replace').strip()
                try : 
                    if line.startswith('$GPGGA'):
                        gpgga_data = parse_gpgga(line)
                    elif line.startswith('$GPRMC'):
                        gprmc_data = parse_gprmc(line)

                        if gprmc_data and gpgga_data and gprmc_data['time_utc'] == gpgga_data['time_utc']:

                            if last_message_time + time_between_messages < time.time():
                                last_message_time = time.time()
                                logging.info (f"Time: {gpgga_data['time_utc']}, Latitude: {gpgga_data['latitude']}, Longitude: {gpgga_data['longitude']}, Altitude: {gpgga_data['altitude']}, Satellites: {gpgga_data['satellites']}, HDOP: {gpgga_data['hdop']}, True Heading: {gprmc_data['true_heading']}")
                           
                            writer.writerow([gpgga_data['time_utc'], gpgga_data['latitude'], gpgga_data['longitude'], gpgga_data['altitude'], gpgga_data['satellites'], gpgga_data['hdop'], gprmc_data['true_heading']])
                            file.flush()
                        elif last_message_time + time_between_messages < time.time():
                            logging.info("GPGGA and GPRMC messages do not match.")
                            
                except Exception as e:
                    logging.info("Error while parsing GPS data.")
                    logging.info(f"Error: {e}")
                    logging.info(traceback.format_exc())

        except KeyboardInterrupt:
            logging.info("Script stopped by user.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.info(f"Error: {e}")