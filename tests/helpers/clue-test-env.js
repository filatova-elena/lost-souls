function setupClueTestEnv(overrides = {}) {
  const storage = {};

  window.getFromLocalStorage = (key, fallback) => storage[key] || fallback;
  window.saveToLocalStorage = (key, value) => { storage[key] = value; };
  window.getScannedClues = () => storage.scanned || { all: [] };
  window.getCharacterProfile = () => ({ characterId: 'alice', skills: [] });
  
  // Use the real skills module for accurate testing
  const skills = require('../../src/lib/skills');
  window.hasSkillAccess = skills.hasSkillAccess;
  window.parseSkill = skills.parseSkill;
  window.convertSkills = skills.convertSkills;
  window.spawnParticles = jest.fn();
  window.triggerUnlockAnimation = jest.fn();
  window.buildOctogramLock = jest.fn();
  window.renderProgressPip = jest.fn();
  window.__progressData = { mainQuestHashtag: 'main_quest', mainQuestTotal: 3, sideQuests: {} };
  window.__noAccessMessages = {
    skill_phrases: { art: { level_2: ['expert art skills'] } },
    wrappers: { '_default': ['You need {requirements}.'] }
  };

  const access = require('../../src/js/clue-access');
  window.resolveClueState = access.resolveClueState;
  window.buildSkillLockedMessage = access.buildSkillLockedMessage;
  window.getQuestClueIsKeyFor = access.getQuestClueIsKeyFor;
  window.joinWithOr = access.joinWithOr;

  // Apply overrides
  Object.assign(window, overrides);

  return { storage };
}

function loadCluePage(clueData) {
  window.__clueData = clueData;
  // Load the clue-page module (it's an IIFE that runs on DOMContentLoaded)
  delete require.cache[require.resolve('../../src/js/clue-page')];
  require('../../src/js/clue-page');
  // Trigger DOMContentLoaded to initialize the page
  document.dispatchEvent(new Event('DOMContentLoaded'));
}

module.exports = { setupClueTestEnv, loadCluePage };
