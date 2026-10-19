/**
 * Phone check page (/check/)
 * Each check decides pass or fail for itself, and render() writes the outcome
 * to the page as data-state attributes. A check's row, candle, button and
 * troubleshooting group share its data-check id; the section carries the
 * overall state. CSS decides what is visible.
 */
(function() {
'use strict';

// The values are the data-state attribute values the CSS matches on
const State = Object.freeze({ PENDING: 'pending', PASS: 'pass', FAIL: 'fail' });

// id: matches data-check in the template.
// run(): decides by calling this.pass() or this.fail(message); never touches the page.
// needsUserAction: the browser only shows the permission prompt after a tap.
// peek(): may call this.fail() if the answer is already known before the player does anything.
class Check {
  constructor({ id, run, needsUserAction = false, peek = () => Promise.resolve() }) {
    this.id = id;
    this.run = run;
    this.needsUserAction = needsUserAction;
    this.peek = peek;
    this.state = State.PENDING;
    this.errorMessage = '';
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
      this.fail('Your browser can\'t run the game. Update it, or open this page in Safari (iPhone) or Chrome (Android).');
    }
  }
});

const CAMERA_BLOCKED = 'Camera access was blocked. Allow it in your browser settings, then reload.';

function cameraErrorMessage(err) {
  if (err.name === 'NotAllowedError' || err.name === 'SecurityError') return CAMERA_BLOCKED;
  if (err.name === 'NotFoundError' || err.name === 'OverconstrainedError') return 'No camera found on this device.';
  return 'Couldn\'t start the camera. Try reloading, or open this page directly in Safari (iPhone) or Chrome (Android).';
}

const cameraCheck = new Check({
  id: 'camera',
  needsUserAction: true,
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
  },
  // Reads the browser's current permission each time, because iOS forgets grants between visits
  async peek() {
    if (!navigator.permissions || !navigator.permissions.query) return;
    try {
      const permission = await navigator.permissions.query({ name: 'camera' });
      if (permission.state === 'denied') this.fail(CAMERA_BLOCKED);
    } catch (e) {
      // Not every browser supports querying the camera permission; then the check just waits for the tap
    }
  }
});

const CHECKS = [cameraCheck, storageCheck, browserCheck];

function overallState() {
  if (CHECKS.some(check => check.state === State.FAIL)) return State.FAIL;
  return CHECKS.every(check => check.state === State.PASS) ? State.PASS : State.PENDING;
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

async function run(check) {
  await check.run();
  render();
}

// The page's scripts are deferred, so they have all run by DOMContentLoaded.
document.addEventListener('DOMContentLoaded', function() {
  const userActionChecks = CHECKS.filter(check => check.needsUserAction);

  CHECKS.filter(check => !check.needsUserAction).forEach(run);
  userActionChecks.forEach(check => check.peek().then(render));

  const btn = document.getElementById('camera-check-btn');
  btn.addEventListener('click', async () => {
    btn.disabled = true;
    await Promise.all(userActionChecks.map(run));
    btn.disabled = false;
  });
});

})();
