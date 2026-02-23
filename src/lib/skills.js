/**
 * Shared skill-matching logic for both build-time (Eleventy) and client-side use
 * This module provides a single source of truth for skill parsing and access checking
 */

const SKILL_SUFFIX = { expert: '_2', basic: '_1', personal: '' };

/**
 * Parse a skill string into base name and level
 * @param {string} skill - Skill string (e.g., "botanical_2", "personal_romano")
 * @returns {Object|null} { base: string, level: number } or null if invalid
 */
function parseSkill(skill) {
  if (!skill || typeof skill !== 'string') return null;
  const match = skill.match(/^(.+?)(?:_(\d+))?$/);
  if (!match) return null;
  return { base: match[1], level: match[2] ? parseInt(match[2], 10) : 0 };
}

/**
 * Convert skills from nested format to flat array
 * @param {Array|Object} skills - Skills in nested format { expert: [], basic: [], personal: [] } or flat array
 * @returns {Array<string>} Flat array of skill strings
 */
function convertSkills(skills) {
  // If skills is already a flat array (new format), return it as-is
  if (Array.isArray(skills)) {
    return skills.filter(Boolean);
  }
  
  // Otherwise, convert from nested format (old format)
  return Object.entries(SKILL_SUFFIX).flatMap(([level, suffix]) =>
    (skills[level] || []).filter(Boolean).map(skill => `${skill}${suffix}`)
  );
}

/**
 * Check if user has access based on required skills (OR logic)
 * User needs at least ONE of the required skills
 * @param {Array<string>} requiredSkills - Array of required skills (e.g., ["history_1", "botanical_1"])
 * @param {Array<string>} userSkills - Array of user's skills
 * @returns {boolean} True if user has access
 */
function hasSkillAccess(requiredSkills, userSkills) {
  if (!requiredSkills || requiredSkills.length === 0) {
    // No skill requirements means accessible to everyone
    return true;
  }

  // Check if user has at least ONE of the required skills (OR logic)
  return requiredSkills.some(required => {
    const req = parseSkill(required);
    if (!req) return false;
    return userSkills.some(userSkill => {
      const user = parseSkill(userSkill);
      return user && user.base === req.base && user.level >= req.level;
    });
  });
}

/**
 * Find characters who have access to a clue's required skills
 * @param {Array<string>} clueSkills - Array of required skills for the clue
 * @param {Array<Object>} characters - Array of character objects
 * @returns {Array<string>} Array of character names (with "The" prefix removed) who have access
 */
function charactersWithAccess(clueSkills, characters) {
  if (!clueSkills || clueSkills.length === 0) return [];
  if (!characters || !Array.isArray(characters)) return [];
  
  return characters
    .filter(char => char.is_player !== false && char.skills)
    .filter(char => {
      const charSkills = convertSkills(char.skills);
      return hasSkillAccess(clueSkills, charSkills);
    })
    .map(char => {
      const title = char.title || char.id;
      return title.replace(/^The /, '');
    });
}

/**
 * Convert character skills array to readable strings using skills.yaml data
 * @param {Array|Object} skills - Skills in nested format { expert: [], basic: [], personal: [] } or flat array
 * @param {Object} skillsData - Skills data from skills.yaml
 * @returns {Array<string>} Array of formatted skill strings with icons
 */
function formatCharacterSkills(skills, skillsData) {
  if (!skills || !skillsData) return [];
  
  // Handle both flat array and nested object formats
  let skillIds = [];
  if (Array.isArray(skills)) {
    skillIds = skills;
  } else if (skills && typeof skills === 'object') {
    // Nested format: combine all levels
    skillIds = [
      ...(skills.expert || []),
      ...(skills.basic || []),
      ...(skills.personal || [])
    ];
  }
  
  const formatted = [];
  
  skillIds.forEach(skillId => {
    // Skip meta skills
    if (skillId && skillId.startsWith("is_character_")) return;
    
    // Extract level from skill ID (e.g., "art_2" -> level "2", "personal_romano" -> level "1")
    let level = "1"; // Default to level 1
    let baseSkillId = skillId;
    
    // Check if skill has level suffix
    const levelMatch = skillId.match(/_(1|2)$/);
    if (levelMatch) {
      level = levelMatch[1];
      baseSkillId = skillId.replace(/_[12]$/, "");
    } else if (skillId.startsWith("personal_")) {
      // Personal skills without suffix are always level 1
      level = "1";
      baseSkillId = skillId;
    }
    
    // Look up the skill in skills.yaml
    let skillInfo = skillsData[baseSkillId];
    
    // For personal skills, try without level suffix if not found
    if (!skillInfo && skillId.startsWith("personal_") && skillId.match(/_[12]$/)) {
      baseSkillId = skillId.replace(/_[12]$/, "");
      skillInfo = skillsData[baseSkillId];
    }
    
    if (skillInfo && skillInfo.level && skillInfo.level[level]) {
      const levelText = skillInfo.level[level];
      const icon = skillInfo.icon ? ` ${skillInfo.icon}` : "";
      formatted.push(`${levelText}${icon}`);
    } else if (skillInfo && skillInfo.title) {
      // Fallback to title if level not found
      const icon = skillInfo.icon ? ` ${skillInfo.icon}` : "";
      formatted.push(`${skillInfo.title}${icon}`);
    } else {
      // Fallback: format the ID
      formatted.push(skillId.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase()));
    }
  });
  
  return formatted;
}

// Support both Node.js (Eleventy) and browser environments
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    parseSkill,
    convertSkills,
    hasSkillAccess,
    charactersWithAccess,
    formatCharacterSkills,
    SKILL_SUFFIX
  };
} else if (typeof window !== 'undefined') {
  window.parseSkill = parseSkill;
  window.convertSkills = convertSkills;
  window.hasSkillAccess = hasSkillAccess;
  window.charactersWithAccess = charactersWithAccess;
  // formatCharacterSkills is only used in Eleventy, not in browser
}
