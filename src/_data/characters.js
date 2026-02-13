const path = require('path');
const loadYamlDir = require('../utils/loadYamlDir');

// __dirname points to src/_data when this file is loaded by Eleventy
const charactersDir = path.join(__dirname, 'characters');
const characters = loadYamlDir(charactersDir, false);

module.exports = characters;
