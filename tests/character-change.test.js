/** @jest-environment jsdom */

function load(beforeLoad = () => {}) {
  document.body.innerHTML = `
    <div class="progress-tracker" data-progress-tracker>
      <span class="progress-label" data-character-label>Select a character</span>
      <div class="progress-track" data-quest=""><div class="progress-pips" data-pips></div></div>
    </div>`;
  window.__progressData = { characterNames: { antiquarian: 'The Antiquarian' }, characterTracks: {} };
  window.convertSkills = skills => skills;
  localStorage.clear();
  beforeLoad();
  jest.resetModules();
  require('../src/js/main');
}

const label = () => document.querySelector('[data-character-label]').textContent;

afterEach(() => jest.restoreAllMocks());

test('the status bar shows the character as soon as it is stored', () => {
  load();
  expect(label()).toBe('Select a character');
  window.storeCharacterProfile('antiquarian', []);
  expect(label()).toBe('The Antiquarian');
});

test('a listener that fails does not stop the character from being stored, or the bar from updating', () => {
  // The browser reports a failing listener on the window (its console); it does not throw it back
  const reported = [];
  window.addEventListener('error', event => {
    event.preventDefault();
    reported.push(event.error.message);
  });
  let profile;
  load(() => document.addEventListener('characterchange', () => { throw new Error('some listener broke'); }));

  expect(() => { profile = window.storeCharacterProfile('antiquarian', []); }).not.toThrow();
  expect(reported).toContain('some listener broke');
  expect(profile.characterId).toBe('antiquarian');
  expect(window.getCharacterProfile().characterId).toBe('antiquarian');
  expect(label()).toBe('The Antiquarian');
});
