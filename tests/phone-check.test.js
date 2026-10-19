/** @jest-environment jsdom */
const fs = require('fs');
const path = require('path');

// Use the real page markup so the tests can't drift from the template
const page = fs.readFileSync(path.join(__dirname, '../src/check/index.njk'), 'utf8')
  .replace(/^---[\s\S]*?---/, '')
  .replace(/\{\{[^}]*\}\}/g, '');

async function setup({ getUserMedia = jest.fn() } = {}) {
  document.body.innerHTML = page;
  Object.defineProperty(navigator, 'mediaDevices', { value: { getUserMedia }, configurable: true });
  jest.resetModules();
  require('../src/js/phone-check');
  document.dispatchEvent(new Event('DOMContentLoaded'));
  await flush();
}

const state = id => document.querySelector(`.check-row[data-check="${id}"]`).dataset.state;
const overall = () => document.getElementById('phone-check').dataset.state;
const flush = () => new Promise(r => setTimeout(r, 0));
const tapCamera = async () => { document.getElementById('camera-check-btn').click(); await flush(); };

afterEach(() => jest.restoreAllMocks());

test('camera waits for a tap while the other checks run on load', async () => {
  await setup();
  expect(state('camera')).toBe('pending');
  expect(state('storage')).toBe('pass');
  expect(state('browser')).toBe('pass');
  expect(overall()).toBe('pending');
});

test('allowing the camera lights every candle and shows the reveal', async () => {
  await setup({ getUserMedia: jest.fn().mockResolvedValue({ getTracks: () => [] }) });
  await tapCamera();
  expect(state('camera')).toBe('pass');
  expect(document.querySelectorAll('.check-candle[data-state="pass"]')).toHaveLength(3);
  expect(overall()).toBe('pass');
});

test('a blocked camera fails and shows its troubleshooting', async () => {
  await setup({ getUserMedia: jest.fn().mockRejectedValue(Object.assign(new Error('raw'), { name: 'NotAllowedError' })) });
  await tapCamera();
  expect(state('camera')).toBe('fail');
  expect(document.querySelector('.troubleshooting-group[data-check="camera"]').dataset.state).toBe('fail');
  expect(overall()).toBe('fail');
});

test('blocked storage fails', async () => {
  jest.spyOn(Storage.prototype, 'setItem').mockImplementation(() => { throw new Error('blocked'); });
  await setup();
  expect(state('storage')).toBe('fail');
});

test('browser check fails when a feature the game needs is missing', async () => {
  const flatMap = Array.prototype.flatMap;
  Array.prototype.flatMap = undefined;
  try {
    await setup();
    expect(state('browser')).toBe('fail');
  } finally {
    Array.prototype.flatMap = flatMap;
  }
});
