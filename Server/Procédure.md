# Mise en place d'une capture

## Vérifier la Batterie
Assurez-vous que les GoPros et le GPS sont suffisamment chargés. Pour les tests, les GoPros n'ont pas besoin de carte SD.
## Fixation des GoPros
Installez les deux GoPros sur le toit de la voiture de manière à ce qu'elles filment vers la droite et la gauche de la voiture.
## Branchement des GoPros
Connectez les GoPros au convertisseur de courant de la voiture.
## Fixation du GPS
Placez le GPS sur le toit de la voiture, au même niveau que les GoPros.
## Branchement du GPS
Connectez le GPS à l'ordinateur.
## Création d'un Réseau Wi-Fi
Mettez en place un réseau Wi-Fi nommé "edencar", sans mot de passe. Ce réseau doit avoir accès à Internet pour initialiser les horloges des Raspberry Pi.
## Démarrage de la Voiture 
Mettez la voiture en marche.
## Récupération des IP des GoPros 
Trouvez les adresses IP des deux GoPros sur le point d'accès Wi-Fi.
## Connexion aux Raspberry Pi 
Accédez aux deux Raspberry Pi depuis un navigateur à l'adresse "IP:8080". Vérifiez via la route "/## monitoring_info" que l'espace de stockage n'est pas saturé (prévoir 15 Go pour 3 heures de session).
## Allumage des GoPros 
Mettez en marche les deux GoPros et attendez que le message "USB CONNECTE" s'affiche à l'écran.
## Lancement de la Capture 
Activez la capture sur les deux APIs des Raspberry Pi en utilisant la route "startCapture" avec une résolution de 12 (4: (640, 480), 7: (1280, 720), 12: (1920, 1080)). Notez le lien entre l'adresse IP de chaque Raspberry Pi, son nom, et son emplacement par rapport à la voiture.
## Attente du QR Code 
Surveillez la route "/monitoring" jusqu'à ce que le message "En attente du QRCode" apparaisse dans la section "output_string".
## Lancement du Script GPS 
Démarrez le script "capturePosition.py" (commande python capturePosition.py) et attendez le message "GPGGA and GPRMC messages match." Ceci indique que le GPS est calibré et que l'enregistrement des coordonnées GPS a commencé.
## Affichage du QR Code 
Accédez à "IPgopro/QRCodeDateTimeGenerator.html.html" et présentez le QRCode généré aux deux GoPros. Attendez que le message "QR code détecté" apparaisse sur la route "/monitoring_info" des deux GoPros.
## Début du Trajet
La voiture est maintenant prête à partir.

# Durant la capture

## Surveillance des GoPros :
- Utilisation du Disque : Surveillez régulièrement l'évolution sur la route "/monitoring_info" pour les deux GoPros. Assurez-vous que l'utilisation du disque (disk_usage) et le nombre de photos capturées augmentent.
- Latence du Buffer : Vérifiez que la valeur de buffer_late est proche de 0.

## Surveillance du GPS :
- Messages GPS : Assurez-vous que le GPS n'affiche pas de messages d'erreur fréquents, tels que "GPGGA and GPRMC messages do not match". Quelques messages de ce type (jusqu'à un par minute) sont normaux, mais si leur nombre est trop élevé, arrêtez la capture et redémarrez-la à partir du moment où les erreurs ont commencé.

# A la fin de la capture

## Arrêt de la Capture
Lancez la route "/stop_capture" sur les deux Raspberry Pi.
## Arrêt du Script GPS
Dans le terminal où le script "capturePosition.py" a été lancé, utilisez le raccourci CTRL+C pour arrêter le script.
## Vérification de la Fin de Capture
Surveillez "/monitoring_info" pour confirmer que la capture est terminée (state=4) sur les deux GoPros.
## Liste des Répertoires
Utilisez la route "/list_directory" pour vérifier que la date du jour apparaît sur les Raspberry Pi.
## Association Photos et GPS
Lancez la route "/associate_photos_with_GPS_data", en envoyant la date du jour et le fichier généré par "capturePosition.py" (le fichier se trouve dans "output/AAAA-MM-JJ/positions/gps_data.csv").
## Suivi du Traitement
Surveillez "/monitoring_info" jusqu'à ce que "state=2" apparaisse dans "parsing_info" (ce qui devrait se faire en quelques secondes ou minutes).
## Génération du ZIP
Lancez la route "/create_zip" avec comme paramètre la date du jour.
## Suivi de la Génération des ZIPs
Suivez l'évolution via "/monitoring_info". L'initialisation peut prendre jusqu'à 30 secondes avant que le pourcentage de progression ne commence à s'afficher.
## Récupération des ZIPs
Une fois le state à "done", accédez à "http://IPraspberry/output/" pour récupérer les fichiers ZIP créés à la date du jour sur chaque Raspberry Pi.

# Bugs potentiels
- Anormal Buffer Late : Si la valeur buffer_late est extrêmement élevée ou basse, cela peut être dû à une mauvaise calibration de l'horloge des Raspberry Pi. La capture ne pourra pas être arrêtée via la route "stop_gopro". Utilisez la route "kill_current_process" et suivez la même procédure pour récupérer les images.

- Problèmes Majeurs : En cas de gros problème, il est possible de se connecter aux Raspberry Pi via SSH et SFTP.

# Description rapide des routes

- /monitoring_info : Affiche l'état des processus et du stockage sur la Raspberry Pi. Cette route permet de visualiser l'avancement des traitements et d'identifier d'éventuelles erreurs.

- /gopro/kill_current_process : Arrête brutalement l'enregistrement en provenance de la GoPro en interrompant le processus. À utiliser en dernier recours. Le nombre d'images manquantes dépendra du retard de buffer indiqué dans "/monitoring_info".

- /gopro/start_capture : Démarre une capture vidéo.

- /gopro/stop_capture : Demande l'arrêt de la capture vidéo. Envoie une heure de fin au processus qui enregistre les images, arrêtant l'enregistrement une fois cette heure atteinte.

- /file_management/associate_photos_with_GPS_datas : Associe l'heure des photos aux relevés GPS du script "capturePosition.py". Enregistre un fichier "photo_time_and_position.csv".

- /file_management/create_zip : Génère un fichier ZIP contenant les photos et les données GPS associées. L'avancement est visible dans "/monitoring_info". Le fichier ZIP est enregistré sur le serveur NGINX, accessible via le port 80 de la Raspberry Pi dans le dossier "output/".

- /file_management/delete_directory : Supprime toutes les images capturées pour une date donnée, ainsi que les tableurs associés. Ne supprime pas les fichiers ZIP.

- /file_management/delete_zip : Supprime un fichier ZIP d'une date donnée. Efface le répertoire du serveur NGINX mais conserve les données des photos et des tableurs.

- /file_management/list_directories : Affiche tous les dossiers contenant les photos des jours de capture. Ne retourne pas les données du serveur NGINX.