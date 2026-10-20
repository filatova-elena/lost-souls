/**
 * Clue page initialization
 * Resolves clue access state and sets data-state attribute on the page.
 * CSS handles all visibility based on data-state.
 */
(function() {
'use strict';

const AccessState = {
  UNLOCKED: 'unlocked',
  SKILL_LOCKED: 'skill-locked'
};

const STORAGE_KEYS = window.STORAGE_KEYS || {
  SCANNED: 'scanned'
};

// ============================================================================
// Utility
// ============================================================================

function joinWithOr(items) {
  if (window.joinWithOr) return window.joinWithOr(items);
  if (items.length <= 1) return items[0] || '';
  if (items.length === 2) return `${items[0]} or ${items[1]}`;
  return `${items.slice(0, -1).join(', ')}, or ${items[items.length - 1]}`;
}

function buildLockSectionContent(message, suggestedCharacters) {
  let html = `
    <div class="lock-assembly">
      <div class="lock-glow"></div>
      <div class="lock-shackle"></div>
      <div class="lock-body"><div class="keyhole"></div></div>
    </div>
  `;
  if (message) html += `<p>${message}</p>`;
  if (suggestedCharacters?.length) {
    const bold = suggestedCharacters.map(n => `<strong>${n}</strong>`);
    html += `<span class="character-callout">Seek out ${joinWithOr(bold)}</span>`;
  }
  return html;
}

// ============================================================================
// Storage
// ============================================================================

// Saves the scan order (all) and what the history page needs to show the clue (details)
function recordClueScan(clue) {
  const scanned = window.getScannedClues();
  if (!scanned.all.includes(clue.id)) {
    scanned.all.push(clue.id);
  }
  scanned.details = scanned.details || {};
  scanned.details[clue.id] = { title: clue.title, type: clue.type };
  window.saveToLocalStorage(STORAGE_KEYS.SCANNED, scanned);
  return scanned;
}

// ============================================================================
// Access control
// ============================================================================

function determineAccessState(clueData, noAccessMessages) {
  if (window.resolveClueState) {
    return window.resolveClueState(clueData, {
      userSkills: window.getCharacterProfile()?.skills || [],
      noAccessMessages,
      hasSkillAccessFn: window.hasSkillAccess,
      parseSkillFn: window.parseSkill
    });
  }
  return { name: AccessState.UNLOCKED };
}

// ============================================================================
// Page init
// ============================================================================

function initCluePage() {
  const page = document.querySelector('.clue-page');
  if (!page) return;

  const clueData = window.__clueData;
  const noAccessMessages = window.__noAccessMessages;
  if (!clueData) return;

  // Determine access state
  const state = determineAccessState(clueData, noAccessMessages);
  page.dataset.state = state.name;

  // Skill-locked: populate lock section
  if (state.name === AccessState.SKILL_LOCKED) {
    const lockSection = page.querySelector('.clue-lock');
    if (lockSection) {
      lockSection.innerHTML = buildLockSectionContent(
        state.message, state.suggestedCharacters
      );
    }
  }

  // Unlocked: mark as scanned, handle effects
  if (state.name === AccessState.UNLOCKED) {
    const scanned = window.getScannedClues();
    if (!scanned.all?.includes(clueData.id)) {
      recordClueScan(clueData);
      if (window.isTrackClue(clueData.id) && window.spawnParticles) {
        window.renderProgressTracker(true);
        window.spawnParticles();
      }
    }
  }

  // Sign-in character display
  if (clueData.id === 'SIGN_IN') {
    const characterDisplay = document.getElementById('sign-in-character-name');
    if (characterDisplay && window.getCharacterProfile) {
      const profile = window.getCharacterProfile();
      if (profile?.characterId && window.__characters) {
        const character = window.__characters.find(c => c.id === profile.characterId);
        characterDisplay.textContent = character ? character.title : profile.characterId;
      } else {
        characterDisplay.textContent = 'None';
      }
    }
  }
}

document.addEventListener('DOMContentLoaded', initCluePage);
})();
