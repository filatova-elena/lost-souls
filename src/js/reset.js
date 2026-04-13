'use strict';

document.addEventListener('DOMContentLoaded', () => {
  if (!window.getCharacterProfile || !window.getScannedClues) {
    console.error('reset.js: required functions from main.js not available');
    return;
  }

  displayCharacterInfo();
  displayStats();

  document.getElementById('reset-btn')
    ?.addEventListener('click', handleReset);
});

function displayCharacterInfo() {
  const display = document.getElementById('character-display');
  if (!display) return;

  const profile = window.getCharacterProfile();
  if (!profile) {
    display.innerHTML = '<p class="muted">No character selected</p>';
    return;
  }

  const characters = window.__characters || [];
  const character = characters.find(c => c.id === profile.characterId);

  if (!character) {
    display.innerHTML = `<p><strong>Character ID:</strong> ${profile.characterId}</p>`;
    return;
  }

  const baseUrl = window.__siteBaseUrl || '';
  const imageHtml = character.image
    ? `<img src="${baseUrl}${character.image}" alt="${character.title}" class="character-avatar">`
    : '';

  display.innerHTML = `
    <div class="character-card">
      ${imageHtml}
      <div>
        <h3 class="character-name">${character.title}</h3>
        <p class="character-personality">${character.personality || ''}</p>
      </div>
    </div>
  `;
}

function displayStats() {
  const scanned = window.getScannedClues();
  const progress = window.__progressData || {};
  const profile = window.getCharacterProfile();

  setText('total-clues', scanned.all?.length || 0);

  const charId = profile?.characterId;
  const track = charId ? progress.characterTracks?.[charId] : null;
  if (track) {
    const found = track.clueChain.filter(id => scanned.all?.includes(id)).length;
    setText('track-clues', `${found} / ${track.clueChain.length}`);
  } else {
    setText('track-clues', '—');
  }
}

function setText(id, value) {
  const el = document.getElementById(id);
  if (el) el.innerHTML = `<strong>${value}</strong>`;
}

function handleReset() {
  if (!confirm('Are you sure? This clears all progress, clues, and your character.')) return;
  if (window.resetInvestigation) {
    window.resetInvestigation();
    alert('Investigation reset! Reloading…');
    window.location.reload();
  }
}
