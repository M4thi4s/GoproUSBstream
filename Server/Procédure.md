# Mise en place d'une capture

0. Vérifier que les gopros et le GPS ont de la batterie. Les gopros n'ont pas besoin de carte SD pour les tests
1. Fixer les 2 gopros sur le toit de la voiture à regarder vers la droite et la gauche de la voiture
2. Brancher les gopros au convertisseur de courant de la voiture
3. Fixer le GPS sur le toit de la voiture à la même hauteur que les gopros
4. Brancher le GPS à l'ordinateur
5. Créer un réseau wifi sans mot de passe nommé "edencar"
6. Démarrer la voiture
7. Récuperer l'IP des 2 gopros sur le point d'acces wifi
8. Se connecter aux 2 raspberry sur l'ordinateur via la navigateur à l'adresse "IP:8080" et vérifier via la route "/monitoring_info" que les raspberry n'ont pas leur espace de stockage saturé (compter 20go / 3h de session => nombre à confirmer)
9. Démarrer le script "capturePosition.py" (python capturePosition.py) et attendre que le message "GPGGA and GPRMC messages match." apparaisse. Ce message signifie que le GPS est calibré et que l'enregistrement des coordonnées GPS a démarré.
10. Allumer les 2 gopros et attendre que le message "USB CONNECTE" s'affiche sur l'écran.
11. Sur les 2 APIs des raspberry, lancer la route "startCapture" avc une résolution de 12   (4: (640, 480), 7: (1280, 720), 12: (1920, 1080))
12. Lancer la route /monitoring jusqu'à ce que le message "En attente du QRCode" apparaisse dans la section "output_string"
13. Se connecter à l'adresse "IPgopro/actualDate.html" et montrer un QRCode généré à une des caméras des gopros. Identifier l'IP de la caméra qui a la message "QR code détecté" qui s'affiche sur la route "/monitoring_info". Avant de montrer le QRCode à la deuxième gopro, bien associé l'IP au coté de la voiture où le QRCode a été montré (gauche ou droite).
14. Montrer le QRCode à la deuxième gopro et attendre que le message "QR code détecté" apparaisse sur l'autre adresse IP. Bien noter que cette IP correspond à l'autre coté.
15. A ce niveau la, la prise de photos peut commencer !

# Durant la capture

1. Vérifier à interval régulier l'évolution de monitoring_info/ pour les 2 gopros. 
- Vérifier que le disk_usage et le nombre de photos augmente
- Vérifier que la valeur buffer_late est proche de 0

2. Vérifier que le GPS ne retourne pas de message "GPGGA and GPRMC messages do not match". Il peut en avoir quelques un de l'ordre de 1 par minute maximum mais si il le terminal en ait submergé, arreter la capture et reprendre une capture du début des erreurs.

# A la fin de la capture

1. Lancer la route /stop_capture sur les 2 raspberry.
2. Dans le terminal qui a lancé le script "capturePosition.py", couper le script à l'aide du raccourci CTRL+C
2. Lancer la route /list_directory et vérifier que la date du jour apparaisse sur les raspberry
3. Lancer la route /associate_photos_with_GPS_data en envoyant la date du jours et le fichier généré via capturePosition.py (le fichier est localisé en partant du dossier ou est stocké "capturePosition.py", puis dans le fichier output/AAAA-MM-JJ/positions/gps_data.csv)
4. Attendre que la route "/monitoring_info" prenne le state=2 dans la partie "parsing_info" (Normalement atteint au bout de quelques secondes ou minutes)
5. Télécharger les 2 dossier contenant les images en faisant un appel à la route "/download_directory". Cette route peut être extremement longue car elle consiste à générer un fichier compressé avec toute les images avant de proposer son téléchargement par le navigateur. Si la récuperation via cette route est impossible => se connecter en SSH à la raspberry et récuperer les fichiers via sftp (contacter Mathias). Bien différencier le dossier téléchargé pour la gopro gauche et celui pour la gopro droite.
6. Tout debrancher et mettre à charger les gopros et le GPS.
