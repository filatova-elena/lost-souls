/**
 * Phone check page (/check/)
 * Pressing the begin button runs the checks one after another, each shown as it
 * starts. Each check decides pass or fail for itself, and render() writes the
 * outcome to the page as data-state attributes. A check's row, candle and
 * troubleshooting group share its data-check id; the page carries the overall
 * state. CSS decides what is visible.
 */
(function() {
'use strict';

// The values are the data-state attribute values the CSS matches on
const State = Object.freeze({ PENDING: 'pending', RUNNING: 'running', PASS: 'pass', FAIL: 'fail' });

// Each check stays on screen at least this long, so the sequence can be followed
const STEP_MS = 1200;

// id: matches data-check in the template.
// run(): decides by calling this.pass() or this.fail(message); never touches the page.
class Check {
  constructor({ id, run }) {
    this.id = id;
    this.run = run;
    this.state = State.PENDING;
    this.errorMessage = '';
  }

  start() {
    this.state = State.RUNNING;
  }

  pass() {
    this.state = State.PASS;
    this.errorMessage = '';
  }

  fail(message) {
    this.state = State.FAIL;
    this.errorMessage = message;
  }
}

const browserCheck = new Check({
  id: 'browser',
  // The game's scripts use optional chaining (?.) and flatMap, so a browser
  // that can't handle them can't run the game. Syntax can only be probed by parsing it.
  run() {
    let canRunGame = typeof Array.prototype.flatMap === 'function';
    try {
      new Function('return ({})?.a');
    } catch (e) {
      canRunGame = false;
    }
    if (canRunGame) {
      this.pass();
    } else {
      this.fail('This browser can\'t run the game. Try Safari (iPhone) or Chrome (Android).');
    }
  }
});

const storageCheck = new Check({
  id: 'storage',
  run() {
    try {
      localStorage.setItem('__storage_test__', '1');
      localStorage.removeItem('__storage_test__');
      this.pass();
    } catch (e) {
      this.fail('Local storage is blocked or unavailable. This may happen in Private/Incognito mode. Your progress will not be saved.');
    }
  }
});

function cameraErrorMessage(err) {
  if (err.name === 'NotAllowedError' || err.name === 'SecurityError') {
    return 'Camera access was blocked. Allow it in your browser settings, then reload.';
  }
  if (err.name === 'NotFoundError' || err.name === 'OverconstrainedError') return 'No camera found on this device.';
  return 'Couldn\'t start the camera. Try reloading, or open this page directly in Safari (iPhone) or Chrome (Android).';
}

const cameraCheck = new Check({
  id: 'camera',
  async run() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      this.fail('This browser can\'t access the camera. Try Safari (iPhone) or Chrome (Android), and open the link outside of email or social apps.');
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
      stream.getTracks().forEach(track => track.stop());
      this.pass();
    } catch (err) {
      this.fail(cameraErrorMessage(err));
    }
  }
});

// In the order they are shown
const CHECKS = [browserCheck, storageCheck, cameraCheck];

function overallState() {
  if (CHECKS.some(check => check.state === State.FAIL)) return State.FAIL;
  return CHECKS.every(check => check.state === State.PASS) ? State.PASS : State.RUNNING;
}

function render() {
  CHECKS.forEach(check => {
    document.querySelectorAll(`[data-check="${check.id}"]`).forEach(el => {
      el.dataset.state = check.state;
    });
    document.querySelector(`[data-check="${check.id}"] [data-error]`).textContent = check.errorMessage;
  });

  document.getElementById('phone-check').dataset.state = overallState();
}

const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

// Stops at the first failure
async function runChecks() {
  for (const check of CHECKS) {
    check.start();
    render();
    await Promise.all([check.run(), sleep(STEP_MS)]);
    render();
    if (check.state === State.FAIL) return;
  }
}

// The page's scripts are deferred, so they have all run by DOMContentLoaded.
document.addEventListener('DOMContentLoaded', function() {
  document.getElementById('begin-btn').addEventListener('click', runChecks, { once: true });
});

})();
