const path = require('path');
const loadYamlDir = require('../utils/loadYamlDir');
const fs = require('fs');
const yaml = require('js-yaml');

// Load characters and quests
const charactersDir = path.join(__dirname, 'characters');
const characters = loadYamlDir(charactersDir, false);

const questsDir = path.join(__dirname, 'quests');
const questFiles = fs.readdirSync(questsDir);
const questsById = {};

questFiles.forEach(file => {
  if (file.endsWith('.yaml') || file.endsWith('.yml')) {
    const filePath = path.join(questsDir, file);
    const fileContents = fs.readFileSync(filePath, 'utf8');
    const quest = yaml.load(fileContents);
    if (quest && quest.id) {
      questsById[quest.id] = quest;
    }
  }
});

// Load clues to count key clues for each side quest
// Note: This will be called during Eleventy build, clues data should be available
// We'll compute totals in the template instead since clues data structure may vary
// This file just provides the mapping: character ID → quest hashtag
const characterSideQuests = {};

characters.forEach(character => {
  if (character.objectives && character.objectives.private) {
    const privateQuestId = character.objectives.private;
    const quest = questsById[privateQuestId];
    if (!quest) {
      console.warn(`[character_side_quests] Character "${character.id}" references quest "${privateQuestId}" but no quest with that id was found. Available quest IDs: ${Object.keys(questsById).join(', ')}`);
    } else {
      // Use hashtag if available, otherwise fall back to quest id (e.g., main_quest uses its id as hashtag)
      const hashtag = quest.hashtag || quest.id;
      characterSideQuests[character.id] = {
        hashtag: hashtag,
        questId: quest.id,
        objectiveShort: quest.objective_short || 'Side Quest'
      };
    }
  }
});

module.exports = characterSideQuests;
