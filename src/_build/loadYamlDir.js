const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');

function loadYamlDir(dir, recursive = true) {
  if (typeof dir !== 'string') {
    throw new Error(`loadYamlDir: dir must be a string, got ${typeof dir}: ${JSON.stringify(dir)}`);
  }
  
  const files = fs.readdirSync(dir);
  let items = [];

  for (const file of files) {
    const filePath = path.join(dir, file);

    if (recursive && fs.statSync(filePath).isDirectory()) {
      items = items.concat(loadYamlDir(filePath, recursive));
    } else if (file.endsWith('.yaml') || file.endsWith('.yml')) {
      try {
        const item = yaml.load(fs.readFileSync(filePath, 'utf8'));
        if (item) {
          item.filename = path.basename(filePath, path.extname(filePath));
          items.push(item);
        }
      } catch (error) {
        throw new Error(`Error reading ${filePath}: ${error.message}`);
      }
    }
  }

  items.sort((a, b) => a.filename.localeCompare(b.filename));
  items.byFilename = new Map(items.map(i => [i.filename, i]));

  return items;
}

module.exports = loadYamlDir;
