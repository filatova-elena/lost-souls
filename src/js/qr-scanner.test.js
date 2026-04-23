/**
 * QR Scanner lifecycle tests
 * Run with: node src/js/qr-scanner.test.js
 */

let testsPassed = 0;
let testsFailed = 0;

function assert(condition, msg) {
  if (!condition) {
    console.error('  FAIL: ' + msg);
    testsFailed++;
  } else {
    console.log('  PASS: ' + msg);
    testsPassed++;
  }
}

// Mock Html5Qrcode
class MockHtml5Qrcode {
  constructor(elementId) {
    this.elementId = elementId;
    this.running = false;
    this.cleared = false;
    this.stopCallCount = 0;
    this._onSuccess = null;
  }
  start(cameraConfig, scanConfig, onSuccess) {
    this._onSuccess = onSuccess;
    this.running = true;
    return Promise.resolve();
  }
  stop() {
    this.stopCallCount++;
    this.running = false;
    return Promise.resolve();
  }
  clear() {
    this.cleared = true;
  }
  getRunningTrackCameraCapabilities() {
    return { zoomFeature: () => ({ isSupported: () => false }) };
  }
  simulateScan(text) {
    if (this._onSuccess) this._onSuccess(text);
  }
}

// ============================================================================
// Core state machine (extracted from qr-scanner.js)
// ============================================================================

let scanner = null;
let overlay = null;
let closing = false;
let navigatedTo = null;

function resetState() {
  scanner = null;
  overlay = null;
  closing = false;
  navigatedTo = null;
}

function openScanner() {
  if (overlay || closing) return false;
  overlay = { id: 'qr-scanner-overlay' };
  scanner = new MockHtml5Qrcode('qr-scanner-reader');
  scanner.start({ facingMode: 'environment' }, { fps: 10 }, onScanSuccess);
  return true;
}

function onScanSuccess(decodedText) {
  if (closing || !scanner) return;
  closeScanner(function() {
    navigatedTo = decodedText;
  });
}

function stopAndCleanup() {
  if (scanner) {
    const s = scanner;
    scanner = null;
    return s.stop().then(() => s.clear()).catch(() => {});
  }
  return Promise.resolve();
}

function closeScanner(callback) {
  if (closing) return;
  closing = true;
  stopAndCleanup().finally(() => {
    if (overlay) overlay = null;
    closing = false;
    if (typeof callback === 'function') callback();
  });
}

// ============================================================================
// Tests
// ============================================================================

async function runTests() {
  console.log('\n=== QR Scanner Lifecycle Tests ===\n');

  // Test 1: Basic open
  console.log('Test 1: Open scanner');
  resetState();
  assert(openScanner() === true, 'opens successfully');
  assert(scanner !== null, 'scanner created');
  assert(overlay !== null, 'overlay created');
  await Promise.resolve();
  assert(scanner.running === true, 'scanner running');

  // Test 2: Cannot double-open
  console.log('\nTest 2: Cannot double-open');
  assert(openScanner() === false, 'second open blocked');

  // Test 3: Close scanner, verify full cleanup
  console.log('\nTest 3: Close scanner');
  resetState();
  openScanner();
  await Promise.resolve();
  const ref3 = scanner;
  closeScanner();
  await new Promise(r => setTimeout(r, 10));
  assert(scanner === null, 'scanner null');
  assert(overlay === null, 'overlay null');
  assert(closing === false, 'closing false');
  assert(ref3.stopCallCount === 1, 'stop called once');
  assert(ref3.cleared === true, 'clear called');
  assert(ref3.running === false, 'not running');

  // Test 4: Reopen after close
  console.log('\nTest 4: Reopen after close');
  assert(openScanner() === true, 'reopens after close');
  assert(scanner !== null, 'new scanner');

  // Test 5: Scan success -> cleanup -> navigate
  console.log('\nTest 5: Scan success full lifecycle');
  resetState();
  openScanner();
  await Promise.resolve();
  const ref5 = scanner;
  ref5.simulateScan('https://example.com/clues/AO79/');
  await new Promise(r => setTimeout(r, 10));
  assert(scanner === null, 'scanner null after scan');
  assert(overlay === null, 'overlay null after scan');
  assert(closing === false, 'closing false after scan');
  assert(ref5.stopCallCount === 1, 'stop called');
  assert(ref5.cleared === true, 'clear called');
  assert(navigatedTo === 'https://example.com/clues/AO79/', 'navigated correctly');

  // Test 6: Reopen after scan success
  console.log('\nTest 6: Reopen after scan success');
  assert(openScanner() === true, 'reopens after scan');

  // Test 7: Blocked during closing
  console.log('\nTest 7: Blocked during closing');
  resetState();
  openScanner();
  await Promise.resolve();
  closing = true;
  assert(openScanner() === false, 'blocked while closing');

  // Test 8: onScanSuccess with no scanner
  console.log('\nTest 8: onScanSuccess ignored without scanner');
  resetState();
  navigatedTo = null;
  onScanSuccess('https://example.com');
  await new Promise(r => setTimeout(r, 10));
  assert(navigatedTo === null, 'no navigation');

  // Test 9: onScanSuccess ignored while closing
  console.log('\nTest 9: onScanSuccess ignored while closing');
  resetState();
  openScanner();
  await Promise.resolve();
  closing = true;
  navigatedTo = null;
  scanner.simulateScan('https://example.com');
  await new Promise(r => setTimeout(r, 10));
  assert(navigatedTo === null, 'no navigation while closing');

  // Test 10: stop() rejects - still cleans up
  console.log('\nTest 10: Cleanup after stop() rejects');
  resetState();
  openScanner();
  await Promise.resolve();
  scanner.stop = () => Promise.reject(new Error('camera busy'));
  closeScanner();
  await new Promise(r => setTimeout(r, 10));
  assert(scanner === null, 'scanner null after failed stop');
  assert(overlay === null, 'overlay null after failed stop');
  assert(closing === false, 'closing false after failed stop');

  // Test 11: Reopen after failed stop
  console.log('\nTest 11: Reopen after failed stop');
  assert(openScanner() === true, 'reopens after failed stop');

  // Test 12: Slow stop - state correct during and after
  console.log('\nTest 12: Slow stop');
  resetState();
  openScanner();
  await Promise.resolve();
  scanner.stop = () => new Promise(r => setTimeout(r, 50));
  scanner.simulateScan('https://example.com/slow/');
  assert(closing === true, 'closing during slow stop');
  assert(navigatedTo === null, 'not navigated yet');
  assert(openScanner() === false, 'blocked during slow stop');
  await new Promise(r => setTimeout(r, 100));
  assert(closing === false, 'closing false after slow stop');
  assert(navigatedTo === 'https://example.com/slow/', 'navigated after slow stop');
  assert(overlay === null, 'overlay null after slow stop');

  // Test 13: Reopen after slow stop
  console.log('\nTest 13: Reopen after slow stop');
  assert(openScanner() === true, 'reopens after slow stop');

  // Test 14: Multiple rapid scans - only first processes
  // The library holds its own callback reference, so it could fire multiple times
  console.log('\nTest 14: Multiple rapid scans');
  resetState();
  openScanner();
  await Promise.resolve();
  navigatedTo = null;
  const savedCallback = scanner._onSuccess; // library's internal ref
  savedCallback('https://first.com');
  savedCallback('https://second.com'); // library fires again before stop completes
  savedCallback('https://third.com');
  await new Promise(r => setTimeout(r, 10));
  assert(navigatedTo === 'https://first.com', 'only first scan navigates');

  // Summary
  console.log('\n=== Results ===');
  console.log(`${testsPassed} passed, ${testsFailed} failed`);
  if (testsFailed > 0) process.exit(1);
}

runTests();
