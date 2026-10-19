(function() {
'use strict';

// LocalStorage keys - centralized constants
const STORAGE_KEYS = {
  CHARACTER_PROFILE: 'character_profile',
  SCANNED: 'scanned',
  UNLOCKED: 'unlocked',
  UNLOCKED_ACTS: 'unlocked_acts'
};

function saveToLocalStorage(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
    return true;
  } catch (error) {
    console.error(`Failed to save to localStorage key "${key}":`, error);
    return false;
  }
}

function getFromLocalStorage(key, defaultValue = null) {
  try {
    const item = localStorage.getItem(key);
    if (item === null) return defaultValue;
    return JSON.parse(item);
  } catch {
    return defaultValue;
  }
}

function storeCharacterProfile(characterId, skills) {
  if (!characterId) return null;
  const profile = { characterId, skills: window.convertSkills(skills) };
  saveToLocalStorage(STORAGE_KEYS.CHARACTER_PROFILE, profile);
  return profile;
}

function getCharacterProfile() {
  return getFromLocalStorage(STORAGE_KEYS.CHARACTER_PROFILE);
}

function getScannedClues() {
  return getFromLocalStorage(STORAGE_KEYS.SCANNED, { all: [] });
}

function clearCharacterProfile() {
  localStorage.removeItem(STORAGE_KEYS.CHARACTER_PROFILE);
}

function resetInvestigation() {
  localStorage.removeItem(STORAGE_KEYS.CHARACTER_PROFILE);
  localStorage.removeItem(STORAGE_KEYS.SCANNED);
  localStorage.removeItem(STORAGE_KEYS.UNLOCKED);
  localStorage.removeItem(STORAGE_KEYS.UNLOCKED_ACTS);
}

function becomeGrandmother(charactersData) {
  if (!Array.isArray(charactersData)) return null;
  const grandmother = charactersData.find(c => c.id === 'grandmother');
  if (!grandmother?.skills) return null;
  return storeCharacterProfile('grandmother', grandmother.skills);
}

// ============================================================================
// Progress tracker (global — runs on every page)
// ============================================================================

function getCharacterTrack() {
  var progressData = window.__progressData || {};
  var profile = getCharacterProfile();
  var charId = profile?.characterId;
  if (!charId) return null;
  return progressData.characterTracks?.[charId] || null;
}

function isTrackClue(clueId) {
  var track = getCharacterTrack();
  return track?.clueChain?.includes(clueId) || false;
}

function renderProgressTracker(justProgressed) {
  var tracker = document.querySelector('[data-progress-tracker]');
  if (!tracker) return;

  var progressData = window.__progressData || {};
  var profile = getCharacterProfile();
  var charId = profile?.characterId;
  var label = tracker.querySelector('[data-character-label]');

  if (label) {
    if (charId && progressData.characterNames?.[charId]) {
      label.textContent = progressData.characterNames[charId];
    } else {
      label.textContent = 'Select a character';
    }
  }

  var track = getCharacterTrack();
  var trackEl = tracker.querySelector('.progress-track');
  if (!trackEl) return;

  if (!track) {
    trackEl.style.display = 'none';
    return;
  }

  var scanned = getScannedClues();
  var chain = track.clueChain;
  var found = chain.filter(function(id) { return scanned.all?.includes(id); }).length;

  trackEl.setAttribute('data-quest', track.trackId);
  trackEl.style.display = '';

  var pipsContainer = trackEl.querySelector('[data-pips]');
  if (!pipsContainer) return;

  pipsContainer.innerHTML = '';

  for (var i = 0; i < chain.length; i++) {
    var isFilled = scanned.all?.includes(chain[i]);
    var isJustFound = justProgressed && i === found - 1;
    window.renderProgressPip(pipsContainer, isFilled, isJustFound);
  }
}

window.saveToLocalStorage = saveToLocalStorage;
window.getFromLocalStorage = getFromLocalStorage;
window.storeCharacterProfile = storeCharacterProfile;
window.getCharacterProfile = getCharacterProfile;
window.getScannedClues = getScannedClues;
window.clearCharacterProfile = clearCharacterProfile;
window.resetInvestigation = resetInvestigation;
window.becomeGrandmother = becomeGrandmother;
window.STORAGE_KEYS = STORAGE_KEYS;
window.renderProgressTracker = renderProgressTracker;
window.isTrackClue = isTrackClue;
window.getCharacterTrack = getCharacterTrack;

document.addEventListener('DOMContentLoaded', function() {
  renderProgressTracker();
});

})();
