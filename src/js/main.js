(function() {
'use strict';

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
  saveToLocalStorage('character_profile', profile);
  return profile;
}

function getCharacterProfile() {
  return getFromLocalStorage('character_profile');
}

function getScannedClues() {
  return getFromLocalStorage('scanned', { all: [] });
}

function clearCharacterProfile() {
  localStorage.removeItem('character_profile');
}

function resetInvestigation() {
  localStorage.removeItem('character_profile');
  localStorage.removeItem('scanned');
  localStorage.removeItem('unlocked');
  localStorage.removeItem('unlocked_acts');
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

})();
