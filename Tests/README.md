Ce dossier contient une série de scripts de test pour le projet GoPro. Ces tests sont axés sur différentes fonctionnalités liées à l'usage des caméras GoPro, notamment le streaming, la capture d'images, l'enregistrement vidéo, et la calibration via QR Code.
Scripts de Test Inclus

# goproGetAndCompareTpsBetweenStreamFrame.py
Ce script teste la différence de temps entre les frames lors du streaming à partir de GoPros. Il permet de démarrer et d'arrêter les GoPros, de capturer des images et d'enregistrer des vidéos avec des informations temporelles détaillées.

# goproPreviewStream.py
Ce script est conçu pour démarrer des flux de streaming depuis les GoPros, capturer des images et analyser le streaming. Il gère également le démarrage et l'arrêt des streams sur les caméras.

# goproQRCodeDateCalibration.py
Focalisé sur la calibration de l'heure via QR Code, ce script extrait des informations temporelles à partir de QR Codes et les associe à des vidéos enregistrées, pour une synchronisation précise.

# goproWebCamStream.py
Ce test implique le streaming de vidéos depuis des GoPros configurées en mode webcam. Il comprend la capture d'images et l'enregistrement de vidéos, tout en testant différents paramètres de résolution et de champ de vision (FOV).

# QRCodeDateTimeGenerator.html
Une page HTML simple avec un script JavaScript pour générer des QR Codes en temps réel avec l'heure actuelle. Utile pour les tests de calibration temporelle via QR Code.
Utilisation

Pour exécuter les scripts de test, suivez ces étapes :

1. Assurez-vous que les dépendances requises sont installées.
2. Connectez votre GoPro via USB et assurez-vous qu'elle est reconnue par votre système.
3. Exécutez les scripts individuellement pour tester les différentes fonctionnalités.
4. Pour QRCodeDateTimeGenerator.html, ouvrez le fichier dans un navigateur pour générer et visualiser les QR Codes en temps réel.

# Notes Importantes

Les scripts sont indépendants les uns des autres et peuvent être exécutés séparément.
Certains scripts utilisent des bibliothèques telles que av et psutil, assurez-vous qu'elles sont installées.
Il est recommandé de lire et de comprendre chaque script avant de l'exécuter, car ils peuvent affecter le fonctionnement de vos appareils GoPro.