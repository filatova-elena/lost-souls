const path = require('path');
const loadYamlDir = require('../_build/loadYamlDir');

// When Eleventy loads this file, __dirname points to src/_data
const charactersDir = path.join(__dirname, 'characters');
const characters = loadYamlDir(charactersDir, false);

module.exports = characters;
