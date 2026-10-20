const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');
const clues = require('../src/_data/clues');

const questsDir = path.join(__dirname, '../src/_data/quests');
const keyClueIds = fs.readdirSync(questsDir)
  .filter(file => file.startsWith('track_'))
  .flatMap(file => yaml.load(fs.readFileSync(path.join(questsDir, file), 'utf8')).clue_chain);

test('every key clue on a track can be scanned by anyone: none needs a skill', () => {
  const blocked = keyClueIds.filter(id => {
    const clue = clues.find(candidate => candidate.id === id);
    return !clue || (clue.skills || []).length > 0;
  });
  expect(blocked).toEqual([]);
});
