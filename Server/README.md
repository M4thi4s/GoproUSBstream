# Description
Ce projet offre une solution pour enregistrer des flux vidéos et photos à partir d'une GoPro connectée via USB. Il inclut des fonctionnalités avancées telles que l'extraction des images des flux vidéo avec enregistrement précis de l'heure de chaque frame, la calibration temporelle via un QR Code au début de chaque vidéo, et la récupération des positions GPS pour associer des coordonnées précises aux images extraites.

## Fonctionnalités
- Extraction de flux vidéo GoPro : Enregistre l'heure exacte de chaque frame avec une précision d'environ 100ms.
- Extraction d'images à partir de flux vidéo : Capture des images du flux vidéo avec enregistrement de l'heure précise de chaque frame.
- Calibration temporelle via QRCode : Utilise un QRCode au début de chaque vidéo pour calibrer l'heure exacte.
- Récupération de positions GPS : Utilise un GPS EOS Arrow 100+ pour récupérer des positions et les enregistrer dans un tableur.
- Association d'images avec heure et position GPS : Extractions d'images de vidéos associées à une heure exacte et une position GPS précise.

# Paramètres Réseau
Les pramètres réseaux dépendent de la configuration du raspberry. Dans mon cas voici la configuration pour effectuer une connexion automatique : 

    Nom du réseau WiFi : edenCar
    Mot de passe : Aucun

# Configuration du GPS

Pour changer la fréquence de rafraîchissement du GPS, utilisez le logiciel EOS Utility et modifiez les configurations du mode "USB".

# Todo List
- Tester avec différents FOV pour améliorer la lecture de caractères.
- Réaliser un test de 2 heures et analyser le retard du buffer avec une meilleure résolution.
- Analyser le comportement lorsque le buffer atteint sa taille maximale et calculer la durée correspondante dans le buffer.
- Effectuer un test de 2 heures avec les GoPros pour analyser tout retard potentiel.

# Architecture du Projet

## Server.py
    Serveur Flask avec des endpoints pour démarrer l'enregistrement, obtenir des informations de monitoring, arrêter les processus en cours, lister les répertoires, associer des photos avec des données GPS, télécharger et supprimer des répertoires.
    Utilisation de multiprocessing pour gérer les opérations en parallèle.
    Fonctions pour la gestion des GoPros, y compris le démarrage, l'arrêt, et la calibration.

## parsePhotos.py
    Script pour extraire les images des vidéos et associer des coordonnées GPS aux photos.
    Conversion des timestamps et recherche des coordonnées GPS les plus proches pour chaque image.

## gopro.py
    Script pour la gestion de la GoPro, y compris la détection de l'adresse IP de la GoPro, le démarrage/arrêt de l'enregistrement, et le décodage des QR Codes.

## configs.py
    Configuration des dossiers de sortie pour les photos et les vidéos.

## capturePositions.py
    Script pour capturer les positions GPS via un GPS EOS Arrow 100+.
    Parse et enregistre les données GPS dans un fichier CSV.

## parseVideo.py
    Extraction et traitement des images des vidéos, y compris la vérification de la qualité de l'image et l'association avec des coordonnées GPS.

## server.service
    Fichier de service systemd pour déployer l'application comme un service sur un serveur Linux.

## requirements.txt
    Liste des dépendances Python nécessaires pour exécuter le projet.

# Installation
    Clonez le dépôt Git.
    Installez les dépendances Python avec pip install -r requirements.txt.
    Configurez le fichier configs.py selon vos besoins.
    Lancez le serveur Flask avec python server.py.

# Calibration par QRCode
Pour calibrer les flux des gopros à une heure exacte vous allez devoir utiliser un QRCode contenant l'heure précise en ms. Un fichier HTML générant ce QRCode est disponible dans le dossier v1/QRCodeDatTimeGenerator.html.

## Utilisation
Voir le fichier Procédure.md

# License

## Conditions d'Utilisation
Libre d'utilisation et de modification : Vous pouvez utiliser et modifier ce code comme vous le souhaitez.
Obligation de citation : Si vous utilisez ou modifiez ce code, vous devez citer clairement l'auteur original.

## Responsabilité
L'auteur n'est pas responsable des conséquences de l'utilisation de ce code.

## Droits d'Auteur
Le code est protégé par des droits d'auteur et appartient à l'auteur original.