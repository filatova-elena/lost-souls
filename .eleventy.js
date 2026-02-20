const markdownIt = require("markdown-it");
const yaml = require("js-yaml");
const { charactersWithAccess } = require("./src/lib/skills");

const markdownItOptions = {
  html: true,
  breaks: true,
  linkify: true
};

const md = new markdownIt(markdownItOptions);

module.exports = function(eleventyConfig) {
  // Register YAML data file format
  eleventyConfig.addDataExtension("yaml,yml", (contents) => {
    return yaml.load(contents);
  });

  // Pass through static assets
  eleventyConfig.addPassthroughCopy("src/css");
  eleventyConfig.addPassthroughCopy("src/js");
  eleventyConfig.addPassthroughCopy("src/assets");
  eleventyConfig.addPassthroughCopy("src/fonts");
  eleventyConfig.addPassthroughCopy("src/quests/*.css");
  eleventyConfig.addPassthroughCopy("src/clues/*.css");
  eleventyConfig.addPassthroughCopy("src/refs/*.css");
  eleventyConfig.addPassthroughCopy("src/book/*.css");
  
  // Copy universal skills.js to output js directory
  eleventyConfig.addPassthroughCopy({
    "src/lib/skills.js": "js/skills.js"
  });

  // Add filters
  eleventyConfig.addFilter("json", function(value) {
    return JSON.stringify(value);
  });

  // Markdown filter - renders markdown strings to HTML
  eleventyConfig.addFilter("markdown", function(value) {
    if (!value) return "";
    return md.render(value);
  });

  // Get clue by filename - throws error if not found
  eleventyConfig.addFilter("getClue", function(filename, cluesData) {
    if (!filename || !cluesData) {
      throw new Error(`getClue: Missing filename or cluesData. filename=${filename}, cluesData=${!!cluesData}`);
    }
    const clue = cluesData.byFilename?.get(filename);
    if (!clue) {
      throw new Error(`Clue not found: "${filename}". Available clues: ${Array.from(cluesData.byFilename?.keys() || []).slice(0, 10).join(', ')}...`);
    }
    return clue;
  });

  // Get rumor by filename
  eleventyConfig.addFilter("getRumor", function(filename, rumorsData) {
    if (!filename || !rumorsData) return null;
    return rumorsData.byFilename?.get(filename) || null;
  });

  // Find quest by ID
  eleventyConfig.addFilter("findQuestById", function(quests, questId) {
    if (!quests || !Array.isArray(quests) || !questId) return null;
    return quests.find(q => q.id === questId) || null;
  });

  // Filter items by act
  eleventyConfig.addFilter("filterByAct", function(items, actKey) {
    if (!Array.isArray(items)) return [];
    return items.filter(item => item.act === actKey);
  });

  // Check if item is key for a quest
  eleventyConfig.addFilter("isKeyForQuest", function(item, questHashtag) {
    if (!item || !questHashtag || !item.is_key) return false;
    if (Array.isArray(item.is_key)) {
      return item.is_key.includes(questHashtag);
    }
    return item.is_key === questHashtag;
  });

  // Filter items by quest hashtag (all related items)
  eleventyConfig.addFilter("filterByQuestHashtag", function(items, questHashtag) {
    if (!Array.isArray(items) || !questHashtag) return [];
    return items.filter(item => {
      // Must have the quest hashtag
      return item.hashtags && item.hashtags.includes(questHashtag);
    });
  });

  // Filter items by quest hashtag and is_key
  eleventyConfig.addFilter("filterByQuestKey", function(items, questHashtag) {
    if (!Array.isArray(items) || !questHashtag) return [];
    return items.filter(item => {
      // Must have the quest hashtag
      if (!item.hashtags || !item.hashtags.includes(questHashtag)) return false;
      // Must be marked as key for this quest
      if (!item.is_key) return false;
      // Handle both array and single value (for backwards compatibility)
      if (Array.isArray(item.is_key)) {
        return item.is_key.includes(questHashtag);
      }
      return item.is_key === questHashtag;
    });
  });

  // Filter items that are marked as key clues for a quest (checks is_key only, not hashtags)
  eleventyConfig.addFilter("filterKeyClues", function(items, questHashtag) {
    if (!Array.isArray(items) || !questHashtag) return [];
    return items.filter(item => {
      if (!item.is_key) return false;
      // Handle both array and single value
      if (Array.isArray(item.is_key)) {
        return item.is_key.includes(questHashtag);
      }
      return item.is_key === questHashtag;
    });
  });

  // Check if a key is a metadata key (for clue organization template)
  eleventyConfig.addFilter("isMetaKey", function(key) {
    return ["name", "purpose", "constraints", "notes"].includes(key);
  });

  // Concatenate arrays (for building tag lists in templates)
  eleventyConfig.addFilter("concat", function(arr, items) {
    if (!Array.isArray(arr)) return items || [];
    if (!Array.isArray(items)) return arr;
    return arr.concat(items);
  });

  // Merge objects (for building object structures in templates)
  eleventyConfig.addFilter("merge", function(obj, addition) {
    if (!obj || typeof obj !== 'object') return addition || {};
    if (!addition || typeof addition !== 'object') return obj;
    return { ...obj, ...addition };
  });

  // Create an object with a single key-value pair (for dynamic keys in templates)
  eleventyConfig.addFilter("obj", function(key, value) {
    if (!key) return {};
    const result = {};
    result[key] = value;
    return result;
  });

  // Convert object to array of [key, value] pairs for iteration
  eleventyConfig.addFilter("items", function(obj) {
    if (!obj || typeof obj !== 'object') return [];
    return Object.entries(obj);
  });

  // Get emoji icon for clue type
  eleventyConfig.addFilter("typeIcon", function(type) {
    if (!type) return "📝";
    const t = type.toLowerCase();
    if (t.includes("vision")) return "👁️";
    if (t.includes("artifact") || t.includes("object")) return "🏺";
    if (t.includes("administrative")) return "📋";
    if (t.includes("document") || t.includes("medical") || t.includes("legal") || t.includes("financial")) return "📄";
    if (t.includes("botanical")) return "🌿";
    if (t.includes("newspaper")) return "📰";
    return "📝";
  });

  // Pre-compute which characters have access to a clue's required skills
  // This runs at build time to avoid client-side iteration
  // Uses shared skills module for single source of truth
  eleventyConfig.addFilter("charactersWithAccess", charactersWithAccess);

  // Convert character skills array to readable strings using skills.yaml
  eleventyConfig.addFilter("formatCharacterSkills", function(skills, skillsData) {
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
  });

  // Compute which story gates a clue unlocks
  // Takes a clue ID and storyGates object, returns array of gate keys
  eleventyConfig.addFilter("unlocksGates", function(clueId, storyGates) {
    if (!clueId || !storyGates || typeof storyGates !== 'object') {
      return [];
    }
    
    const unlockedGates = [];
    
    // Iterate through all gates and check if this clue ID appears in their clues array
    for (const [gateKey, gateData] of Object.entries(storyGates)) {
      if (gateData && Array.isArray(gateData.clues) && gateData.clues.includes(clueId)) {
        unlockedGates.push(gateKey);
      }
    }
    
    return unlockedGates;
  });

  // Add collection for characters
  eleventyConfig.addCollection("characters", function(collectionApi) {
    return collectionApi.getAll().filter(item => item.data.type === "character");
  });

  // Add collection for clues
  eleventyConfig.addCollection("clues", function(collectionApi) {
    return collectionApi.getAll().filter(item => item.data.type === "clue");
  });

  // Add collection for book chapters
  eleventyConfig.addCollection("chapters", function(collectionApi) {
    return collectionApi.getAll().filter(item => item.data.type === "chapter");
  });

  return {
    pathPrefix: process.env.PATH_PREFIX || "/",
    dir: {
      input: "src",
      output: "_site",
      includes: "_includes",
      data: "_data"
    },
    templateFormats: ["njk", "md", "html"],
    htmlTemplateEngine: "njk",
    markdownTemplateEngine: "njk",
    dataFileExtensions: ["yaml", "yml", "json", "js", "cjs", "mjs", "ts"]
  };
};
