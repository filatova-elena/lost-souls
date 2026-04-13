/**
 * Pure clue access logic for both build-time (Eleventy) and client-side use
 * This module provides a single source of truth for clue access state resolution
 * All functions are pure and accept dependencies as parameters for easy testing
 */

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
 * Determines the access state of a clue based on gates and skills
 * Checks in order: story gate → skill requirements
 */
function resolveClueState(clueData, options) {
  const {
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

// Support both Node.js (Eleventy) and browser environments
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    resolveClueState,
    buildSkillLockedMessage,
    randomItem,
    joinWithOr
  };
} else if (typeof window !== 'undefined') {
  window.resolveClueState = resolveClueState;
  window.buildSkillLockedMessage = buildSkillLockedMessage;
  window.randomItem = randomItem;
  window.joinWithOr = joinWithOr;
}
