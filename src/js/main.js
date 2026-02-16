(function() {
'use strict';

const CHARACTER_PROFILE_KEY = 'character_profile';
const SCANNED_CLUES_KEY = 'scanned';
const UNLOCKED_CLUES_KEY = 'unlocked';

// Skills functions are now imported from skills.js (loaded before this script)
// Using window.parseSkill, window.convertSkills, window.hasSkillAccess

function storeCharacterProfile(characterId, skills) {
  if (!characterId) {
    console.error('Character ID is required');
    return null;
  }

  const profile = {
    characterId,
    skills: window.convertSkills(skills)
  };

  localStorage.setItem(CHARACTER_PROFILE_KEY, JSON.stringify(profile));
  return profile;
}

function getCharacterProfile() {
  try {
    const profile = JSON.parse(localStorage.getItem(CHARACTER_PROFILE_KEY));
    return profile?.characterId ? profile : null;
  } catch {
    return null;
  }
}

function clearCharacterProfile() {
  localStorage.removeItem(CHARACTER_PROFILE_KEY);
}

/**
 * Reset investigation - clears all localStorage data
 */
function resetInvestigation() {
  localStorage.removeItem(CHARACTER_PROFILE_KEY);
  localStorage.removeItem(SCANNED_CLUES_KEY);
  localStorage.removeItem(UNLOCKED_CLUES_KEY);
}

/**
 * Check if user has access to a clue based on their skills
 * Uses OR logic: user needs at least ONE of the required skills
 * @param {Array<string>} requiredSkills - Array of required skills (e.g., ["history_1", "botanical_1", "personal_romano"])
 * @param {Array<string>} userSkills - Array of user's skills
 * @returns {Object} { hasAccess: boolean, missingSkills: Array<string> }
 */
function checkClueAccess(requiredSkills = [], userSkills = []) {
  // Use shared hasSkillAccess function from skills.js
  const hasAccess = window.hasSkillAccess(requiredSkills, userSkills);
  
  if (hasAccess) {
    return { hasAccess: true, missingSkills: [] };
  }

  // User doesn't have any of the required skills - return all as missing
  return { hasAccess: false, missingSkills: requiredSkills };
}

/**
 * Get a random item from an array
 */
function randomItem(array) {
  return array[Math.floor(Math.random() * array.length)];
}

/**
 * Join array with Oxford comma "or"
 */
function joinWithOr(items) {
  if (items.length === 0) return '';
  if (items.length === 1) return items[0];
  if (items.length === 2) return `${items[0]} or ${items[1]}`;
  const last = items[items.length - 1];
  const rest = items.slice(0, -1);
  return `${rest.join(', ')}, or ${last}`;
}

/**
 * Generate no-access message for a clue
 * @param {Array<string>} missingSkills - Array of missing skills
 * @param {string} clueType - Clue type (e.g., "Artifact (Object)")
 * @param {Object} noAccessMessages - The no_access_messages data structure
 * @returns {string} The generated message
 */
function generateNoAccessMessage(missingSkills, clueType, noAccessMessages) {
  if (!noAccessMessages || !noAccessMessages.skill_phrases || !noAccessMessages.wrappers) {
    return "You don't have the required skills to access this clue.";
  }
  
  // Get skill phrases for missing skills
  const phrases = [];
  for (const skill of missingSkills) {
    const parsed = window.parseSkill(skill);
    if (!parsed) continue;
    
    const skillPhrases = noAccessMessages.skill_phrases[parsed.base];
    if (!skillPhrases) continue;
    
    let phraseArray;
    if (parsed.level > 0) {
      // Has level (e.g., botanical_1, medical_2)
      phraseArray = skillPhrases[`level_${parsed.level}`];
    } else {
      // Personal skill (no level)
      phraseArray = Array.isArray(skillPhrases) ? skillPhrases : null;
    }
    
    if (phraseArray && phraseArray.length > 0) {
      phrases.push(randomItem(phraseArray));
    }
  }
  
  if (phrases.length === 0) {
    phrases.push("the required expertise");
  }
  
  // Get wrapper for clue type
  let wrappers = noAccessMessages.wrappers[clueType];
  if (!wrappers || wrappers.length === 0) {
    wrappers = noAccessMessages.wrappers._default || ["The meaning here escapes you. You'd need {requirements}."];
  }
  
  const wrapper = randomItem(wrappers);
  const requirements = joinWithOr(phrases);
  const message = wrapper.replace('{requirements}', requirements);
  
  return message;
}

/**
 * Get unlocked clues from localStorage
 * @returns {Array<string>} Array of unlocked clue IDs
 */
function getUnlockedClues() {
  try {
    const unlocked = JSON.parse(localStorage.getItem(UNLOCKED_CLUES_KEY));
    return Array.isArray(unlocked) ? unlocked : [];
  } catch {
    return [];
  }
}

/**
 * Mark a clue as unlocked (via alchemical symbols) and save to localStorage
 * @param {string} clueId - The clue ID to mark as unlocked
 * @returns {Array<string>} Updated unlocked clues array
 */
function markClueAsUnlocked(clueId) {
  if (!clueId) {
    console.error('Clue ID is required');
    return [];
  }

  const unlocked = getUnlockedClues();
  
  if (!unlocked.includes(clueId)) {
    unlocked.push(clueId);
    try {
      localStorage.setItem(UNLOCKED_CLUES_KEY, JSON.stringify(unlocked));
    } catch (error) {
      console.error('Failed to save unlocked clues:', error);
    }
  }
  
  return unlocked;
}

/**
 * Check clue access (pure logic, no DOM manipulation)
 * Access check order:
 * 1. Is unlocked? (via alchemical symbols)
 * 2. Check story gates (TODO - not implemented)
 * 3. Check skills
 * @param {Object} clueData - Clue data object with skills, type, accessChars (pre-computed), etc.
 * @param {Object} noAccessMessages - The no_access_messages data structure
 * @returns {Object} { hasAccess: boolean, missingSkills: Array<string>, message?: string, suggestedCharacters?: Array<string> }
 */
function checkAccess(clueData, noAccessMessages) {
  if (!clueData) {
    console.error('Clue data is required');
    return { hasAccess: false, missingSkills: [] };
  }
  
  // 1. Check if unlocked via alchemical symbols
  const unlocked = getUnlockedClues();
  if (unlocked.includes(clueData.id)) {
    return { hasAccess: true, missingSkills: [] };
  }
  
  // 2. Check story gates (TODO - not implemented)
  // This would check if prerequisite clues/events have been completed
  
  // 3. Check skills
  const profile = getCharacterProfile();
  const userSkills = profile ? profile.skills : [];
  const requiredSkills = Array.isArray(clueData.skills) ? clueData.skills : [];
  
  const access = checkClueAccess(requiredSkills, userSkills);
  
  if (!access.hasAccess && noAccessMessages) {
    access.message = generateNoAccessMessage(access.missingSkills, clueData.type, noAccessMessages);
    
    // Use pre-computed character list from build time (clueData.accessChars)
    // This avoids client-side iteration over all characters
    if (clueData.accessChars && Array.isArray(clueData.accessChars) && clueData.accessChars.length > 0) {
      access.suggestedCharacters = clueData.accessChars;
    }
  }
  
  return access;
}

/**
 * Render clue access control in the DOM
 * @param {Object} access - Access check result from checkAccess()
 * @param {boolean} showLockFirst - If true, show lock even if hasAccess (for animation)
 */
function renderClueAccess(access, showLockFirst = false) {
  const narrationSections = document.querySelectorAll('.clue-narration');
  const contentSections = document.querySelectorAll('.clue-content');
  const lockSection = document.querySelector('.clue-no-access');
  
  if (access.hasAccess && !showLockFirst) {
    // Show all content (already unlocked)
    narrationSections.forEach(section => section.style.display = '');
    contentSections.forEach(section => section.style.display = '');
    // Hide lock
    if (lockSection) {
      lockSection.style.display = 'none';
    }
    
    // Show static ring if unlock_code exists
    const clueData = window.__clueData || {};
    if (clueData.unlock_code && window.buildStaticRing) {
      const staticRing = document.querySelector('.static-ring[data-unlock-code]');
      if (staticRing) {
        const seanceSection = staticRing.closest('.seance-section');
        if (seanceSection) {
          seanceSection.style.display = '';
          window.buildStaticRing(staticRing, clueData.unlock_code);
        }
      }
    }
  } else {
    // Hide content (either locked or about to unlock)
    narrationSections.forEach(section => section.style.display = 'none');
    contentSections.forEach(section => section.style.display = 'none');
    
    // Show and populate lock message if needed
    if (lockSection && (access.message || showLockFirst)) {
      const message = access.message || '';
      const clueData = window.__clueData || {};
      const unlockCode = clueData.unlock_code || null;
      const lockHTML = generateLockHTML(message, access.suggestedCharacters, unlockCode);
      lockSection.innerHTML = lockHTML;
      lockSection.style.display = '';
      
      // Initialize octogram lock if present
      if (unlockCode && window.buildOctogramLock) {
        const lockContainer = lockSection.querySelector('.octogram-lock[data-unlock-code]');
        if (lockContainer) {
          const cluePage = lockSection.closest('main') || lockSection.closest('.clue-page');
          window.buildOctogramLock(lockContainer, unlockCode, () => {
            if (cluePage) {
              const isKeyClue = clueData.is_key && (Array.isArray(clueData.is_key) ? clueData.is_key.length > 0 : !!clueData.is_key);
              
              // Mark clue as unlocked and scanned when unlocked via octogram
              if (clueData.id) {
                markClueAsUnlocked(clueData.id);
                markClueAsScanned(clueData.id, clueData);
                
                // Update progress tracker if key clue
                if (isKeyClue && window.renderProgressTracker) {
                  const progressData = window.__progressData || {};
                  const characterProfile = getCharacterProfile();
                  const currentCharacterId = characterProfile?.characterId;
                  const characterSideQuests = progressData.sideQuests || {};
                  const sideQuestInfo = currentCharacterId ? characterSideQuests[currentCharacterId] : null;
                  const mainQuestHashtag = progressData.mainQuestHashtag || 'main_quest';
                  const sideQuestHashtag = sideQuestInfo?.hashtag;
                  
                  const keyHashtags = Array.isArray(clueData.is_key) ? clueData.is_key : (clueData.is_key ? [clueData.is_key] : []);
                  let newlyFoundQuestHashtag = null;
                  if (keyHashtags.includes(mainQuestHashtag)) {
                    newlyFoundQuestHashtag = mainQuestHashtag;
                  } else if (sideQuestHashtag && keyHashtags.includes(sideQuestHashtag)) {
                    newlyFoundQuestHashtag = sideQuestHashtag;
                  }
                  
                  if (newlyFoundQuestHashtag) {
                    window.renderProgressTracker(newlyFoundQuestHashtag);
                    window.spawnParticles();
                  } else {
                    window.renderProgressTracker();
                  }
                } else if (window.renderProgressTracker) {
                  window.renderProgressTracker();
                }
              }
              
              window.triggerUnlockAnimation(cluePage, lockSection, isKeyClue);
            }
          });
        }
      }
    } else if (lockSection) {
      lockSection.style.display = 'none';
    }
  }
}


/**
 * Set character to grandmother (who has all skills)
 * @param {Array<Object>} charactersData - Characters data array to find grandmother
 * @returns {Object|null} The stored profile or null if failed
 */
function becomeGrandmother(charactersData) {
  if (!charactersData || !Array.isArray(charactersData)) {
    console.error('becomeGrandmother requires characters data array');
    return null;
  }
  
  // Find grandmother character from data
  const grandmother = charactersData.find(char => char.id === 'grandmother');
  if (!grandmother || !grandmother.skills) {
    console.error('Grandmother character not found in characters data');
    return null;
  }
  
  return storeCharacterProfile('grandmother', grandmother.skills);
}

/**
 * Get scanned clues from localStorage
 * @returns {Object} Scanned clues object with structure: { all: [], quest1: [], quest2: [], ... }
 */
function getScannedClues() {
  try {
    const scanned = JSON.parse(localStorage.getItem(SCANNED_CLUES_KEY));
    return scanned || { all: [] };
  } catch {
    return { all: [] };
  }
}

/**
 * Save scanned clues to localStorage
 * @param {Object} scanned - Scanned clues object
 */
function saveScannedClues(scanned) {
  try {
    localStorage.setItem(SCANNED_CLUES_KEY, JSON.stringify(scanned));
  } catch (error) {
    console.error('Failed to save scanned clues:', error);
  }
}

/**
 * Mark a clue as scanned and update localStorage
 * @param {string} clueId - The clue ID to mark as scanned
 * @param {Object} clueData - Clue data object with is_key field (array of quest hashtags)
 * @returns {Object} Updated scanned clues object
 */
function markClueAsScanned(clueId, clueData = {}) {
  if (!clueId) {
    console.error('Clue ID is required');
    return null;
  }

  const scanned = getScannedClues();
  
  // Ensure 'all' array exists
  if (!Array.isArray(scanned.all)) {
    scanned.all = [];
  }
  
  // Add to 'all' if not already present
  if (!scanned.all.includes(clueId)) {
    scanned.all.push(clueId);
  }
  
  // Add to quest-specific arrays based on is_key
  const isKey = clueData.is_key || [];
  if (Array.isArray(isKey)) {
    isKey.forEach(questHashtag => {
      if (!questHashtag) return;
      
      // Initialize quest array if it doesn't exist
      if (!Array.isArray(scanned[questHashtag])) {
        scanned[questHashtag] = [];
      }
      
      // Add clue ID if not already present
      if (!scanned[questHashtag].includes(clueId)) {
        scanned[questHashtag].push(clueId);
      }
    });
  } else if (isKey) {
    // Handle case where is_key is a single string (backwards compatibility)
    const questHashtag = isKey;
    if (!Array.isArray(scanned[questHashtag])) {
      scanned[questHashtag] = [];
    }
    if (!scanned[questHashtag].includes(clueId)) {
      scanned[questHashtag].push(clueId);
    }
  }
  
  saveScannedClues(scanned);
  return scanned;
}

// Expose functions to global scope
// Note: parseSkill, convertSkills, and hasSkillAccess are exposed by skills.js
window.storeCharacterProfile = storeCharacterProfile;
window.getCharacterProfile = getCharacterProfile;
window.clearCharacterProfile = clearCharacterProfile;
window.resetInvestigation = resetInvestigation;
window.becomeGrandmother = becomeGrandmother;
window.checkClueAccess = checkClueAccess;
window.checkAccess = checkAccess;
window.renderClueAccess = renderClueAccess;
window.getScannedClues = getScannedClues;
window.saveScannedClues = saveScannedClues;
window.markClueAsScanned = markClueAsScanned;
window.getUnlockedClues = getUnlockedClues;
window.markClueAsUnlocked = markClueAsUnlocked;

})();
