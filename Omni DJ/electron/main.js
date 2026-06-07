'use strict';
// SESSIE 77 - B0 + B1: Electron-wrapper rond de bestaande Flask-backend (sidecar).
// De analyse blijft 100% lokaal. B0 = prototype (UI + analyse + export in een
// venster). B1 (deze versie) voegt lifecycle-hardening toe:
//   - robuuste process-tree-kill (detached spawn + groep-kill) zodat er geen
//     zombie python/ffmpeg achterblijft bij afsluiten;
//   - een macOS application-menu met de standaard Cmd-shortcuts (Q/C/V/R, ...);
//   - nette shutdown op SIGINT/SIGTERM;
//   - veilige link-afhandeling (externe links in de standaardbrowser, geen
//     wegnavigatie uit de lokale backend).
// NOG NIET in B1: de sidecar uit de PyInstaller-build (we starten de dev-venv) en
// finish-notificatie/Dock-progress (vereisen renderer->main IPC) -> B1b/B2.

const { app, BrowserWindow, Menu, shell } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const http = require('http');
const net = require('net');
const fs = require('fs');

// electron/ zit IN de app-map (.../Omni DJ/Omni DJ/electron); de app-root is een
// niveau hoger. Overschrijfbaar via env voor een PyInstaller-sidecar (B1b/B2).
const APP_DIR = path.join(__dirname, '..');
const PY = process.env.OMNI_DJ_PYTHON || path.join(APP_DIR, 'venv', 'bin', 'python3');
const APP_PY = process.env.OMNI_DJ_APP || path.join(APP_DIR, 'app.py');
const FFMPEG_DIR = path.join(APP_DIR, 'vendor', 'ffmpeg');

// SESSIE 78 - B1b: kies de backend. In een gepackagede build (electron-builder)
// is de PyInstaller-backend als extraResource "backend" meegebundeld; we draaien
// dan die binary HEADLESS (geen browser-open). In dev valt het terug op de
// venv-python + app.py (B0/B1-gedrag). Override-volgorde:
//   1) OMNI_DJ_BACKEND  = absoluut pad naar de gebouwde backend-executable
//   2) gepackaged       = <resources>/backend/Omni DJ.app/Contents/MacOS/Omni DJ
//                         of <resources>/backend/Omni DJ (onedir-layout)
//   3) dev              = venv python + app.py
function resolveBackend() {
  const override = process.env.OMNI_DJ_BACKEND;
  if (override && fs.existsSync(override)) {
    return { mode: 'sidecar', exe: override };
  }
  if (app.isPackaged) {
    const res = process.resourcesPath;
    const candidates = [
      path.join(res, 'backend', 'Omni DJ.app', 'Contents', 'MacOS', 'Omni DJ'),
      path.join(res, 'backend', 'Omni DJ'),
      path.join(res, 'backend', 'Omni DJ.exe'),
    ];
    for (const c of candidates) {
      if (fs.existsSync(c)) return { mode: 'sidecar', exe: c };
    }
  }
  return { mode: 'dev', py: PY, appPy: APP_PY };
}

app.setName('Omni DJ');

let backend = null;
let backendPid = null;   // pid == process-group id (detached spawn) voor tree-kill
let win = null;
let appOrigin = null;    // http://127.0.0.1:<port> zodra de poort bekend is

function freePort() {
  return new Promise((resolve, reject) => {
    const srv = net.createServer();
    srv.unref();
    srv.on('error', reject);
    srv.listen(0, '127.0.0.1', () => {
      const p = srv.address().port;
      srv.close(() => resolve(p));
    });
  });
}

function startBackend(port) {
  const b = resolveBackend();
  const env = Object.assign({}, process.env, {
    OMNI_DJ_PORT: String(port),
    // Headless: de sidecar/launcher mag GEEN browser openen; Electron laadt de UI
    // zelf in het venster. In dev (app.py direct) is dit een no-op.
    OMNI_DJ_NO_BROWSER: '1',
    // Zorg dat de (dev) gebundelde static ffmpeg/ffprobe gevonden worden. In de
    // gepackagede backend lost media_tools de binaries zelf op uit Resources/bin.
    PATH: FFMPEG_DIR + path.delimiter + (process.env.PATH || ''),
  });
  let cmd, args, cwd;
  if (b.mode === 'sidecar') {
    cmd = b.exe;
    args = [String(port)];
    cwd = path.dirname(b.exe);   // launcher chdir't zelf naar _MEIPASS; dit is enkel veilig
    console.log('[omnidj] backend = packaged sidecar:', b.exe);
  } else {
    cmd = b.py;
    args = [b.appPy, String(port)];
    cwd = APP_DIR;
    console.log('[omnidj] backend = dev venv:', b.py, b.appPy);
  }
  // detached: true -> de child wordt groepsleider (setsid), zodat we bij het
  // afsluiten de HELE boom (python/sidecar + ffmpeg-children) in een keer killen.
  backend = spawn(cmd, args, { cwd, env, stdio: 'inherit', detached: true });
  backendPid = backend.pid;
  backend.on('exit', (code) => { console.log('[omnidj] backend exited with', code); backend = null; });
  backend.on('error', (e) => console.error('[omnidj] backend spawn error:', e));
}

// Robuuste tree-kill: stuur SIGTERM naar de hele process-groep (negatief pid),
// en na een korte gratie SIGKILL als er nog iets leeft. Voorkomt zombie-python
// en achtergebleven ffmpeg-processen.
function killBackend() {
  if (!backend || !backendPid) { backend = null; return; }
  const pgid = backendPid;
  try {
    process.kill(-pgid, 'SIGTERM');
  } catch (_e) {
    try { backend.kill('SIGTERM'); } catch (_x) {}
  }
  setTimeout(() => {
    try { process.kill(-pgid, 'SIGKILL'); } catch (_e) {}
  }, 1500);
  backend = null;
}

function waitForHealth(port, timeoutMs) {
  const url = 'http://127.0.0.1:' + port + '/';
  const deadline = Date.now() + (timeoutMs || 90000);
  return new Promise((resolve, reject) => {
    (function poll() {
      const req = http.get(url, (res) => {
        res.resume();
        // Elke niet-5xx respons betekent: Flask is op en bedient de route.
        if (res.statusCode && res.statusCode < 500) return resolve();
        retry();
      });
      req.on('error', retry);
      req.setTimeout(2000, () => { req.destroy(); retry(); });
      function retry() {
        if (Date.now() > deadline) return reject(new Error('backend health-check timeout'));
        setTimeout(poll, 500);
      }
    })();
  });
}

function buildMenu() {
  const isMac = process.platform === 'darwin';
  const template = [];
  if (isMac) {
    template.push({
      label: app.name,
      submenu: [
        { role: 'about' },
        { type: 'separator' },
        { role: 'hide' }, { role: 'hideOthers' }, { role: 'unhide' },
        { type: 'separator' },
        { role: 'quit' },
      ],
    });
  }
  template.push({
    label: 'Edit',
    submenu: [
      { role: 'undo' }, { role: 'redo' }, { type: 'separator' },
      { role: 'cut' }, { role: 'copy' }, { role: 'paste' }, { role: 'selectAll' },
    ],
  });
  template.push({
    label: 'View',
    submenu: [
      { role: 'reload' }, { role: 'forceReload' }, { role: 'toggleDevTools' },
      { type: 'separator' },
      { role: 'resetZoom' }, { role: 'zoomIn' }, { role: 'zoomOut' },
      { type: 'separator' },
      { role: 'togglefullscreen' },
    ],
  });
  template.push({
    label: 'Window',
    submenu: isMac
      ? [{ role: 'minimize' }, { role: 'zoom' }, { type: 'separator' }, { role: 'front' }]
      : [{ role: 'minimize' }, { role: 'zoom' }, { role: 'close' }],
  });
  return Menu.buildFromTemplate(template);
}

// Veilige link-afhandeling: externe http(s)-links openen in de standaardbrowser,
// nooit in het app-venster; wegnavigeren van de lokale backend blokkeren.
function applyNavigationGuard(contents) {
  contents.setWindowOpenHandler(({ url }) => {
    if (/^https?:/i.test(url)) shell.openExternal(url);
    return { action: 'deny' };
  });
  contents.on('will-navigate', (event, url) => {
    if (appOrigin && url.startsWith(appOrigin)) return;   // interne navigatie OK
    event.preventDefault();
    if (/^https?:/i.test(url)) shell.openExternal(url);
  });
}

async function boot() {
  win = new BrowserWindow({
    width: 1440,
    height: 900,
    minWidth: 980,
    minHeight: 640,
    backgroundColor: '#0f0f10',
    show: true,
    title: 'Omni DJ',
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      preload: path.join(__dirname, 'preload.js'),
    },
  });
  applyNavigationGuard(win.webContents);
  win.loadFile(path.join(__dirname, 'splash.html'));

  try {
    const port = await freePort();
    appOrigin = 'http://127.0.0.1:' + port;
    startBackend(port);
    await waitForHealth(port, 90000);
    await win.loadURL(appOrigin + '/');
  } catch (e) {
    console.error('[omnidj] boot failed:', e);
    if (win) win.loadFile(path.join(__dirname, 'splash.html'), { hash: 'error' });
  }
}

app.whenReady().then(() => {
  // SESSIE 80: in dev (npm start) toont het Dock anders het generieke
  // Electron-icoon. De gepackagede app krijgt het icoon al uit de bundle
  // (build/icon.icns), dus daar doen we niets. De Dock-NAAM blijft in dev
  // "Electron" (komt uit de Electron.app-bundle zelf, niet aanpasbaar).
  if (!app.isPackaged && process.platform === 'darwin' && app.dock) {
    try { app.dock.setIcon(path.join(APP_DIR, 'static', 'icon_1024.png')); } catch (_e) {}
  }
  Menu.setApplicationMenu(buildMenu());
  boot();
});

// Eén-venster-utility: het venster sluiten = de app afsluiten = de backend stoppen.
app.on('window-all-closed', () => { app.quit(); });
app.on('before-quit', killBackend);
app.on('will-quit', killBackend);
app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) boot();
});

// Nette shutdown als het hoofdproces een signaal krijgt (bv. Ctrl-C in de terminal).
['SIGINT', 'SIGTERM'].forEach((sig) => {
  process.on(sig, () => { killBackend(); app.quit(); });
});
