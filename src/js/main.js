const CHARACTER_PROFILE_KEY = 'character_profile';

const SKILL_SUFFIX = { expert: '_2', basic: '_1', personal: '' };

function convertSkills(skills) {
  return Object.entries(SKILL_SUFFIX).flatMap(([level, suffix]) =>
    (skills[level] || []).filter(Boolean).map(skill => `${skill}${suffix}`)
  );
}

function storeCharacterProfile(characterId, skills) {
  if (!characterId) {
    console.error('Character ID is required');
    return null;
  }

  const profile = {
    characterId,
    skills: convertSkills(skills)
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
 * Parse a skill string into base name and level
 * @param {string} skill - Skill string (e.g., "botanical_2", "personal_romano")
 * @returns {Object|null} { base: string, level: number } or null if invalid
 */
function parseSkill(skill) {
  const match = skill.match(/^(.+?)(?:_(\d+))?$/);
  if (!match) return null;
  return { base: match[1], level: match[2] ? parseInt(match[2], 10) : 0 };
}

/**
 * Check if user has access to a clue based on their skills
 * @param {Array<string>} requiredSkills - Array of required skills (e.g., ["history_1", "botanical_1", "personal_romano"])
 * @param {Array<string>} userSkills - Array of user's skills
 * @returns {Object} { hasAccess: boolean, missingSkills: Array<string> }
 */
function checkClueAccess(requiredSkills = [], userSkills = []) {
  const missingSkills = requiredSkills.filter(required => {
    const req = parseSkill(required);
    if (!req) return true;
    return !userSkills.some(userSkill => {
      const user = parseSkill(userSkill);
      return user && user.base === req.base && user.level >= req.level;
    });
  });

  return { hasAccess: missingSkills.length === 0, missingSkills };
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
    const parsed = parseSkill(skill);
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
  
  return wrapper.replace('{requirements}', requirements);
}

/**
 * Check clue access (pure logic, no DOM manipulation)
 * @param {Object} clueData - Clue data object with skills, type, etc.
 * @returns {Object} { hasAccess: boolean, missingSkills: Array<string>, message?: string }
 */
function checkAccess(clueData, noAccessMessages) {
  if (!clueData) {
    console.error('Clue data is required');
    return { hasAccess: false, missingSkills: [] };
  }
  
  const profile = getCharacterProfile();
  const userSkills = profile ? profile.skills : [];
  const requiredSkills = Array.isArray(clueData.skills) ? clueData.skills : [];
  
  const access = checkClueAccess(requiredSkills, userSkills);
  
  if (!access.hasAccess && noAccessMessages) {
    access.message = generateNoAccessMessage(access.missingSkills, clueData.type, noAccessMessages);
  }
  
  return access;
}

/**
 * Render clue access control in the DOM
 * @param {Object} access - Access check result from checkAccess()
 */
function renderClueAccess(access) {
  const narrationSections = document.querySelectorAll('.clue-narration');
  const contentSections = document.querySelectorAll('.clue-content');
  
  // Remove any existing no-access messages
  const existingMessage = document.querySelector('.clue-no-access');
  if (existingMessage) {
    existingMessage.remove();
  }
  
  if (access.hasAccess) {
    // Show all content
    narrationSections.forEach(section => section.style.display = '');
    contentSections.forEach(section => section.style.display = '');
  } else {
    // Hide content
    narrationSections.forEach(section => section.style.display = 'none');
    contentSections.forEach(section => section.style.display = 'none');
    
    // Add no-access message if available
    if (access.message) {
      const messageSection = document.createElement('section');
      messageSection.className = 'clue-no-access';
      messageSection.innerHTML = `<p>${access.message}</p>`;
      
      // Insert after header, before any hidden sections
      const header = document.querySelector('header');
      if (header && header.parentNode) {
        header.parentNode.insertBefore(messageSection, header.nextSibling);
      }
    }
  }
}

/**
 * Initialize clue access control on page load
 * @param {Object} clueData - Clue data object with skills, type, etc.
 * @param {Object} noAccessMessages - The no_access_messages data structure
 */
function initClueAccess(clueData, noAccessMessages) {
  const access = checkAccess(clueData, noAccessMessages);
  renderClueAccess(access);
  return access;
}
