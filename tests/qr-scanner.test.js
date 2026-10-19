/** @jest-environment jsdom */

// Loads the real src/js/qr-scanner.js and drives it through the DOM.
// Only the camera library (Html5Qrcode) is faked.

let scanners;
let stopBehavior;

class FakeHtml5Qrcode {
  constructor(elementId) {
    this.elementId = elementId;
    this.stopCalls = 0;
    this.cleared = false;
    scanners.push(this);
  }

  start(cameraConfig, scanConfig, onSuccess) {
    this.cameraConfig = cameraConfig;
    this.onSuccess = onSuccess;
    return FakeHtml5Qrcode.startResult();
  }

  stop() {
    this.stopCalls++;
    return stopBehavior();
  }

  clear() {
    this.cleared = true;
  }

  getRunningTrackCameraCapabilities() {
    throw new Error('no zoom');
  }
}

function load() {
  document.body.innerHTML = '<button id="qr-scan-btn"></button>';
  window.location.hash = '';

  // Capture the module's own listeners so earlier loads can't also react
  const domReady = [];
  jest.spyOn(document, 'addEventListener').mockImplementation((type, fn) => {
    if (type === 'DOMContentLoaded') domReady.push(fn);
  });
  jest.resetModules();
  require('../src/js/qr-scanner');
  document.addEventListener.mockRestore();
  domReady.forEach(fn => fn());
}

const flush = () => new Promise(resolve => setTimeout(resolve, 0));
const overlay = () => document.getElementById('qr-scanner-overlay');
const open = () => document.getElementById('qr-scan-btn').click();
const close = async () => { document.getElementById('qr-scanner-close').click(); await flush(); };
const scan = async text => { scanners[scanners.length - 1].onSuccess(text); await flush(); };

beforeEach(() => {
  scanners = [];
  stopBehavior = () => Promise.resolve();
  FakeHtml5Qrcode.startResult = () => Promise.resolve();
  window.Html5Qrcode = FakeHtml5Qrcode;
  jest.spyOn(console, 'error').mockImplementation(() => {});
  load();
});

afterEach(() => jest.restoreAllMocks());

test('the scan button opens the scanner on the back camera', () => {
  open();
  expect(overlay()).not.toBeNull();
  expect(scanners).toHaveLength(1);
  expect(scanners[0].elementId).toBe('qr-scanner-reader');
  expect(scanners[0].cameraConfig).toEqual({ facingMode: 'environment' });
});

test('opening twice does not stack a second scanner', () => {
  open();
  open();
  expect(document.querySelectorAll('#qr-scanner-overlay')).toHaveLength(1);
  expect(scanners).toHaveLength(1);
});

test('the close button stops the camera, removes the overlay, and the scanner can reopen', async () => {
  open();
  await close();
  expect(scanners[0].stopCalls).toBe(1);
  expect(scanners[0].cleared).toBe(true);
  expect(overlay()).toBeNull();

  open();
  expect(overlay()).not.toBeNull();
  expect(scanners).toHaveLength(2);
});

test('a scanned code closes the scanner and opens that address', async () => {
  open();
  await scan('#clue-AO100');
  expect(scanners[0].stopCalls).toBe(1);
  expect(overlay()).toBeNull();
  expect(window.location.hash).toBe('#clue-AO100');
});

test('repeated scans of the same frame navigate once', async () => {
  open();
  const { onSuccess } = scanners[0];
  onSuccess('#first');
  onSuccess('#second');
  onSuccess('#third');
  await flush();
  expect(scanners[0].stopCalls).toBe(1);
  expect(window.location.hash).toBe('#first');
});

test('while a slow stop is in progress, the scan button and further scans do nothing', async () => {
  let finishStop;
  stopBehavior = () => new Promise(resolve => { finishStop = resolve; });
  open();
  document.getElementById('qr-scanner-close').click();

  open();
  scanners[0].onSuccess('#late');
  expect(scanners).toHaveLength(1);

  finishStop();
  await flush();
  expect(overlay()).toBeNull();
  expect(window.location.hash).toBe('');
});

test('pressing close twice while the camera is still stopping leaves the overlay until it has stopped', async () => {
  let finishStop;
  stopBehavior = () => new Promise(resolve => { finishStop = resolve; });
  open();
  document.getElementById('qr-scanner-close').click();
  document.getElementById('qr-scanner-close').click();
  await flush();
  expect(overlay()).not.toBeNull();
  expect(scanners[0].stopCalls).toBe(1);

  finishStop();
  await flush();
  expect(overlay()).toBeNull();
});

test('a rejected stop() still removes the overlay and allows reopening', async () => {
  stopBehavior = () => Promise.reject('stop failed');
  open();
  await close();
  expect(overlay()).toBeNull();
  open();
  expect(overlay()).not.toBeNull();
});

test('a stop() that throws synchronously still removes the overlay and allows reopening', async () => {
  // The real library throws a bare string when the camera never started
  stopBehavior = () => { throw 'scanner is not running'; };
  open();
  await close();
  expect(overlay()).toBeNull();
  open();
  expect(overlay()).not.toBeNull();
});

test('after the camera permission is denied, the player can still close the scanner', async () => {
  FakeHtml5Qrcode.startResult = () => Promise.reject(new Error('Permission denied'));
  stopBehavior = () => { throw 'scanner is not running'; };
  open();
  await flush();
  expect(document.getElementById('qr-scanner-hint').textContent).toContain('Unable to access camera');

  await close();
  expect(overlay()).toBeNull();
  open();
  expect(overlay()).not.toBeNull();
});
