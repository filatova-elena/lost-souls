/** @jest-environment jsdom */
const fs = require('fs');
const path = require('path');

// Use the real page markup so the tests can't drift from the template
const page = fs.readFileSync(path.join(__dirname, '../src/history/index.njk'), 'utf8')
  .replace(/^---[\s\S]*?---/, '')
  .replace(/\{\{[^}]*\}\}/g, '');

function load(scanned) {
  document.body.innerHTML = page;
  window.getScannedClues = () => scanned;

  // Capture the script's own listener so earlier loads can't also react
  const domReady = [];
  jest.spyOn(document, 'addEventListener').mockImplementation((type, fn) => {
    if (type === 'DOMContentLoaded') domReady.push(fn);
  });
  jest.resetModules();
  require('../src/js/history');
  document.addEventListener.mockRestore();
  domReady.forEach(fn => fn());
}

const history = () => document.getElementById('history');
const rows = () => Array.from(document.querySelectorAll('.clue-list li'));

afterEach(() => jest.restoreAllMocks());

test('with no clues found, the page says so and lists nothing', () => {
  load({ all: [] });
  expect(history().dataset.state).toBe('empty');
  expect(rows()).toHaveLength(0);
});

test('lists the clues newest first, each linking to its clue page', () => {
  load({
    all: ['AO100', 'WC3', 'AO101'],
    details: {
      AO100: { title: 'Typewriter', type: 'Artifact (Object)' },
      WC3: { title: 'Cordelia\'s Diary', type: 'Writing' },
      AO101: { title: 'Bell Collection', type: 'Artifact (Object)' }
    }
  });
  expect(history().dataset.state).toBe('list');
  expect(rows().map(row => row.querySelector('a').textContent)).toEqual(['Bell Collection', 'Cordelia\'s Diary', 'Typewriter']);
  expect(rows()[0].querySelector('a').getAttribute('href')).toBe('clues/AO101/');
  expect(rows()[0].textContent).toContain('Artifact (Object)');
});

test('the administrative sign-in clue is not listed', () => {
  load({
    all: ['SIGN_IN', 'AO100'],
    details: {
      SIGN_IN: { title: 'Sign In', type: 'Document (Administrative)' },
      AO100: { title: 'Typewriter', type: 'Artifact (Object)' }
    }
  });
  expect(rows().map(row => row.querySelector('a').textContent)).toEqual(['Typewriter']);
});

test('a clue saved without a title is listed by its id and still links', () => {
  load({ all: ['AO100'] });
  expect(rows()[0].querySelector('a').textContent).toBe('AO100');
  expect(rows()[0].querySelector('a').getAttribute('href')).toBe('clues/AO100/');
});
