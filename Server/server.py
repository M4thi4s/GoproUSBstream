from flask import Flask, request, jsonify, Response
from flask_restx import Api, Resource, Namespace, fields, reqparse
import os
import multiprocessing
from multiprocessing import Manager
from gopro import startRecord, shutdown_gopro
import psutil
import zipfile
from configs import output_folder, output_gopro_folder, output_zip_folder
import numpy as np
from parsePhotos import start_extract_images_and_match_coordinates
import time
import pandas as pd
from werkzeug.datastructures import FileStorage
from flask_cors import CORS
import traceback

app = Flask(__name__)
CORS(app)

api = Api(app, version='1.0', title='GoPro API', description='Une API pour gérer la capture de vidéos GoPro')

# Namespace pour la gestion de GoPro
ns_gopro = Namespace('gopro', description='Opérations GoPro')
api.add_namespace(ns_gopro)

# Namespace pour la gestion des fichiers
ns_file_management = Namespace('file_management', description='Gestion des fichiers')
api.add_namespace(ns_file_management)

# Définition du modèle de requête pour /start_capture
start_capture_model = api.model('StartCapture', {
    'resolution': fields.Integer(default=12, description='4: (640, 480), 7: (1280, 720), 12: (1920, 1080)'),
})

# Initialisation des variables globales
manager = None
shared_gopro_capture_info = None
shared_parsing_info = None
current_process = None

def initialize_manager():
    global manager, shared_gopro_capture_info, shared_parsing_info, current_process
    manager = Manager()
    shared_gopro_capture_info = manager.dict()
    shared_parsing_info = manager.dict()
    current_process = None

@ns_gopro.route('/start_capture')
class StartCapture(Resource):
    @api.expect(start_capture_model)
    def post(self):
        global current_process

        # Vérifier si un processus est déjà en cours
        if current_process is not None and current_process.is_alive():
            return {'state': 'Ko', 'error': 'Process is already running'}

        # reset dict
        shared_gopro_capture_info.clear()

        current_output_folder = os.path.join(output_folder, time.strftime("%Y-%m-%d"), output_gopro_folder)

        args = request.json
        current_process = multiprocessing.Process(target=startRecord, args=(current_output_folder, shared_gopro_capture_info, args['resolution']))
        current_process.start()
        return {'state': 'Ok'}
        
@api.route('/monitoring_info')
class MonitoringInfo(Resource):
    def get(self):
        # Calcul de l'utilisation du disque
        disk_info = psutil.disk_usage('/')
        disk_usage_mb = disk_info.used / (1024 * 1024)  # Convertir en Mo
        disk_usage_percent = disk_info.percent

        # Calcul de l'utilisation de la RAM
        ram_info = psutil.virtual_memory()
        ram_usage = ram_info.percent

        # Calcul de l'utilisation du swap
        swap_info = psutil.swap_memory()
        swap_usage = swap_info.percent

        # Retourne les informations de monitoring
        return { 
            'disk_usage_Mo': disk_usage_mb,
            'disk_usage_percent': disk_usage_percent,
            'ram_usage_percent': ram_usage,
            'swap_usage_percent': swap_usage,
            'gopro_capture_info': shared_gopro_capture_info.copy(),
            'parsing_info': shared_parsing_info.copy()
        }

@ns_gopro.route('/kill_current_process')
class KillCurrentProcess(Resource):
    def get(self):
        global current_process

        if current_process is not None and current_process.is_alive():
            current_process.terminate()
            # current_process = None
        
        try:
            shutdown_gopro()
            return {'state': 'Process and gopro shutdown successfully'}
        except Exception as e:
            return {'state': 'Ko', 'error': 'Process shutdown but unable to shutting down the GoPro. '+str(e)}


@ns_gopro.route('/stop_capture')
class StopCaptureProcess(Resource):
    def get(self):
        shared_gopro_capture_info["end_time"] = time.time()
        return {'state': 'Ok. Please wait for buffer to be written.'}

# Définition du modèle de requête pour /associate_photos_with_GPS_data
ns_file_management = Namespace('file_management', description='Gestion des fichiers')
api.add_namespace(ns_file_management)

# Création d'un parser pour le téléchargement de fichiers
file_upload = reqparse.RequestParser()
file_upload.add_argument('coordinates_file', type=FileStorage, location='files', required=True, help='Fichier CSV contenant les coordonnées GPS')
file_upload.add_argument('directory_name', type=str, required=True, help='Nom du dossier de sortie')

@ns_file_management.route('/list_directories')
class ListDirectories(Resource):
    def get(self):
        directories = [d for d in os.listdir(output_folder) if os.path.isdir(os.path.join(output_folder, d))]
        return jsonify(directories)

@ns_file_management.route('/associate_photos_with_GPS_data')
class ParseVideos(Resource):
    @api.expect(file_upload)  # Parser pour le fichier
    def post(self):
        global current_process

        if current_process is not None and current_process.is_alive():
            return {'state': 'Ko', 'error': 'Process is already running'}

        # reset dict
        shared_parsing_info.clear()

        uploaded_file_args = file_upload.parse_args()
        uploaded_file = uploaded_file_args['coordinates_file']
        directory_name = uploaded_file_args['directory_name']
        
        input_folder = os.path.join(output_folder, directory_name, output_gopro_folder)
        output_folder_date = os.path.join(output_folder, directory_name, output_gopro_folder)

        if not os.path.exists(input_folder):
            return {'state': 'Ko', 'error': 'Folder does not exist'}


        try:
            # Lire le fichier CSV avec pandas
            df = pd.read_csv(uploaded_file)

            # Vérifier le format des colonnes
            if df.columns.tolist() != ["Time (UTC)","Latitude","Longitude","Altitude","Satellites","HDOP","True Heading"]:
                raise Exception("Invalid file format. Expected columns: 'Time (UTC)', 'Latitude', 'Longitude', 'Altitude', 'Satellites', 'HDOP'")

            # Convertir le DataFrame en un tableau NumPy
            coordinatesNumpy = df.to_numpy()

        except Exception as e:
            return {'state': 'Ko', 'error': f'Error while parsing coordinates file. {e}'}
        
        current_process = multiprocessing.Process(target=start_extract_images_and_match_coordinates, args=(input_folder, coordinatesNumpy, shared_parsing_info))
        current_process.start()
        return {'state': 'Ok'}
    
@ns_file_management.route('/delete_directory/<string:directory_name>')
@api.param('directory_name', 'Nom du dossier à supprimer')
class DeleteDirectory(Resource):
    def get(self, directory_name):
        global current_process

        if current_process is not None and current_process.is_alive():
            return {'state': 'Ko', 'error': 'Process is already running'}
        
        directory_path_full = os.path.join(output_folder, directory_name)

        if not os.path.exists(directory_path_full):
            return {'state': 'Ko', 'error': 'Folder does not exist.'}

        try:
            # Suppression du dossier
            os.system(f'rm -rf {directory_path_full}')
            return {'state': 'Ok'}
        except Exception as e:
            return {'state': 'Ko', 'error': f'Error while deleting directory. {e}'}


def zip_directory(directory_path, full_output_zip_folder, zip_filename, progress_dict):
    try:
        progress_dict['state'] = 'in_progress'
        progress_dict['progress'] = 0

        # Créer une liste de tous les fichiers à zipper
        file_paths = []
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                file_paths.append(file_path)
                print ("File path: ", file_path)

        total_files = len(file_paths)
        processed_files = 0

        with zipfile.ZipFile(os.path.join(full_output_zip_folder, zip_filename), 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in file_paths:
                zipf.write(file_path, os.path.relpath(file_path, directory_path))
                processed_files += 1
                progress_dict['progress'] = (processed_files / total_files) * 100
                print(f"File {processed_files}/{total_files} zipped. Progress: {progress_dict['progress']:.2f}%")

        progress_dict['state'] = 'done'
    except Exception as e:
        print(f"An error occurred: {e}")
        traceback.print_exc()  # Ajout d'une trace complète pour aider au diagnostic
        progress_dict['state'] = 'error'
        progress_dict['error'] = str(e)

    print("Exiting zip_directory function")

@ns_file_management.route('/create_zip/<string:directory_name>')
@api.param('directory_name', 'Nom du dossier à zipper')
class CreateZip(Resource):
    def get(self, directory_name):
        global current_process

        directory_path = os.path.join(output_folder, directory_name)
        full_output_zip_folder = os.path.join(output_zip_folder, directory_name)
        if not os.path.exists(directory_path):
            return {'state': 'Ko', 'error': 'Folder does not exist'}

        if current_process is not None and current_process.is_alive():
            return {'state': 'Ko', 'error': 'Another process is running'}
        
        if not os.path.exists(full_output_zip_folder):
            os.makedirs(full_output_zip_folder)

        shared_parsing_info.clear()
        current_process = multiprocessing.Process(target=zip_directory, args=(directory_path, full_output_zip_folder, 'photos.zip', shared_parsing_info))
        current_process.start()

        return {'state': 'Ok'}
    
# Route pour supprimer le fichier ZIP
@ns_file_management.route('/delete_zip/<string:directory_name>')
@api.param('directory_name', 'Nom du dossier du fichier ZIP')
class DeleteZip(Resource):
    def get(self, directory_name):
        zip_file_path = os.path.join(output_zip_folder, directory_name, 'photos.zip')
        if os.path.exists(zip_file_path):
            os.remove(zip_file_path)
            return {'state': 'Ok'}
        else:
            return {'state': 'Ko', 'error': 'ZIP file does not exist'}
if __name__ == '__main__':
    initialize_manager()  # Initialisation du Manager et des variables partagées
    app.run(host='0.0.0.0', port=8080)
