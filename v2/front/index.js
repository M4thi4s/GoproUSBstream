document.addEventListener('DOMContentLoaded', function() {
    const qualitySelect = document.getElementById('quality');
    const ipGoproGaucheInput = document.getElementById('ipGoproGauche');
    const ipGoproDroiteInput = document.getElementById('ipGoproDroite');
    const logsGoproGauche = document.getElementById('logsGoproGauche');
    const logsGoproDroite = document.getElementById('logsGoproDroite');
    const startStreamButton = document.getElementById('startStream');
    const refreshLogsButton = document.getElementById('refreshLogs');
    const stopCaptureButton = document.getElementById('stopCapture');
    const associateGoprosButton = document.getElementById('associateGopros');
    const downloadButtons = document.getElementsByClassName('downloadData');
  
    let refreshIntervalId;
  
    function sendRequest(ip, endpoint, options, callback) {
      fetch(`${ip}/${endpoint}`, options)
        .then(response => response.json())
        .then(data => callback(data))
        .catch(error => console.error('Error:', error));
    }
  
    function handleFiles(files) {
      const file = files[0]; // Prendre le premier fichier si plusieurs sont sélectionnés
      const directoryName = new Date().toISOString().split('T')[0]; // Format 2024-03-26
      const ipGauche = `http://${ipGoproGaucheInput.value}:8080`;
      const ipDroite = `http://${ipGoproDroiteInput.value}:8080`;
  
      const formData = new FormData();
      formData.append('coordinates_file', file);
      formData.append('directory_name', directoryName);
  
      const options = {
        method: 'POST',
        body: formData
      };
  
      sendRequest(ipGauche, 'file_management/associate_photos_with_GPS_data', options, console.log);
      sendRequest(ipDroite, 'file_management/associate_photos_with_GPS_data', options, console.log);
    }
  
    startStreamButton.addEventListener('click', () =>
    {
  
        const quality = qualitySelect.value;
        const ipGauche = `http://${ipGoproGaucheInput.value}:8080`;
        const ipDroite = `http://${ipGoproDroiteInput.value}:8080`;

        const startOptions = {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ resolution: parseInt(quality) })
        };

        sendRequest(ipGauche, 'gopro/start_capture', startOptions, console.log);
        sendRequest(ipDroite, 'gopro/start_capture', startOptions, console.log);

        if(refreshIntervalId) clearInterval(refreshIntervalId);
        refreshIntervalId = setInterval(() => {
        refreshLogs(ipGauche, logsGoproGauche);
        refreshLogs(ipDroite, logsGoproDroite);
        }, 30000);
    });

  refreshLogsButton.addEventListener('click', () => {
    const ipGauche = `http://${ipGoproGaucheInput.value}:8080`;
    const ipDroite = `http://${ipGoproDroiteInput.value}:8080`;

    refreshLogs(ipGauche, logsGoproGauche);
    refreshLogs(ipDroite, logsGoproDroite);
  });

  stopCaptureButton.addEventListener('click', () => {
    const ipGauche = `http://${ipGoproGaucheInput.value}:8080`;
    const ipDroite = `http://${ipGoproDroiteInput.value}:8080`;

    sendRequest(ipGauche, 'gopro/stop_capture', { method: 'GET' }, console.log);
    sendRequest(ipDroite, 'gopro/stop_capture', { method: 'GET' }, console.log);

    if(refreshIntervalId) clearInterval(refreshIntervalId);
  });

  associateGoprosButton.addEventListener('click', () => {
    const csvInput = document.createElement('input');
    csvInput.type = 'file';
    csvInput.accept = '.csv';
    csvInput.onchange = e => handleFiles(e.target.files);
    csvInput.click(); // pour déclencher le dialogue de fichier
  });

  Array.from(downloadButtons).forEach(button => {
    button.addEventListener('click', event => {
      const ip = `http://${event.target.dataset.ip}:8080`;
      const directoryName = new Date().toISOString().split('T')[0]; // Format 2024-03-26
      downloadData(ip, directoryName);
    });
  });

  function refreshLogs(ip, textareaElement) {
    sendRequest(ip, 'monitoring_info', { method: 'GET' }, data => {
      textareaElement.value = JSON.stringify(data, null, 2);
    });
  }

  function downloadData(ip, directoryName) {
    const downloadEndpoint = `file_management/download_directory/${directoryName}`;
    window.open(`${ip}/${downloadEndpoint}`);
  }
});
