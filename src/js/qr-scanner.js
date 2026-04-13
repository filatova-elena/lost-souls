(function() {
'use strict';

let scanner = null;
let overlay = null;
let closing = false;

// Handle back-forward cache: reset all state when page is restored
window.addEventListener('pageshow', function(e) {
  if (e.persisted) {
    scanner = null;
    overlay = null;
    closing = false;
    var old = document.getElementById('qr-scanner-overlay');
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
  if (overlay || closing) return;
  if (typeof Html5Qrcode === 'undefined') {
    alert('Scanner library still loading... please try again in a second.');
    return;
  }
  createOverlay();

  var hint = document.getElementById('qr-scanner-hint');
  var viewfinder = document.getElementById('qr-scanner-viewfinder');
  if (hint) hint.textContent = 'Waiting for camera access...';
  if (viewfinder) viewfinder.style.display = 'none';

  scanner = new Html5Qrcode('qr-scanner-reader');
  scanner.start(
    { facingMode: 'environment' },
    { fps: 10, aspectRatio: 1.0 },
    onScanSuccess,
    function() {}
  ).then(function() {
    if (viewfinder) viewfinder.style.display = '';
    if (hint) hint.textContent = 'Point your camera at a purple QR code';
    try {
      var caps = scanner.getRunningTrackCameraCapabilities();
      var zoom = caps.zoomFeature();
      if (zoom.isSupported()) {
        zoom.apply(Math.min(2, zoom.max()));
      }
    } catch (e) {}
  }).catch(function(err) {
    console.error('QR scanner error:', err);
    if (hint) hint.textContent = 'Unable to access camera. Please check permissions.';
  });
}

function onScanSuccess(decodedText) {
  if (closing || !scanner) return;

  var hint = document.getElementById('qr-scanner-hint');
  if (hint) hint.textContent = 'Clue found! Opening...';

  closeScanner(function() {
    window.location.href = decodedText;
  });
}

function stopAndCleanup() {
  if (scanner) {
    var s = scanner;
    scanner = null;
    return s.stop().then(function() { s.clear(); }).catch(function() {});
  }
  return Promise.resolve();
}

function closeScanner(callback) {
  if (closing) return;
  closing = true;

  stopAndCleanup().finally(function() {
    if (overlay) {
      overlay.remove();
      overlay = null;
    }
    closing = false;
    if (typeof callback === 'function') callback();
  });
}

function createScanButton() {
  var btn = document.createElement('button');
  btn.id = 'qr-scan-btn';
  btn.setAttribute('aria-label', 'Scan QR code');
  var grid = [
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
  var c = '#7B2D8E';
  var rects = '';
  grid.forEach(function(row, y) {
    for (var x = 0; x < row.length; x++) {
      if (row[x] === '#') rects += '<rect x="'+x+'" y="'+y+'" width="1" height="1" fill="'+c+'"/>';
    }
  });
  btn.innerHTML = '<svg viewBox="0 0 9 9" width="30" height="30" xmlns="http://www.w3.org/2000/svg" style="transform:rotate(45deg)">'+rects+'</svg>';
  btn.addEventListener('click', openScanner);
  document.body.appendChild(btn);
}

document.addEventListener('DOMContentLoaded', createScanButton);
})();
