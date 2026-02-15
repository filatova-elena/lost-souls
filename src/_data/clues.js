const path = require('path');
const loadYamlDir = require('../utils/loadYamlDir');

// When Eleventy loads this file, __dirname points to src/_data
const cluesDir = path.join(__dirname, 'clues');
const clues = loadYamlDir(cluesDir, true);

module.exports = clues;
