/**
 * Eleventy filters - extracted from .eleventy.js for better organization
 */

const markdownIt = require("markdown-it");
const { charactersWithAccess, formatCharacterSkills } = require("../lib/skills");

const markdownItOptions = {
  html: true,
  breaks: true,
  linkify: true
};

const md = new markdownIt(markdownItOptions);

// ============================================================================
// Helper functions
// ============================================================================

/**
 * Check if an item is marked as key for a quest hashtag
 * Handles both array and single string values for backwards compatibility
 * @param {Object} item - Item to check
 * @param {string} questHashtag - Quest hashtag to check against
 * @returns {boolean} True if item is key for the quest
 */
function isKeyFor(item, questHashtag) {
  if (!item?.is_key || !questHashtag) return false;
  return Array.isArray(item.is_key)
    ? item.is_key.includes(questHashtag)
    : item.is_key === questHashtag;
}

// ============================================================================
// Filters
// ============================================================================

const filters = {
  // JSON stringify filter (clearer name than Nunjucks' built-in dump)
  json: function(value) {
    return JSON.stringify(value);
  },

  // Markdown filter - renders markdown strings to HTML
  markdown: function(value) {
    if (!value) return "";
    return md.render(value);
  },

  // Get clue by filename - throws error if not found
  getClue: function(filename, cluesData) {
    if (!filename || !cluesData) {
      throw new Error(`getClue: Missing filename or cluesData. filename=${filename}, cluesData=${!!cluesData}`);
    }
    const clue = cluesData.byFilename?.get(filename);
    if (!clue) {
      throw new Error(`Clue not found: "${filename}". Available clues: ${Array.from(cluesData.byFilename?.keys() || []).slice(0, 10).join(', ')}...`);
    }
    return clue;
  },

  // Get rumor by filename
  getRumor: function(filename, rumorsData) {
    if (!filename || !rumorsData) return null;
    return rumorsData.byFilename?.get(filename) || null;
  },

  // Find clue by ID from clues collection
  findByClueId: function(clues, clueId) {
    if (!Array.isArray(clues) || !clueId) return null;
    return clues.find(clue => clue.id === clueId) || null;
  },

  // Find quest by ID
  findQuestById: function(quests, questId) {
    if (!quests || !Array.isArray(quests) || !questId) return null;
    return quests.find(q => q.id === questId) || null;
  },

  // Filter items by act
  filterByAct: function(items, actKey) {
    if (!Array.isArray(items)) return [];
    return items.filter(item => item.act === actKey);
  },

  // Check if item is key for a quest
  isKeyForQuest: function(item, questHashtag) {
    return isKeyFor(item, questHashtag);
  },

  // Filter items by quest hashtag (all related items)
  filterByQuestHashtag: function(items, questHashtag) {
    if (!Array.isArray(items) || !questHashtag) return [];
    return items.filter(item => {
      return item.hashtags && item.hashtags.includes(questHashtag);
    });
  },

  // Filter items by quest hashtag and is_key
  filterByQuestKey: function(items, questHashtag) {
    if (!Array.isArray(items) || !questHashtag) return [];
    return items.filter(item => {
      // Must have the quest hashtag
      if (!item.hashtags || !item.hashtags.includes(questHashtag)) return false;
      // Must be marked as key for this quest
      return isKeyFor(item, questHashtag);
    });
  },

  // Filter items that are marked as key clues for a quest (checks is_key only, not hashtags)
  filterKeyClues: function(items, questHashtag) {
    if (!Array.isArray(items) || !questHashtag) return [];
    return items.filter(item => isKeyFor(item, questHashtag));
  },

  // Check if a key is a metadata key (for clue organization template)
  isMetaKey: function(key) {
    return ["name", "purpose", "constraints", "notes"].includes(key);
  },

  // Concatenate arrays (for building tag lists in templates)
  concat: function(arr, items) {
    if (!Array.isArray(arr)) return items || [];
    if (!Array.isArray(items)) return arr;
    return arr.concat(items);
  },

  // Merge objects (for building object structures in templates)
  merge: function(obj, addition) {
    if (!obj || typeof obj !== 'object') return addition || {};
    if (!addition || typeof addition !== 'object') return obj;
    return { ...obj, ...addition };
  },

  // Create an object with a single key-value pair (for dynamic keys in templates)
  obj: function(key, value) {
    if (!key) return {};
    const result = {};
    result[key] = value;
    return result;
  },

  // Convert object to array of [key, value] pairs for iteration
  items: function(obj) {
    if (!obj || typeof obj !== 'object') return [];
    return Object.entries(obj);
  },

  // Get emoji icon for clue type
  typeIcon: function(type) {
    if (!type) return "📝";
    const t = type.toLowerCase();
    if (t.includes("vision")) return "👁️";
    if (t.includes("artifact") || t.includes("object")) return "🏺";
    if (t.includes("administrative")) return "📋";
    if (t.includes("document") || t.includes("medical") || t.includes("legal") || t.includes("financial")) return "📄";
    if (t.includes("botanical")) return "🌿";
    if (t.includes("newspaper")) return "📰";
    return "📝";
  },

  // Pre-compute which characters have access to a clue's required skills
  // This runs at build time to avoid client-side iteration
  // Uses shared skills module for single source of truth
  charactersWithAccess: charactersWithAccess,

  // Convert character skills array to readable strings using skills.yaml
  formatCharacterSkills: formatCharacterSkills,

  // Truncate text to specified length
  truncate: function(value, length) {
    if (!value) return "";
    const str = String(value);
    if (str.length <= length) return str;
    return str.substring(0, length - 3) + "...";
  }
};

module.exports = filters;
