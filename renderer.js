const { ipcRenderer } = require('electron');

let selectInputBtn = document.getElementById('selectInputBtn');
let selectOutputBtn = document.getElementById('selectOutputBtn');
let startConversionBtn = document.getElementById('startConversionBtn');
let openConfigBtn = document.getElementById('openConfigBtn');
let inputPath = document.getElementById('inputPath');
let outputPath = document.getElementById('outputPath');
let progressArea = document.getElementById('progressArea');

let enableYoutubeCheckbox = document.getElementById('enableYoutube');
let youtubeSettings = document.getElementById('youtubeSettings');
let youtubeTitleTemplate = document.getElementById('youtubeTitleTemplate');
let youtubeDescription = document.getElementById('youtubeDescription');
let youtubeTags = document.getElementById('youtubeTags');
let youtubePrivacy = document.getElementById('youtubePrivacy');

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

enableYoutubeCheckbox.addEventListener('change', () => {
    youtubeSettings.style.display = enableYoutubeCheckbox.checked ? 'block' : 'none';
});

startConversionBtn.addEventListener('click', () => {
    if (inputDirectory === '' || outputDirectory === '') {
        alert('Please select both input and output directories');
        return;
    }

    let youtubeOptions = {
        enabled: enableYoutubeCheckbox.checked,
        titleTemplate: youtubeTitleTemplate.value,
        description: youtubeDescription.value,
        tags: youtubeTags.value.split(',').map(tag => tag.trim()),
        privacy: youtubePrivacy.value
    };

    ipcRenderer.send('start-conversion', { inputDirectory, outputDirectory, youtubeOptions });
});

ipcRenderer.on('conversion-started', () => {
    progressArea.textContent = 'Conversion in progress...';
});

ipcRenderer.on('conversion-progress', (event, message) => {
    progressArea.textContent += '\n' + message;
});

ipcRenderer.on('conversion-error', (event, message) => {
    progressArea.textContent += '\nError: ' + message;
});

ipcRenderer.on('conversion-complete', (event, code) => {
    if (code === 0) {
        progressArea.textContent += '\nConversion completed successfully.';
    } else {
        progressArea.textContent += `\nConversion completed with errors. Exit code: ${code}`;
    }
});

openConfigBtn.addEventListener('click', () => {
    ipcRenderer.send('open-config');
});