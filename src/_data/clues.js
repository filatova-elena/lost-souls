const path = require('path');
const loadYamlDir = require('../utils/loadYamlDir');

// __dirname points to src/_data when this file is loaded by Eleventy
const cluesDir = path.join(__dirname, 'clues');
const clues = loadYamlDir(cluesDir, true);

module.exports = clues;
