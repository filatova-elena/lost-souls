const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');

// Recursively read all YAML files from the clues directory
function getAllYamlFiles(dir, fileList = []) {
  const files = fs.readdirSync(dir);
  
  files.forEach(file => {
    const filePath = path.join(dir, file);
    const stat = fs.statSync(filePath);
    
    if (stat.isDirectory()) {
      getAllYamlFiles(filePath, fileList);
    } else if (file.endsWith('.yaml') || file.endsWith('.yml')) {
      fileList.push(filePath);
    }
  });
  
  return fileList;
}

const cluesDir = path.join(__dirname, 'clues');
const allFiles = getAllYamlFiles(cluesDir);

const clues = [];

allFiles.forEach(filePath => {
  try {
    const fileContents = fs.readFileSync(filePath, 'utf8');
    const clue = yaml.load(fileContents);
    
    if (clue && clue.id) {
      clues.push(clue);
    }
  } catch (error) {
    console.error(`Error reading ${filePath}:`, error.message);
  }
});

// Sort by id for consistent ordering
clues.sort((a, b) => {
  if (a.id < b.id) return -1;
  if (a.id > b.id) return 1;
  return 0;
});

module.exports = clues;
