const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');

function loadYamlFiles(dir, recursive = true) {
  if (typeof dir !== 'string') {
    throw new Error(`loadYamlFiles: dir must be a string, got ${typeof dir}: ${JSON.stringify(dir)}`);
  }
  
  const files = fs.readdirSync(dir);
  let items = [];

  for (const file of files) {
    const filePath = path.join(dir, file);

    if (recursive && fs.statSync(filePath).isDirectory()) {
      items = items.concat(loadYamlFiles(filePath, recursive));
    } else if (file.endsWith('.yaml') || file.endsWith('.yml')) {
      try {
        const item = yaml.load(fs.readFileSync(filePath, 'utf8'));
        if (item) {
          item.fileName = path.basename(filePath, path.extname(filePath));
          items.push(item);
        }
      } catch (error) {
        throw new Error(`Error reading ${filePath}: ${error.message}`);
      }
    }
  }

  items.sort((a, b) => a.fileName.localeCompare(b.fileName));
  items.byFileName = new Map(items.map(i => [i.fileName, i]));

  return items;
}

module.exports = loadYamlFiles;
