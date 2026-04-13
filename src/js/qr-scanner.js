(function() {
'use strict';

let scanner = null;
let overlay = null;

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

  document.getElementById('qr-scanner-close').addEventListener('click', closeScanner);
  // Also close on tap anywhere on the overlay background
  overlay.addEventListener('click', function(e) {
    if (e.target === overlay) closeScanner();
  });
}

function openScanner() {
  if (overlay) return;
  createOverlay();

  const hint = document.getElementById('qr-scanner-hint');
  const viewfinder = document.getElementById('qr-scanner-viewfinder');
  if (hint) hint.textContent = 'Waiting for camera access...';
  if (viewfinder) viewfinder.style.display = 'none';

  scanner = new Html5Qrcode('qr-scanner-reader');
  scanner.start(
    { facingMode: 'environment' },
    {
      fps: 10,
      aspectRatio: 1.0
    },
    onScanSuccess,
    () => {}
  ).then(() => {
    if (viewfinder) viewfinder.style.display = '';
    if (hint) hint.textContent = 'Point your camera at a purple QR code';
  }).catch(err => {
    console.error('QR scanner error:', err);
    if (hint) hint.textContent = 'Unable to access camera. Please check permissions.';
  });
}

function onScanSuccess(decodedText) {
  // Only navigate if it looks like a URL for our site
  if (decodedText.startsWith('http')) {
    closeScanner();
    window.location.href = decodedText;
  }
}

function closeScanner() {
  const s = scanner;
  scanner = null;
  if (overlay) {
    overlay.remove();
    overlay = null;
  }
  if (s) {
    s.stop().then(() => {
      s.clear();
    }).catch(() => {});
  }
}

function createScanButton() {
  const btn = document.createElement('button');
  btn.id = 'qr-scan-btn';
  btn.setAttribute('aria-label', 'Scan QR code');
  // QR icon: exact pixel grid from reference, then rotated
  // Each character = 1 cell. # = filled, . = empty
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
