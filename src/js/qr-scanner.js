(function() {
'use strict';

let scanner = null;
let overlay = null;
let closing = false;

function log(msg) {
  console.log('[QR Scanner] ' + msg + ' | scanner=' + !!scanner + ' overlay=' + !!overlay + ' closing=' + closing);
  // Show on screen for mobile debugging
  const hint = document.getElementById('qr-scanner-hint');
  if (hint) hint.textContent = msg;
}

// Handle back-forward cache: reset all state when page is restored
window.addEventListener('pageshow', function(e) {
  if (e.persisted) {
    log('Page restored from bfcache, resetting state');
    scanner = null;
    overlay = null;
    closing = false;
    // Remove any leftover overlay DOM
    const old = document.getElementById('qr-scanner-overlay');
    if (old) old.remove();
  }
});

function createOverlay() {
  overlay = document.createElement('div');
  overlay.id = 'qr-scanner-overlay';
  overlay.innerHTML = `
    <button id="qr-scanner-close" aria-label="Close scanner">&times;</button>
    <div id="qr-scanner-viewfinder">
      <div id="qr-scanner-reader"></div>
    </div>
    <p id="qr-scanner-hint">Point your camera at a purple QR code</p>
  `;
  document.body.appendChild(overlay);

  document.getElementById('qr-scanner-close').addEventListener('click', function() {
    closeScanner();
  });
  overlay.addEventListener('click', function(e) {
    if (e.target === overlay) closeScanner();
  });
}

function openScanner() {
  log('openScanner called');
  if (overlay || closing) {
    log('BLOCKED: overlay or closing is set');
    return;
  }
  if (typeof Html5Qrcode === 'undefined') {
    alert('Scanner library still loading... please try again in a second.');
    return;
  }
  createOverlay();

  const hint = document.getElementById('qr-scanner-hint');
  const viewfinder = document.getElementById('qr-scanner-viewfinder');
  if (hint) hint.textContent = 'Waiting for camera access...';
  if (viewfinder) viewfinder.style.display = 'none';

  scanner = new Html5Qrcode('qr-scanner-reader');
  log('scanner created, calling start()');

  scanner.start(
    { facingMode: 'environment' },
    { fps: 10, aspectRatio: 1.0 },
    onScanSuccess,
    () => {}
  ).then(() => {
    log('scanner started successfully');
    if (viewfinder) viewfinder.style.display = '';
    if (hint) hint.textContent = 'Point your camera at a purple QR code';
    try {
      const caps = scanner.getRunningTrackCameraCapabilities();
      const zoom = caps.zoomFeature();
      if (zoom.isSupported()) {
        zoom.apply(Math.min(2, zoom.max()));
        log('zoom applied');
      }
    } catch (e) {
      log('zoom not available: ' + e.message);
    }
  }).catch(err => {
    log('scanner start FAILED: ' + err);
    if (hint) hint.textContent = 'Unable to access camera. Please check permissions.';
  });
}

function onScanSuccess(decodedText) {
  log('onScanSuccess: ' + decodedText);
  if (closing || !scanner) {
    log('BLOCKED: closing or no scanner');
    return;
  }

  const hint = document.getElementById('qr-scanner-hint');
  if (hint) hint.textContent = 'Clue found! Opening...';

  closeScanner(function() {
    log('navigating to: ' + decodedText);
    window.location.href = decodedText;
  });
}

function stopAndCleanup() {
  log('stopAndCleanup');
  if (scanner) {
    const s = scanner;
    scanner = null;
    return s.stop().then(() => {
      log('scanner stopped');
      s.clear();
      log('scanner cleared');
    }).catch(err => {
      log('stop/clear error: ' + err);
    });
  }
  log('no scanner to stop');
  return Promise.resolve();
}

function closeScanner(callback) {
  log('closeScanner called');
  if (closing) {
    log('BLOCKED: already closing');
    return;
  }
  closing = true;

  stopAndCleanup().finally(() => {
    log('cleanup done, removing overlay');
    if (overlay) {
      overlay.remove();
      overlay = null;
    }
    closing = false;
    log('close complete');
    if (typeof callback === 'function') callback();
  });
}

function createScanButton() {
  const btn = document.createElement('button');
  btn.id = 'qr-scan-btn';
  btn.setAttribute('aria-label', 'Scan QR code');
  const grid = [
    '###.#.###',
    '#.#...#.#',
    '###.#.###',
    '....#....',
    '#.#.#.#..',
    '....#..#.',
    '###...#..',
    '#.#.#..#.',
    '###..#.##',
  ];
  const c = '#7B2D8E';
  let rects = '';
  grid.forEach((row, y) => {
    for (let x = 0; x < row.length; x++) {
      if (row[x] === '#') rects += `<rect x="${x}" y="${y}" width="1" height="1" fill="${c}"/>`;
    }
  });
  btn.innerHTML = `<svg viewBox="0 0 9 9" width="30" height="30" xmlns="http://www.w3.org/2000/svg" style="transform:rotate(45deg)">${rects}</svg>`;
  btn.addEventListener('click', openScanner);
  document.body.appendChild(btn);
}

document.addEventListener('DOMContentLoaded', createScanButton);
})();
