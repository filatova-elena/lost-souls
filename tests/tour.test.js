/** @jest-environment jsdom */
const fs = require('fs');
const path = require('path');

const stored = {};

function load(markup = defaultMarkup) {
  document.body.innerHTML = markup;
  Object.keys(stored).forEach(key => delete stored[key]);
  window.getFromLocalStorage = (key, fallback) => (key in stored ? stored[key] : fallback);
  window.saveToLocalStorage = (key, value) => { stored[key] = value; };
  jest.resetModules();
  require('../src/js/tour');
}

const defaultMarkup = `
  <button id="qr-scan-btn"></button>
  <div class="progress-tracker"><a class="progress-history"></a></div>
`;

const tour = () => document.querySelector('.tour');
const text = () => document.querySelector('.tour-text').textContent;
const count = () => document.querySelector('.tour-count').textContent;
const next = () => document.querySelector('.tour-next');
const skip = () => document.querySelector('.tour-skip');
const press = key => document.dispatchEvent(new KeyboardEvent('keydown', { key }));

afterEach(() => {
  if (tour()) press('Escape');
  jest.restoreAllMocks();
});

test('starts on the scan button', () => {
  load();
  window.startTour();
  expect(count()).toBe('1 / 3');
  expect(text()).toContain('scan a QR code');
  expect(next().textContent).toBe('Next');
});

test('goes on to the status bar and then the history button, which ends with Got it', () => {
  load();
  window.startTour();
  next().click();
  expect(count()).toBe('2 / 3');
  expect(text()).toContain('Your character');
  next().click();
  expect(count()).toBe('3 / 3');
  expect(text()).toContain('clue you’ve found');
  expect(next().textContent).toBe('Got it');
  expect(tour().dataset.last).toBe('true');
});

test('Got it ends the tour and remembers it was seen', () => {
  load();
  window.startTour();
  next().click();
  next().click();
  next().click();
  expect(tour()).toBeNull();
  expect(stored.tour_seen).toBe(true);
});

test('Skip ends the tour from any step and remembers it was seen', () => {
  load();
  window.startTour();
  next().click();
  skip().click();
  expect(tour()).toBeNull();
  expect(stored.tour_seen).toBe(true);
});

test('Escape ends the tour and remembers it was seen', () => {
  load();
  window.startTour();
  press('Escape');
  expect(tour()).toBeNull();
  expect(stored.tour_seen).toBe(true);
});

test('tapping the dimmed screen does not end the tour', () => {
  load();
  window.startTour();
  tour().click();
  expect(tour()).not.toBeNull();
  expect(stored.tour_seen).toBeUndefined();
});

test('shows only once', () => {
  load();
  window.startTour();
  press('Escape');
  window.startTour();
  expect(tour()).toBeNull();
});

test('stops listening for resizes and keys once it has ended', () => {
  load();
  const removeWindow = jest.spyOn(window, 'removeEventListener');
  const removeDocument = jest.spyOn(document, 'removeEventListener');
  window.startTour();
  press('Escape');
  expect(removeWindow).toHaveBeenCalledWith('resize', expect.any(Function));
  expect(removeDocument).toHaveBeenCalledWith('keydown', expect.any(Function));
});

test('leaves out a step whose target is not on the page', () => {
  load('<button id="qr-scan-btn"></button><div class="progress-tracker"></div>');
  window.startTour();
  expect(count()).toBe('1 / 2');
  next().click();
  expect(count()).toBe('2 / 2');
  expect(next().textContent).toBe('Got it');
});

test('does nothing when none of its targets are on the page', () => {
  load('<p>nothing here</p>');
  window.startTour();
  expect(tour()).toBeNull();
  expect(stored.tour_seen).toBeUndefined();
});

test('the real status bar still has everything the tour points at', () => {
  const tracker = fs.readFileSync(path.join(__dirname, '../src/_includes/clues/progress-tracker.njk'), 'utf8');
  expect(tracker).toContain('id="qr-scan-btn"');
  expect(tracker).toContain('class="progress-tracker"');
  expect(tracker).toContain('class="progress-history"');
});

describe('the Begin investigation animation', () => {
  beforeEach(() => jest.useFakeTimers());
  afterEach(() => jest.useRealTimers());

  test('tells the caller when it has closed, once', () => {
    document.body.innerHTML = '';
    jest.resetModules();
    require('../src/js/effects');
    let overlayWhenCalled;
    const onClosed = jest.fn(() => { overlayWhenCalled = document.getElementById('typewriterOverlay'); });
    window.renderTypewriterAnimation('Ada', 'You are now investigating as', 'Ready', onClosed);

    jest.advanceTimersByTime(500);
    expect(onClosed).not.toHaveBeenCalled();

    jest.advanceTimersByTime(15000);
    expect(document.getElementById('typewriterOverlay')).toBeNull();
    expect(onClosed).toHaveBeenCalledTimes(1);
    expect(overlayWhenCalled).toBeNull();
  });
});
