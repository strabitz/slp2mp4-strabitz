const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const { execFile, spawn } = require('child_process');
const fs = require('fs');

let mainWindow;
let configWindow;

// Determine the path to the config file and Python executable
let configPath, pythonExecutablePath;
if (app.isPackaged) {
  configPath = path.join(process.resourcesPath, 'config.json');
  pythonExecutablePath = path.join(process.resourcesPath, 'slp2mp4');
} else {
  configPath = path.join(__dirname, 'slp2mp4', 'data', 'config.json');
  pythonExecutablePath = 'python';
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
    },
  });

  mainWindow.loadFile('index.html');
}

function createConfigWindow() {
  configWindow = new BrowserWindow({
    width: 600,
    height: 800,
    parent: mainWindow,
    modal: true,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
    },
  });

  configWindow.loadFile('config.html');
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

ipcMain.on('select-input-directory', async (event) => {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openDirectory']
  });
  if (!result.canceled) {
    event.reply('input-directory-selected', result.filePaths[0]);
  }
});

ipcMain.on('select-output-directory', async (event) => {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openDirectory']
  });
  if (!result.canceled) {
    event.reply('output-directory-selected', result.filePaths[0]);
  }
});

ipcMain.on('start-conversion', (event, { inputDirectory, outputDirectory, youtubeOptions }) => {
  event.reply('conversion-started');

  const args = [
    'run',
    '-o',
    outputDirectory,
    inputDirectory,
  ];

  if (youtubeOptions.enabled) {
    args.push('--youtube');
    args.push('--youtube-title', youtubeOptions.titleTemplate);
    args.push('--youtube-description', youtubeOptions.description);
    args.push('--youtube-tags', youtubeOptions.tags.join(','));
    args.push('--youtube-privacy', youtubeOptions.privacy);
  }

  const pythonProcess = app.isPackaged
    ? execFile(pythonExecutablePath, args)
    : spawn('python', [path.join(__dirname, 'slp2mp4', 'slp2mp4.py'), ...args]);

  pythonProcess.stdout.on('data', (data) => {
    event.reply('conversion-progress', data.toString());
  });

  pythonProcess.stderr.on('data', (data) => {
    event.reply('conversion-error', data.toString());
  });

  pythonProcess.on('close', (code) => {
    event.reply('conversion-complete', code);
  });
});

ipcMain.on('open-config', () => {
  createConfigWindow();
});

ipcMain.on('get-config', (event) => {
  fs.readFile(configPath, 'utf8', (err, data) => {
    if (err) {
      console.error("Error reading config file:", err);
      event.reply('config-data', {});
    } else {
      event.reply('config-data', JSON.parse(data));
    }
  });
});

ipcMain.on('save-config', (event, newConfig) => {
  fs.writeFile(configPath, JSON.stringify(newConfig, null, 2), (err) => {
    if (err) {
      console.error("Error writing config file:", err);
      event.reply('config-save-result', false);
    } else {
      event.reply('config-save-result', true);
    }
  });
});