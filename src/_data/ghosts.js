const path = require('path');
const loadYamlDir = require('../_build/loadYamlDir');

// When Eleventy loads this file, __dirname points to src/_data
const ghostsDir = path.join(__dirname, 'ghosts');
const ghosts = loadYamlDir(ghostsDir, false);

// Create a map by ghost id for easy lookup
const ghostsById = {};
ghosts.forEach(ghost => {
  if (ghost.id) {
    ghostsById[ghost.id] = ghost;
  }
  if (ghost.ghost) {
    ghostsById[ghost.ghost] = ghost;
  }
});

module.exports = {
  all: ghosts,
  byId: ghostsById
};
