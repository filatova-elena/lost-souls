/**
 * Clue history page (/history/)
 * Lists the clues this player has already opened, newest first, each linking
 * back to its clue page. The title and type were saved when the clue was scanned.
 */
(function() {
'use strict';

function isAdministrative(details) {
  return Boolean(details && details.type && details.type.includes('Administrative'));
}

function buildItem(id, details, baseUrl) {
  const item = document.createElement('li');
  item.className = 'list-item';

  const main = document.createElement('div');
  main.className = 'item-main';

  const link = document.createElement('a');
  link.href = `${baseUrl}clues/${id}/`;
  link.textContent = (details && details.title) || id;
  main.appendChild(link);

  if (details && details.type) {
    const type = document.createElement('span');
    type.className = 'muted type-label';
    type.textContent = ` \u2014 ${details.type}`;
    main.appendChild(type);
  }

  item.appendChild(main);
  return item;
}

document.addEventListener('DOMContentLoaded', function() {
  const page = document.getElementById('history');
  const scanned = window.getScannedClues();
  const details = scanned.details || {};

  // Scan order is oldest first, and the sign-in page is not a clue the player found
  const ids = scanned.all.filter(id => !isAdministrative(details[id])).reverse();

  const list = page.querySelector('.clue-list');
  ids.forEach(id => list.appendChild(buildItem(id, details[id], page.dataset.baseUrl)));
  page.dataset.state = ids.length ? 'list' : 'empty';
});

})();
