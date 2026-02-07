const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');

// Read all rumor YAML files from the rumors directory
const rumorsDir = path.join(__dirname, 'rumors');
const files = fs.readdirSync(rumorsDir);

const rumors = [];

files.forEach(file => {
  if (file.endsWith('.yaml') || file.endsWith('.yml')) {
    const filePath = path.join(rumorsDir, file);
    try {
      const fileContents = fs.readFileSync(filePath, 'utf8');
      const rumor = yaml.load(fileContents);
      if (rumor && rumor.id) {
        rumors.push(rumor);
      }
    } catch (error) {
      console.error(`Error reading ${filePath}:`, error.message);
    }
  }
});

// Sort by id for consistent ordering
rumors.sort((a, b) => {
  if (a.id < b.id) return -1;
  if (a.id > b.id) return 1;
  return 0;
});

module.exports = rumors;
