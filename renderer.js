const { ipcRenderer } = require('electron');

let selectInputBtn = document.getElementById('selectInputBtn');
let selectOutputBtn = document.getElementById('selectOutputBtn');
let startConversionBtn = document.getElementById('startConversionBtn');
let openConfigBtn = document.getElementById('openConfigBtn');
let inputPath = document.getElementById('inputPath');
let outputPath = document.getElementById('outputPath');
let progressArea = document.getElementById('progressArea');

let inputDirectory = '';
let outputDirectory = '';

selectInputBtn.addEventListener('click', () => {
    ipcRenderer.send('select-input-directory');
});

ipcRenderer.on('input-directory-selected', (event, path) => {
    inputDirectory = path;
    inputPath.textContent = `Input: ${path}`;
});

selectOutputBtn.addEventListener('click', () => {
    ipcRenderer.send('select-output-directory');
});

ipcRenderer.on('output-directory-selected', (event, path) => {
    outputDirectory = path;
    outputPath.textContent = `Output: ${path}`;
});

startConversionBtn.addEventListener('click', () => {
    if (inputDirectory === '' || outputDirectory === '') {
        alert('Please select both input and output directories');
        return;
    }

    ipcRenderer.send('start-conversion', { inputDirectory, outputDirectory });
});

ipcRenderer.on('conversion-started', () => {
    progressArea.textContent = 'Conversion in progress...';
});

ipcRenderer.on('conversion-error', (event, message) => {
    progressArea.textContent += '\nError: ' + message;
});

ipcRenderer.on('conversion-complete', (event, code) => {
    if (code === 0) {
        progressArea.textContent = 'Conversion completed successfully.';
    } else {
        progressArea.textContent = `Conversion completed with errors. Exit code: ${code}`;
    }
});

openConfigBtn.addEventListener('click', () => {
    ipcRenderer.send('open-config');
});