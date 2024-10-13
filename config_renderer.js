const { ipcRenderer } = require('electron');

// Get all input elements
const meleeIsoInput = document.getElementById('melee_iso');
const dolphinDirInput = document.getElementById('dolphin_dir');
const ffmpegInput = document.getElementById('ffmpeg');
const resolutionSelect = document.getElementById('resolution');
const videoBackendSelect = document.getElementById('video_backend');
const widescreenCheckbox = document.getElementById('widescreen');
const bitrateKbpsInput = document.getElementById('bitrateKbps');
const parallelGamesInput = document.getElementById('parallel_games');
const removeShortCheckbox = document.getElementById('remove_short');
const combineCheckbox = document.getElementById('combine');
const removeSlpsCheckbox = document.getElementById('remove_slps');

// Request current config data
ipcRenderer.send('get-config');

// Populate fields with current config data
ipcRenderer.on('config-data', (event, config) => {
    meleeIsoInput.value = config.melee_iso || '';
    dolphinDirInput.value = config.dolphin_dir || '';
    ffmpegInput.value = config.ffmpeg || '';
    resolutionSelect.value = config.resolution || '1080p';
    videoBackendSelect.value = config.video_backend || 'OGL';
    widescreenCheckbox.checked = config.widescreen || false;
    bitrateKbpsInput.value = config.bitrateKbps || 16000;
    parallelGamesInput.value = config.parallel_games || 'recommended';
    removeShortCheckbox.checked = config.remove_short || false;
    combineCheckbox.checked = config.combine || false;
    removeSlpsCheckbox.checked = config.remove_slps || false;
});

// Save button click handler
document.getElementById('saveBtn').addEventListener('click', () => {
    const newConfig = {
        melee_iso: meleeIsoInput.value,
        dolphin_dir: dolphinDirInput.value,
        ffmpeg: ffmpegInput.value,
        resolution: resolutionSelect.value,
        video_backend: videoBackendSelect.value,
        widescreen: widescreenCheckbox.checked,
        bitrateKbps: parseInt(bitrateKbpsInput.value),
        parallel_games: parallelGamesInput.value,
        remove_short: removeShortCheckbox.checked,
        combine: combineCheckbox.checked,
        remove_slps: removeSlpsCheckbox.checked
    };

    ipcRenderer.send('save-config', newConfig);
});

// Handle save result
ipcRenderer.on('config-save-result', (event, success) => {
    if (success) {
        alert('Configuration saved successfully!');
        window.close();
    } else {
        alert('Error saving configuration. Please try again.');
    }
});