/**
 * Clue page initialization
 * Resolves clue access state and sets data-state attribute on the page.
 * CSS handles all visibility based on data-state.
 */
(function() {
'use strict';

// Act enum
const Act = {
  PROLOGUE: 'act_prologue',
  I_SETTING: 'act_i_setting',
  II_MYSTERY_EMERGES: 'act_ii_mystery_emerges',
  III_INVESTIGATION: 'act_iii_investigation',
  IV_REVELATION: 'act_iv_revelation',
  V_CONCLUSIONS: 'act_v_conclusions',
  V_AFTERMATH: 'act_v_aftermath'
};

// Access state enum
const AccessState = {
  UNLOCKED: 'unlocked',
  GATED: 'gated',
  SKILL_LOCKED: 'skill-locked'
};

// LocalStorage keys
const STORAGE_KEYS = {
  UNLOCKED_ACTS: 'unlocked_acts'
};

// ============================================================================
// Private utility functions
// ============================================================================

// Utility functions are now provided by clue-access.js module
// Using window versions if available, with fallbacks
function joinWithOr(items) {
  if (window.joinWithOr) {
    return window.joinWithOr(items);
  }
  // Fallback if module not loaded
  if (items.length === 0) return '';
  if (items.length === 1) return items[0];
  if (items.length === 2) return `${items[0]} or ${items[1]}`;
  const last = items[items.length - 1];
  const rest = items.slice(0, -1);
  return `${rest.join(', ')}, or ${last}`;
}

/**
 * Builds a user-friendly message explaining why a clue is skill-locked
 * Delegates to the extracted module function
 * @param {Array<string>} missingSkills - Array of skill IDs that are required but missing
 * @param {string} clueType - Type of clue (e.g., "Document", "Artifact")
 * @param {Object} noAccessMessages - Message templates from refs.no_access_messages
 * @returns {string} Formatted message explaining the skill requirements
 */
function buildSkillLockedMessage(missingSkills, clueType, noAccessMessages) {
  if (window.buildSkillLockedMessage) {
    return window.buildSkillLockedMessage(missingSkills, clueType, noAccessMessages);
  }
  // Fallback if module not loaded
  return "You don't have the required skills to access this clue.";
}

/**
 * Builds the complete HTML content for a locked clue section
 * @param {string} message - Message to display explaining why the clue is locked
 * @param {Array<string>|null} suggestedCharacters - Array of character names who can access this clue
 * @param {string|null} unlockCode - Optional unlock code for octogram lock
 * @returns {string} HTML string for the lock section content
 */
function buildLockSectionContent(message, suggestedCharacters = null, unlockCode = null) {
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
    lockHTML += `<span class="character-callout">Seek out ${characterList}</span>`;
  }
  
  return lockHTML;
}

// ============================================================================
// Clue storage functions (private, using generic localStorage utilities)
// ============================================================================

/**
 * Gets the list of clue IDs that have been manually unlocked (via octogram)
 * @returns {Array<string>} Array of manually unlocked clue IDs
 */
function getManuallyUnlockedClues() {
  return window.getFromLocalStorage('unlocked', []);
}

/**
 * Saves a clue as manually unlocked (via octogram puzzle bypass)
 * @param {string} clueId - The ID of the clue that was manually unlocked
 */
function saveManualUnlock(clueId) {
  const unlocked = getManuallyUnlockedClues();
  if (!unlocked.includes(clueId)) {
    unlocked.push(clueId);
    window.saveToLocalStorage('unlocked', unlocked);
  }
}

/**
 * Records that a clue has been scanned
 * @param {string} clueId - The ID of the clue being scanned
 * @returns {Object} Updated scanned clues object
 */
function recordClueScan(clueId) {
  const scanned = window.getScannedClues();
  if (!scanned.all.includes(clueId)) {
    scanned.all.push(clueId);
  }
  window.saveToLocalStorage('scanned', scanned);
  return scanned;
}

/**
 * Tracks quest key progress by hashtag
 * @param {string} clueId - The ID of the clue being scanned
 * @param {Array<string>|undefined} keyHashtags - Array of quest hashtags this clue is a key for
 */
function trackQuestKeyProgress(clueId, keyHashtags) {
  if (!keyHashtags?.length) return;
  const scanned = window.getScannedClues();
  keyHashtags.forEach(hashtag => {
    if (!scanned[hashtag]) scanned[hashtag] = [];
    if (!scanned[hashtag].includes(clueId)) scanned[hashtag].push(clueId);
  });
  window.saveToLocalStorage('scanned', scanned);
}

/**
 * Unlocks a story gate (act) when a gate clue is discovered
 * @param {string|undefined} actKey - The act key to unlock (e.g., "act_ii_mystery_emerges")
 */
function unlockStoryGate(actKey) {
  if (!actKey) return;
  const unlocked = window.getFromLocalStorage(STORAGE_KEYS.UNLOCKED_ACTS, []);
  if (!unlocked.includes(actKey)) {
    unlocked.push(actKey);
    window.saveToLocalStorage(STORAGE_KEYS.UNLOCKED_ACTS, unlocked);
  }
}

/**
 * Processes all side effects of discovering a clue
 * Coordinates scanning, quest progress tracking, and story gate unlocking
 * @param {Object} clueData - Clue data object (id, is_key, story_gate_for)
 */
function processClueDiscovery(clueData) {
  recordClueScan(clueData.id);
  trackQuestKeyProgress(clueData.id, clueData.is_key);
  unlockStoryGate(clueData.story_gate_for);
}

// ============================================================================
// Access control functions
// ============================================================================

/**
 * Determines the access state of a clue based on gates, skills, and unlock status
 * Checks in order: manually unlocked → story gate → skill requirements
 * Delegates to the extracted module function
 * @param {Object} clueData - Clue data object (id, act, skills, etc.)
 * @param {Object} noAccessMessages - Message templates for skill-locked state
 * @returns {Object} State object with name and optional message/suggestedCharacters
 */
function determineAccessState(clueData, noAccessMessages) {
  if (window.resolveClueState) {
    const unlockedClues = getManuallyUnlockedClues();
    const unlockedActs = window.getFromLocalStorage(STORAGE_KEYS.UNLOCKED_ACTS, []);
    const profile = window.getCharacterProfile();
    const userSkills = profile ? profile.skills : [];
    
    return window.resolveClueState(clueData, {
      unlockedClues,
      unlockedActs,
      userSkills,
      noAccessMessages,
      hasSkillAccessFn: window.hasSkillAccess,
      parseSkillFn: window.parseSkill
    });
  }
  
  // Fallback if module not loaded (shouldn't happen in production)
  return { name: AccessState.UNLOCKED };
}

/**
 * Gets the quest hashtag that this clue is a key clue for (main or side quest)
 * Delegates to the extracted module function
 * @param {Object} clueData - Clue data object (must have is_key array)
 * @returns {string|null} Quest hashtag if this clue is a key clue for a quest, null otherwise
 */
function getQuestClueIsKeyFor(clueData) {
  if (window.getQuestClueIsKeyFor) {
    const progressData = window.__progressData || {};
    const profile = window.getCharacterProfile();
    
    return window.getQuestClueIsKeyFor(clueData, {
      mainQuestHashtag: progressData.mainQuestHashtag || 'main_quest',
      sideQuests: progressData.sideQuests || {},
      characterId: profile?.characterId || null
    });
  }
  
  // Fallback if module not loaded (shouldn't happen in production)
  return null;
}

/**
 * Handles what happens when a player successfully unlocks a clue via octogram puzzle
 * Saves the manual unlock, marks as scanned, updates progress, and triggers animations
 * @param {Object} clueData - Clue data object (id, is_key, unlock_code, etc.)
 */
function onOctogramUnlock(clueData) {
  const cluePage = document.querySelector('.clue-page');
  const lockSection = cluePage?.querySelector('.clue-lock');
  if (!cluePage || !lockSection) return;

  saveManualUnlock(clueData.id);
  processClueDiscovery(clueData);
  cluePage.dataset.state = AccessState.UNLOCKED;

  const quest = getQuestClueIsKeyFor(clueData);
  if (quest) {
    renderProgressTracker(quest);
    window.spawnParticles();
  } else {
    renderProgressTracker();
  }

  const isKeyClue = clueData.is_key?.length > 0;
  window.triggerUnlockAnimation(cluePage, lockSection, isKeyClue);
}

/**
 * Sets up the octogram lock UI and wires it to the unlock handler
 * @param {HTMLElement} lockSection - The lock section DOM element
 * @param {Object} clueData - Clue data object (id, unlock_code, is_key, etc.)
 */
function setupOctogramLock(lockSection, clueData) {
  const lockContainer = lockSection.querySelector('.octogram-lock[data-unlock-code]');
  if (!lockContainer || !window.buildOctogramLock) return;
  window.buildOctogramLock(lockContainer, clueData.unlock_code, () => onOctogramUnlock(clueData));
}

// ============================================================================
// Page initialization
// ============================================================================

/**
 * Initializes the clue page: resolves access state, populates UI, handles scanning
 * Main entry point for clue page functionality
 */
function initCluePage() {
  const page = document.querySelector('.clue-page');
  if (!page) return;

  const clueData = window.__clueData;
  const noAccessMessages = window.__noAccessMessages;
  if (!clueData) return;

  logClueDebugInfo(clueData);

  // Determine access state and set data-state (CSS handles visibility)
  const state = determineAccessState(clueData, noAccessMessages);
  page.dataset.state = state.name;

  // Skill-locked: populate the lock section with message, characters, optional octogram
  if (state.name === AccessState.SKILL_LOCKED) {
    const lockSection = page.querySelector('.clue-lock');
    if (lockSection) {
      lockSection.innerHTML = buildLockSectionContent(
        state.message, state.suggestedCharacters, clueData.unlock_code
      );
      if (clueData.unlock_code) {
        setupOctogramLock(lockSection, clueData);
      }
    }
  }

  // Unlocked: mark as scanned, handle key clue effects, init static ring
  if (state.name === AccessState.UNLOCKED) {
    const scanned = window.getScannedClues();
    if (!scanned.all?.includes(clueData.id)) {
      processClueDiscovery(clueData);
      const quest = getQuestClueIsKeyFor(clueData);
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

  // Populate character name for sign-in clues
  if (clueData.id === 'SIGN_IN') {
    const characterDisplay = document.getElementById('sign-in-character-name');
    if (characterDisplay && window.getCharacterProfile) {
      const profile = window.getCharacterProfile();
      if (profile && profile.characterId && window.__characters) {
        const character = window.__characters.find(c => c.id === profile.characterId);
        if (character) {
          characterDisplay.textContent = character.title;
        } else {
          characterDisplay.textContent = profile.characterId;
        }
      } else {
        characterDisplay.textContent = 'None';
      }
    }
  }

  renderProgressTracker();
}

/**
 * Logs debug information about the current clue page state to console
 * @param {Object} clueData - Clue data object
 */
function logClueDebugInfo(clueData) {
  const progressData = window.__progressData || {};
  const characterProfile = window.getCharacterProfile();
  const scanned = window.getScannedClues();
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
  console.log('Clue act:', clueData.act || 'None');
  console.log('Unlocked acts:', window.getFromLocalStorage(STORAGE_KEYS.UNLOCKED_ACTS, []));
  console.log('======================');
}

/**
 * Renders the progress tracker showing main quest and side quest progress
 * @param {string|null} progressedQuestHashtag - Optional hashtag of a quest that just progressed (for animation)
 */
function renderProgressTracker(progressedQuestHashtag = null) {
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
  const scanned = window.getScannedClues();

  // Main quest progress
  const mainTrack = tracker.querySelector('.progress-track.main');
  if (mainTrack) {
    const found = scanned[mainQuestHashtag]?.length || 0;
    const progressedIndex = (progressedQuestHashtag === mainQuestHashtag) ? found - 1 : -1;
    renderQuestProgress(mainTrack, found, mainQuestTotal, progressedIndex);
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
    const progressedIndex = (progressedQuestHashtag === sideQuestData.hashtag) ? found - 1 : -1;
    renderQuestProgress(sideTrack, found, sideQuestData.total, progressedIndex);
  } else if (sideTrack) {
    sideTrack.style.display = 'none';
  }
}

/**
 * Renders progress pips and count for a single quest track
 * @param {HTMLElement} trackElement - The progress track DOM element
 * @param {number} found - Number of key clues found for this quest
 * @param {number} total - Total number of key clues for this quest
 * @param {number} progressedIndex - Index of the clue that just progressed (for animation), -1 if none
 */
function renderQuestProgress(trackElement, found, total, progressedIndex = -1) {
  const pipsContainer = trackElement.querySelector('[data-pips]');
  const countElement = trackElement.querySelector('[data-count]');

  if (!pipsContainer || !countElement) return;

  pipsContainer.innerHTML = '';
  countElement.textContent = `${found} / ${total}`;

  for (let i = 0; i < total; i++) {
    const isFilled = i < found;
    const isJustFound = i === progressedIndex;
    window.renderProgressPip(pipsContainer, isFilled, isJustFound);
  }
}

window.renderProgressTracker = renderProgressTracker;
document.addEventListener('DOMContentLoaded', initCluePage);
})();
