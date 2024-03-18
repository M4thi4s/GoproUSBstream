from flask import Flask, request, jsonify, Response, stream_with_context
from flask_restx import Api, Resource, Namespace, fields
import os
import multiprocessing
from multiprocessing import Manager
from gopro import startRecord, shutdown_gopro
import psutil
import zipfile
from configs import output_folder, output_gopro_folder, output_parsed_folder
import numpy as np
from parseVideo import start_extract_images_and_match_coordinates
import time

app = Flask(__name__)

api = Api(app, version='1.0', title='GoPro API', description='Une API pour gérer la capture de vidéos GoPro')

# Namespace pour la gestion de GoPro
ns_gopro = Namespace('gopro', description='Opérations GoPro')
api.add_namespace(ns_gopro)

# Namespace pour la gestion des fichiers
ns_file_management = Namespace('file_management', description='Gestion des fichiers')
api.add_namespace(ns_file_management)

# Définition du modèle de requête pour /start_capture
start_capture_model = api.model('StartCapture', {
    'capture_duration': fields.Integer(default=15, description='Durée de l\'enregistrement en secondes'),
    'capture_video_number': fields.Integer(default=2, description='Nombre de vidéos à créer'),
    'resolution': fields.Integer(default=7, description='4: (640, 480), 7: (1280, 720), 12: (1920, 1080)'),
})

# Définition du modèle de requête pour /parse_videos
parse_videos_model = api.model('ParseVideos', {
    'directory_name': fields.String(description='Nom du dossier à traiter (date au format AAAA-MM-JJ)'),
    'coordinates_file': fields.String(description='Fichier CSV contenant les coordonnées GPS (au format "TimeStamp,Latitude,Longitude". Les élements doivents être séparés par des virgules et les lignes par des retours à la ligne)'),
})

# Partage des données entre les processus
manager = Manager()

shared_gopro_capture_info = manager.dict()
shared_parsing_info = manager.dict()

# Variable pour conserver le processus en cours
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
        current_process = multiprocessing.Process(target=startRecord, args=(current_output_folder, shared_gopro_capture_info, args['resolution'], args['capture_video_number'], args['capture_duration']))
        current_process.start()
        return {'state': 'Ok'}
        
@api.route('/monitoring_info')
class MonitoringInfo(Resource):
    def get(self):
        # Calcul de l'utilisation du disque
        disk_info = psutil.disk_usage('/')
        disk_usage_mb = disk_info.used / (1024 * 1024)  # Convertir en Mo

        # Calcul de l'utilisation de la RAM
        ram_info = psutil.virtual_memory()
        ram_usage = ram_info.percent

        # Calcul de l'utilisation du swap
        swap_info = psutil.swap_memory()
        swap_usage = swap_info.percent

        # Retourne les informations de monitoring
        return { 
            'disk_usage': disk_usage_mb,
            'ram_usage': ram_usage,
            'swap_usage': swap_usage,
            'gopro_capture_info': shared_gopro_capture_info.copy(),
            'parsing_info': shared_parsing_info.copy()
        }

@ns_gopro.route('/kill_current_process')
class KillCurrentProcess(Resource):
    def get(self):
        global current_process

        if current_process is not None and current_process.is_alive():
            current_process.terminate()
            current_process = None
        
        try:
            shutdown_gopro()
            return {'state': 'Process and gopro shutdwon successfully'}
        except Exception as e:
            return {'state': 'Ko', 'error': 'Process shutdown but unable to shutting down the GoPro. '+str(e)}


@ns_file_management.route('/list_directories')
class ListDirectories(Resource):
    def get(self):
        directories = [d for d in os.listdir(output_folder) if os.path.isdir(os.path.join(output_folder, d))]
        return jsonify(directories)

@ns_file_management.route('/parse_videos')
class ParseVideos(Resource):
    @api.expect(parse_videos_model)
    def post(self):
        global current_process

        # Vérifier si un processus est déjà en cours
        if current_process is not None and current_process.is_alive():
            return {'state': 'Ko', 'error': 'Process is already running'}

        # reset dict
        shared_parsing_info.clear()

        args = request.json

        # Exemple d'utilisation du script
        input_folder = os.path.join(output_folder, args['directory_name'], output_gopro_folder)
        output_folder_date = os.path.join(output_folder, args['directory_name'], output_parsed_folder)

        if not os.path.exists(input_folder):
            return {'state': 'Ko', 'error': 'Folder does not exist'}

        try:
            coordinatesNumpy = np.array([x.split(',') for x in args['coordinates_file'].split('\n') if x != ''])
            if coordinatesNumpy.shape[1] != 3:
                return {'state': 'Ko', 'error': 'Invalid coordinates file format. Must be "TimeStamp,Latitude,Longitude"'}
                        # check if TimeStamp,Latitude,Longitude is present on top of file
            if coordinatesNumpy[0, 0] == "TimeStamp" and coordinatesNumpy[0, 1] == "Latitude" and coordinatesNumpy[0, 2] == "Longitude":
                coordinatesNumpy = np.delete(coordinatesNumpy, 0, 0)
            else:
                raise Exception("Invalid coordinates file format. Must be \"TimeStamp,Latitude,Longitude\"")

            coordinatesNumpy = coordinatesNumpy.astype(np.float64)

        except Exception as e:
            return {'state': 'Ko', 'error': 'Error while parsing coordinates file. '+str(e)}
                
        current_process = multiprocessing.Process(target=start_extract_images_and_match_coordinates, args=(input_folder, output_folder_date, coordinatesNumpy, shared_parsing_info))
        current_process.start()
        return {'state': 'Ok'}


@ns_file_management.route('/download_directory/<string:directory_name>')
@api.param('directory_name', 'Nom du dossier à télécharger')
class DownloadDirectory(Resource):
    def get(self, directory_name):
        global current_process

        if current_process is not None and current_process.is_alive():
            return {'state': 'Ko', 'error': 'Process is already running'}
        
        directory_path_full = os.path.join(output_folder, directory_name, output_parsed_folder)

        if not os.path.exists(directory_path_full):
            return {'state': 'Ko', 'error': 'Folder does not exist or the parsing process is not started.'}

        # Génération du chemin du fichier ZIP temporaire
        zip_file_path = directory_path_full + '.zip'

        def generate_zip():
            with zipfile.ZipFile(zip_file_path, 'w') as zipf:
                for root, dirs, files in os.walk(directory_path_full):
                    for file in files:
                        zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), directory_path_full))
            with open(zip_file_path, 'rb') as f:
                while True:
                    data = f.read(4096)
                    if not data:
                        break
                    yield data
            os.remove(zip_file_path)  # Suppression du fichier ZIP après envoi

        response = Response(stream_with_context(generate_zip()), mimetype='application/zip')
        response.headers['Content-Disposition'] = f'attachment; filename={directory_name}.zip'
        return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
