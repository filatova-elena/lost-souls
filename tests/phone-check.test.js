/** @jest-environment jsdom */
const fs = require('fs');
const path = require('path');

// Use the real page markup so the tests can't drift from the template
const page = fs.readFileSync(path.join(__dirname, '../src/check/index.njk'), 'utf8')
  .replace(/^---[\s\S]*?---/, '')
  .replace(/\{\{[^}]*\}\}/g, '')
  .replace(/\{%[^%]*%\}/g, '');

const STEP = 1200;
let getUserMedia;

function load() {
  document.body.innerHTML = page;
  Object.defineProperty(navigator, 'mediaDevices', { value: { getUserMedia }, configurable: true });

  // Capture the script's own listener so earlier loads can't also react
  const domReady = [];
  jest.spyOn(document, 'addEventListener').mockImplementation((type, fn) => {
    if (type === 'DOMContentLoaded') domReady.push(fn);
  });
  jest.resetModules();
  require('../src/js/phone-check');
  document.addEventListener.mockRestore();
  domReady.forEach(fn => fn());
}

const page_ = () => document.getElementById('phone-check');
const state = id => document.querySelector(`.check-row[data-check="${id}"]`).dataset.state;
const begin = () => document.getElementById('begin-btn').click();
const wait = ms => jest.advanceTimersByTimeAsync(ms);

beforeEach(() => {
  jest.useFakeTimers();
  getUserMedia = jest.fn().mockResolvedValue({ getTracks: () => [] });
  load();
});

afterEach(() => {
  jest.useRealTimers();
  jest.restoreAllMocks();
});

test('nothing runs until the begin button is pressed', async () => {
  await wait(STEP * 5);
  expect(page_().dataset.state).toBeUndefined();
  expect(getUserMedia).not.toHaveBeenCalled();

  begin();
  expect(page_().dataset.state).toBe('running');
  expect(state('browser')).toBe('running');
  expect(state('storage')).toBe('pending');
});

test('runs present, then memory, then camera, and only asks for the camera last', async () => {
  begin();
  await wait(STEP);
  expect(state('browser')).toBe('pass');
  expect(state('storage')).toBe('running');
  expect(getUserMedia).not.toHaveBeenCalled();

  await wait(STEP);
  expect(state('storage')).toBe('pass');
  expect(state('camera')).toBe('running');
  expect(getUserMedia).toHaveBeenCalledTimes(1);
});

test('when all three pass, every candle is lit and the page is done', async () => {
  begin();
  await wait(STEP * 3);
  expect(page_().dataset.state).toBe('pass');
  expect(document.querySelectorAll('.check-candle[data-state="pass"]')).toHaveLength(3);
});

test('the camera is released as soon as it has been checked', async () => {
  const stop = jest.fn();
  getUserMedia.mockResolvedValue({ getTracks: () => [{ stop }] });
  begin();
  await wait(STEP * 3);
  expect(stop).toHaveBeenCalledTimes(1);
});

test('a blocked camera fails and shows its troubleshooting', async () => {
  getUserMedia.mockRejectedValue(Object.assign(new Error('raw'), { name: 'NotAllowedError' }));
  begin();
  await wait(STEP * 3);
  expect(page_().dataset.state).toBe('fail');
  expect(state('camera')).toBe('fail');
  expect(document.querySelector('.troubleshooting-group[data-check="camera"]').dataset.state).toBe('fail');
});

test('stops at the first failure and never asks for the camera', async () => {
  jest.spyOn(Storage.prototype, 'setItem').mockImplementation(() => { throw new Error('blocked'); });
  begin();
  await wait(STEP * 5);
  expect(page_().dataset.state).toBe('fail');
  expect(state('storage')).toBe('fail');
  expect(state('camera')).toBe('pending');
  expect(getUserMedia).not.toHaveBeenCalled();
});

test('a browser missing a feature the game needs fails the first check', async () => {
  const flatMap = Array.prototype.flatMap;
  Array.prototype.flatMap = undefined;
  try {
    begin();
    await wait(STEP);
    expect(state('browser')).toBe('fail');
    expect(state('storage')).toBe('pending');
  } finally {
    Array.prototype.flatMap = flatMap;
  }
});
