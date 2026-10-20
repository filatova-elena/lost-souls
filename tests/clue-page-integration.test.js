/**
 * @jest-environment jsdom
 */

const { setupClueTestEnv, loadCluePage } = require('./helpers/clue-test-env');

describe('clue page interactions', () => {
  let storage;

  beforeEach(() => {
    // Reset DOM
    document.body.innerHTML = '';
    // Clear any existing modules
    jest.resetModules();
    // Setup test environment and capture storage
    ({ storage } = setupClueTestEnv());
  });

  test('player sees clue content when they have access', () => {
    document.body.innerHTML = `
      <div class="clue-page">
        <section class="clue-lock"></section>
        <section class="clue-content">Secret content</section>
      </div>
    `;

    loadCluePage({ id: 'CLUE1', act: 'act_i_setting', skills: [] });
    expect(document.querySelector('.clue-page').dataset.state).toBe('unlocked');
  });

  test('player cannot see clue content when skill-locked', () => {
    document.body.innerHTML = `
      <div class="clue-page">
        <section class="clue-lock"></section>
        <section class="clue-content">Secret content</section>
      </div>
    `;

    loadCluePage({ id: 'CLUE1', act: 'act_i_setting', skills: ['art_2'], type: 'Document' });
    expect(document.querySelector('.clue-page').dataset.state).toBe('skill-locked');
  });

  test('opening a clue saves its title and type for the history page', () => {
    document.body.innerHTML = '<div class="clue-page"><section class="clue-content"></section></div>';

    loadCluePage({ id: 'CLUE1', act: 'act_i_setting', skills: [], title: 'The Typewriter', type: 'Artifact (Object)' });
    expect(storage.scanned.all).toEqual(['CLUE1']);
    expect(storage.scanned.details.CLUE1).toEqual({ title: 'The Typewriter', type: 'Artifact (Object)' });
  });

  test('a clue the player cannot open yet is not saved to the history', () => {
    document.body.innerHTML = '<div class="clue-page"><section class="clue-lock"></section></div>';

    loadCluePage({ id: 'CLUE1', act: 'act_i_setting', skills: ['art_2'], type: 'Document', title: 'Locked' });
    expect(storage.scanned).toBeUndefined();
  });

  test('player can see clue content when they have required skills', () => {
    window.getCharacterProfile = () => ({ characterId: 'alice', skills: ['art_2'] });

    document.body.innerHTML = `
      <div class="clue-page">
        <section class="clue-lock"></section>
        <section class="clue-content">Secret content</section>
      </div>
    `;

    loadCluePage({ id: 'CLUE1', act: 'act_i_setting', skills: ['art_2'], type: 'Document' });
    expect(document.querySelector('.clue-page').dataset.state).toBe('unlocked');
  });
});
