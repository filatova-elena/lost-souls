const path = require('path');
const fs = require('fs');
const yaml = require('js-yaml');
const loadYamlDir = require('../_build/loadYamlDir');

const characters = loadYamlDir(path.join(__dirname, 'characters'), false);

// Load track quest files
const questsDir = path.join(__dirname, 'quests');
const tracks = {};
fs.readdirSync(questsDir).forEach(file => {
  if (!file.startsWith('track_')) return;
  const quest = yaml.load(fs.readFileSync(path.join(questsDir, file), 'utf8'));
  if (quest && quest.id) tracks[quest.id] = quest;
});

// Map each character to their track
const characterTracks = {};
characters.forEach(character => {
  const trackId = character.objectives?.track;
  if (!trackId || trackId === 'meta') return;
  const track = tracks[trackId];
  if (!track) {
    console.warn(`[character_tracks] Character "${character.id}" references track "${trackId}" but no track found.`);
    return;
  }
  characterTracks[character.id] = {
    trackId: track.id,
    aspect: track.aspect,
    clueChain: track.clue_chain,
    objective: track.objective
  };
});

module.exports = characterTracks;
