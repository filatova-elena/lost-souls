const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');

// Read all YAML files from the quests directory
const questsDir = path.join(__dirname, 'quests');
const files = fs.readdirSync(questsDir);

const quests = {};

files.forEach(file => {
  if (file.endsWith('.yaml') || file.endsWith('.yml')) {
    const filePath = path.join(questsDir, file);
    const fileContents = fs.readFileSync(filePath, 'utf8');
    const quest = yaml.load(fileContents);
    
    if (quest && quest.id) {
      quests[quest.id] = quest;
    }
  }
});

// Convert to array for pagination
module.exports = Object.values(quests);
