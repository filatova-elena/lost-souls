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

window.saveToLocalStorage = saveToLocalStorage;
window.getFromLocalStorage = getFromLocalStorage;
window.storeCharacterProfile = storeCharacterProfile;
window.getCharacterProfile = getCharacterProfile;
window.getScannedClues = getScannedClues;
window.clearCharacterProfile = clearCharacterProfile;
window.resetInvestigation = resetInvestigation;
window.becomeGrandmother = becomeGrandmother;
window.STORAGE_KEYS = STORAGE_KEYS;

})();
