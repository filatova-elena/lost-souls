/**
 * Pure clue access logic for both build-time (Eleventy) and client-side use
 * This module provides a single source of truth for clue access state resolution
 * All functions are pure and accept dependencies as parameters for easy testing
 */

/**
 * Returns a random item from an array
 * @param {Array} array - The array to select from
 * @returns {*} A random item from the array
 */
function randomItem(array) {
  return array[Math.floor(Math.random() * array.length)];
}

/**
 * Joins an array of items with commas and "or" before the last item
 * @param {Array<string>} items - Array of strings to join
 * @returns {string} Formatted string (e.g., "A, B, or C" or "A or B")
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
 * Builds a user-friendly message explaining why a clue is skill-locked
 * @param {Array<string>} missingSkills - Array of skill IDs that are required but missing
 * @param {string} clueType - Type of clue (e.g., "Document", "Artifact")
 * @param {Object} noAccessMessages - Message templates from refs.no_access_messages
 * @param {Function} parseSkillFn - Function to parse skill strings (defaults to window.parseSkill)
 * @param {Function} randomFn - Function to select random item from array (defaults to randomItem)
 * @returns {string} Formatted message explaining the skill requirements
 */
function buildSkillLockedMessage(missingSkills, clueType, noAccessMessages, parseSkillFn = null, randomFn = null) {
  const parseSkill = parseSkillFn || (typeof window !== 'undefined' ? window.parseSkill : null);
  const random = randomFn || randomItem;

  if (!noAccessMessages || !noAccessMessages.skill_phrases || !noAccessMessages.wrappers) {
    return "You don't have the required skills to access this clue.";
  }
  
  if (!parseSkill) {
    return "You don't have the required skills to access this clue.";
  }

  const phrases = [];
  for (const skill of missingSkills) {
    const parsed = parseSkill(skill);
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
      phrases.push(random(phraseArray));
    }
  }
  
  if (phrases.length === 0) {
    phrases.push("the required expertise");
  }
  
  let wrappers = noAccessMessages.wrappers[clueType];
  if (!wrappers || wrappers.length === 0) {
    wrappers = noAccessMessages.wrappers._default || ["The meaning here escapes you. You'd need {requirements}."];
  }
  
  const wrapper = random(wrappers);
  const requirements = joinWithOr(phrases);
  return wrapper.replace('{requirements}', requirements);
}

/**
 * Determines the access state of a clue based on gates, skills, and unlock status
 * Checks in order: manually unlocked → story gate → skill requirements
 * @param {Object} clueData - Clue data object (id, act, skills, etc.)
 * @param {Object} options - Options object with dependencies
 * @param {Array<string>} options.unlockedClues - Array of manually unlocked clue IDs
 * @param {Array<string>} options.unlockedActs - Array of unlocked act keys (e.g., ["act_ii_mystery_emerges"])
 * @param {Array<string>} options.userSkills - Array of user's skill IDs
 * @param {Object} options.noAccessMessages - Message templates for skill-locked state
 * @param {Function} options.hasSkillAccessFn - Function to check skill access (defaults to window.hasSkillAccess)
 * @param {Function} options.parseSkillFn - Function to parse skill strings (for message building)
 * @param {Function} options.randomFn - Function to select random item (for message building)
 * @returns {Object} State object with name and optional message/suggestedCharacters
 */
function resolveClueState(clueData, options) {
  const {
    unlockedClues = [],
    unlockedActs = [],
    userSkills = [],
    noAccessMessages = {},
    hasSkillAccessFn = null,
    parseSkillFn = null,
    randomFn = null
  } = options;

  const hasSkillAccess = hasSkillAccessFn || (typeof window !== 'undefined' ? window.hasSkillAccess : null);
  
  if (!hasSkillAccess) {
    throw new Error('hasSkillAccess function is required');
  }

  // Check if manually unlocked (octogram bypass)
  if (unlockedClues.includes(clueData.id)) {
    return { name: 'unlocked' };
  }

  // Check if this clue's act is unlocked
  // Prologue and Act I are always unlocked
  if (clueData.act && clueData.act !== 'act_prologue' && clueData.act !== 'act_i_setting') {
    if (!unlockedActs.includes(clueData.act)) {
      return { name: 'gated' };
    }
  }

  // Check skill requirements
  const clueSkills = clueData.skills || [];
  const hasAccess = hasSkillAccess(clueSkills, userSkills);

  if (!hasAccess) {
    return {
      name: 'skill-locked',
      message: buildSkillLockedMessage(clueSkills, clueData.type, noAccessMessages, parseSkillFn, randomFn),
      suggestedCharacters: clueData.accessChars
    };
  }

  return { name: 'unlocked' };
}

/**
 * Gets the quest hashtag that this clue is a key clue for (main or side quest)
 * @param {Object} clueData - Clue data object (must have is_key array)
 * @param {Object} options - Options object with dependencies
 * @param {string} options.mainQuestHashtag - Main quest hashtag (defaults to 'main_quest')
 * @param {Object} options.sideQuests - Object mapping characterId to side quest data
 * @param {string|null} options.characterId - Current character ID (null if no character)
 * @returns {string|null} Quest hashtag if this clue is a key clue for a quest, null otherwise
 */
function getQuestClueIsKeyFor(clueData, options = {}) {
  const {
    mainQuestHashtag = 'main_quest',
    sideQuests = {},
    characterId = null
  } = options;

  const keyHashtags = clueData.is_key || [];
  if (keyHashtags.length === 0) return null;

  // Check main quest first
  if (keyHashtags.includes(mainQuestHashtag)) return mainQuestHashtag;

  // Check side quest for current character
  if (characterId) {
    const sideQuest = sideQuests[characterId];
    if (sideQuest?.hashtag && keyHashtags.includes(sideQuest.hashtag)) {
      return sideQuest.hashtag;
    }
  }

  return null;
}

// Support both Node.js (Eleventy) and browser environments
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    resolveClueState,
    buildSkillLockedMessage,
    getQuestClueIsKeyFor,
    randomItem,
    joinWithOr
  };
} else if (typeof window !== 'undefined') {
  window.resolveClueState = resolveClueState;
  window.buildSkillLockedMessage = buildSkillLockedMessage;
  window.getQuestClueIsKeyFor = getQuestClueIsKeyFor;
  window.randomItem = randomItem;
  window.joinWithOr = joinWithOr;
}
