/**
 * Clue page initialization
 * Resolves clue access state and sets data-state attribute on the page.
 * CSS handles all visibility based on data-state.
 */
(function() {
'use strict';

// ============================================================================
// Private utility functions
// ============================================================================

function randomItem(array) {
  return array[Math.floor(Math.random() * array.length)];
}

function joinWithOr(items) {
  if (items.length === 0) return '';
  if (items.length === 1) return items[0];
  if (items.length === 2) return `${items[0]} or ${items[1]}`;
  const last = items[items.length - 1];
  const rest = items.slice(0, -1);
  return `${rest.join(', ')}, or ${last}`;
}

function generateNoAccessMessage(missingSkills, clueType, noAccessMessages) {
  if (!noAccessMessages || !noAccessMessages.skill_phrases || !noAccessMessages.wrappers) {
    return "You don't have the required skills to access this clue.";
  }
  
  const phrases = [];
  for (const skill of missingSkills) {
    const parsed = window.parseSkill(skill);
    if (!parsed) continue;
    
    const skillPhrases = noAccessMessages.skill_phrases[parsed.base];
    if (!skillPhrases) continue;
    
    let phraseArray;
    if (parsed.level > 0) {
      phraseArray = skillPhrases[`level_${parsed.level}`];
    } else {
      phraseArray = Array.isArray(skillPhrases) ? skillPhrases : null;
    }
    
    if (phraseArray && phraseArray.length > 0) {
      phrases.push(randomItem(phraseArray));
    }
  }
  
  if (phrases.length === 0) {
    phrases.push("the required expertise");
  }
  
  let wrappers = noAccessMessages.wrappers[clueType];
  if (!wrappers || wrappers.length === 0) {
    wrappers = noAccessMessages.wrappers._default || ["The meaning here escapes you. You'd need {requirements}."];
  }
  
  const wrapper = randomItem(wrappers);
  const requirements = joinWithOr(phrases);
  return wrapper.replace('{requirements}', requirements);
}

function generateLockHTML(message, suggestedCharacters = null, unlockCode = null) {
  let lockHTML = '';
  
  // If unlock code exists, use octogram lock
  if (unlockCode) {
    lockHTML = `<div class="octogram-lock" data-unlock-code="${unlockCode}"></div>`;
  } else {
    // Standard lock
    lockHTML = `
      <div class="lock-assembly">
        <div class="lock-glow"></div>
        <div class="lock-shackle"></div>
        <div class="lock-body"><div class="keyhole"></div></div>
      </div>
    `;
  }
  
  if (message) {
    lockHTML += `<p>${message}</p>`;
  }
  
  if (suggestedCharacters && suggestedCharacters.length > 0) {
    // Wrap each character name in <strong> tags
    const boldCharacters = suggestedCharacters.map(name => `<strong>${name}</strong>`);
    const characterList = joinWithOr(boldCharacters);
    lockHTML += `<span class="locked-seek">Seek out ${characterList}</span>`;
  }
  
  return lockHTML;
}

// ============================================================================
// Clue storage functions (private, using generic localStorage utilities)
// ============================================================================

function getUnlockedClues() {
  return window.getFromLocalStorage('unlocked', []);
}

function markClueAsUnlocked(clueId) {
  const unlocked = getUnlockedClues();
  if (!unlocked.includes(clueId)) {
    unlocked.push(clueId);
    window.saveToLocalStorage('unlocked', unlocked);
  }
}

function getScannedClues() {
  return window.getFromLocalStorage('scanned', { all: [] });
}

function markClueAsScanned(clueId, clueData = {}) {
  const scanned = getScannedClues();

  if (!scanned.all.includes(clueId)) {
    scanned.all.push(clueId);
  }

  (clueData.is_key || []).forEach(hashtag => {
    if (!scanned[hashtag]) scanned[hashtag] = [];
    if (!scanned[hashtag].includes(clueId)) scanned[hashtag].push(clueId);
  });

  const unlocksGates = clueData.unlocks_gates || [];
  if (unlocksGates.length > 0) {
    if (!scanned.gates) scanned.gates = [];
    unlocksGates.forEach(gate => {
      if (!scanned.gates.includes(gate)) scanned.gates.push(gate);
    });
  }

  window.saveToLocalStorage('scanned', scanned);
  return scanned;
}

// ============================================================================
// Access control functions
// ============================================================================

function resolveClueState(clueData, noAccessMessages) {
  if (getUnlockedClues().includes(clueData.id)) {
    return { name: 'unlocked' };
  }

  if (clueData.gate) {
    const scanned = getScannedClues();
    if (!(scanned.gates || []).includes(clueData.gate)) {
      return { name: 'gated' };
    }
  }

  const profile = window.getCharacterProfile();
  const userSkills = profile ? profile.skills : [];
  const hasAccess = window.hasSkillAccess(clueData.skills || [], userSkills);

  if (!hasAccess) {
    return {
      name: 'skill-locked',
      message: generateNoAccessMessage(clueData.skills || [], clueData.type, noAccessMessages),
      suggestedCharacters: clueData.accessChars
    };
  }

  return { name: 'unlocked' };
}

function getNewlyFoundQuest(clueData) {
  const keyHashtags = clueData.is_key || [];
  if (keyHashtags.length === 0) return null;

  const progressData = window.__progressData || {};
  const mainQuestHashtag = progressData.mainQuestHashtag || 'main_quest';
  if (keyHashtags.includes(mainQuestHashtag)) return mainQuestHashtag;

  const profile = window.getCharacterProfile();
  const sideQuests = progressData.sideQuests || {};
  const sideQuest = profile?.characterId ? sideQuests[profile.characterId] : null;
  if (sideQuest?.hashtag && keyHashtags.includes(sideQuest.hashtag)) return sideQuest.hashtag;

  return null;
}

function initOctogramOnLock(lockSection, clueData) {
  const lockContainer = lockSection.querySelector('.octogram-lock[data-unlock-code]');
  if (!lockContainer || !window.buildOctogramLock) return;

  const cluePage = lockSection.closest('.clue-page');

  window.buildOctogramLock(lockContainer, clueData.unlock_code, () => {
    if (!cluePage) return;

    markClueAsUnlocked(clueData.id);
    markClueAsScanned(clueData.id, clueData);

    const quest = getNewlyFoundQuest(clueData);
    if (quest) {
      renderProgressTracker(quest);
      window.spawnParticles();
    } else {
      renderProgressTracker();
    }

    const isKeyClue = clueData.is_key?.length > 0;
    window.triggerUnlockAnimation(cluePage, lockSection, isKeyClue);
  });
}

// ============================================================================
// Page initialization
// ============================================================================

function initCluePage() {
  const page = document.querySelector('.clue-page');
  if (!page) return;

  const clueData = window.__clueData;
  const noAccessMessages = window.__noAccessMessages;
  if (!clueData) return;

  logDebugInfo(clueData);

  // Resolve state and set data-state (CSS handles visibility)
  const state = resolveClueState(clueData, noAccessMessages);
  page.dataset.state = state.name;

  // Skill-locked: populate the lock section with message, characters, optional octogram
  if (state.name === 'skill-locked') {
    const lockSection = page.querySelector('.clue-lock');
    if (lockSection) {
      lockSection.innerHTML = generateLockHTML(
        state.message, state.suggestedCharacters, clueData.unlock_code
      );
      if (clueData.unlock_code) {
        initOctogramOnLock(lockSection, clueData);
      }
    }
  }

  // Unlocked: mark as scanned, handle key clue effects, init static ring
  if (state.name === 'unlocked') {
    const scanned = getScannedClues();
    if (!scanned.all?.includes(clueData.id)) {
      markClueAsScanned(clueData.id, clueData);
      const quest = getNewlyFoundQuest(clueData);
      if (quest && window.spawnParticles) {
        renderProgressTracker(quest);
        window.spawnParticles();
      }
    }
    // Init static ring (shows which symbols to share with other players)
    if (clueData.unlock_code && window.buildStaticRing) {
      const ring = page.querySelector('.static-ring[data-unlock-code]');
      if (ring) window.buildStaticRing(ring, clueData.unlock_code);
    }
  }

  renderProgressTracker();
}

function logDebugInfo(clueData) {
  const progressData = window.__progressData || {};
  const characterProfile = window.getCharacterProfile();
  const scanned = getScannedClues();
  const currentCharacterId = characterProfile?.characterId;
  const characterSideQuests = progressData.sideQuests || {};
  const sideQuestInfo = currentCharacterId ? characterSideQuests[currentCharacterId] : null;
  const mainQuestFound = scanned[progressData.mainQuestHashtag || 'main_quest']?.length || 0;
  const sideQuestHashtag = sideQuestInfo?.hashtag;

  console.log('=== Clue Page Debug ===');
  console.log('Current character:', currentCharacterId || 'None');
  console.log('Private objective:', sideQuestInfo?.objectiveShort || 'None');
  console.log('Progress towards main objective:', `${mainQuestFound}/${progressData.mainQuestTotal || 0}`);
  console.log('Progress towards private objective:', sideQuestHashtag ? `${scanned[sideQuestHashtag]?.length || 0}/${sideQuestInfo?.total || 0}` : 'N/A');
  console.log('Character skills:', characterProfile?.skills || []);
  console.log('Clue required skills:', clueData.skills || []);
  console.log('Clue state gate:', clueData.gate || 'None');
  console.log('======================');
}

function renderProgressTracker(newlyFoundQuestHashtag = null) {
  const tracker = document.querySelector('[data-progress-tracker]');
  if (!tracker) return;

  const progressData = window.__progressData;
  if (!progressData) {
    console.error('Progress data not found');
    return;
  }

  const mainQuestHashtag = progressData.mainQuestHashtag || 'main_quest';
  const mainQuestTotal = progressData.mainQuestTotal || 0;
  const characterSideQuests = progressData.sideQuests || {};

  const characterProfile = window.getCharacterProfile();
  const currentCharacterId = characterProfile?.characterId || null;
  const scanned = getScannedClues();

  // Main quest progress
  const mainTrack = tracker.querySelector('.progress-track.main');
  if (mainTrack) {
    const found = scanned[mainQuestHashtag]?.length || 0;
    const newlyFoundIndex = (newlyFoundQuestHashtag === mainQuestHashtag) ? found - 1 : -1;
    renderQuestProgress(mainTrack, found, mainQuestTotal, newlyFoundIndex);
  }

  // Side quest progress for current character
  const sideTrack = tracker.querySelector('.progress-track.side');
  if (sideTrack && currentCharacterId && characterSideQuests[currentCharacterId]) {
    const sideQuestData = characterSideQuests[currentCharacterId];
    const found = scanned[sideQuestData.hashtag]?.length || 0;

    const sideLabel = sideTrack.querySelector('.progress-label');
    if (sideLabel && sideQuestData.objectiveShort) {
      sideLabel.textContent = sideQuestData.objectiveShort;
    }

    sideTrack.setAttribute('data-quest', sideQuestData.hashtag);
    sideTrack.style.display = '';
    const newlyFoundIndex = (newlyFoundQuestHashtag === sideQuestData.hashtag) ? found - 1 : -1;
    renderQuestProgress(sideTrack, found, sideQuestData.total, newlyFoundIndex);
  } else if (sideTrack) {
    sideTrack.style.display = 'none';
  }
}

function renderQuestProgress(trackElement, found, total, newlyFoundIndex = -1) {
  const pipsContainer = trackElement.querySelector('[data-pips]');
  const countElement = trackElement.querySelector('[data-count]');

  if (!pipsContainer || !countElement) return;

  pipsContainer.innerHTML = '';
  countElement.textContent = `${found} / ${total}`;

  for (let i = 0; i < total; i++) {
    const isFilled = i < found;
    const isJustFound = i === newlyFoundIndex;
    window.renderProgressPip(pipsContainer, isFilled, isJustFound);
  }
}

window.renderProgressTracker = renderProgressTracker;
document.addEventListener('DOMContentLoaded', initCluePage);
})();
