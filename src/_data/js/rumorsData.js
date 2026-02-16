const path = require('path');
const loadYamlDir = require('../../utils/loadYamlDir');

const rumorsDir = path.join(__dirname, '..', 'rumors');
const rumors = loadYamlDir(rumorsDir, false);

module.exports = rumors;
