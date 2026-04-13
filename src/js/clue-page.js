/**
 * Clue page initialization
 * Resolves clue access state and sets data-state attribute on the page.
 * CSS handles all visibility based on data-state.
 */
(function() {
'use strict';

const AccessState = {
  UNLOCKED: 'unlocked',
  GATED: 'gated',
  SKILL_LOCKED: 'skill-locked'
};

const STORAGE_KEYS = window.STORAGE_KEYS || {
  UNLOCKED_ACTS: 'unlocked_acts',
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

function buildSkillLockedMessage(missingSkills, clueType, noAccessMessages) {
  if (window.buildSkillLockedMessage) {
    return window.buildSkillLockedMessage(missingSkills, clueType, noAccessMessages);
  }
  return "You don't have the required skills to access this clue.";
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

function recordClueScan(clueId) {
  const scanned = window.getScannedClues();
  if (!scanned.all.includes(clueId)) {
    scanned.all.push(clueId);
  }
  window.saveToLocalStorage(STORAGE_KEYS.SCANNED, scanned);
  return scanned;
}

// ============================================================================
// Track progress
// ============================================================================

function getCharacterTrack() {
  const progressData = window.__progressData || {};
  const profile = window.getCharacterProfile();
  const charId = profile?.characterId;
  if (!charId) return null;
  return progressData.characterTracks?.[charId] || null;
}

function isTrackClue(clueId) {
  const track = getCharacterTrack();
  return track?.clueChain?.includes(clueId) || false;
}

// ============================================================================
// Story gates
// ============================================================================

const ACT_DISPLAY_INFO = {
  'act_ii_mystery_emerges': { title: 'Part II Unlocked', subtitle: 'The investigation deepens' },
  'act_iii_investigation': { title: 'Part III Unlocked', subtitle: 'The mystery unfolds' },
  'act_iv_revelation': { title: 'Part IV Unlocked', subtitle: 'The truth emerges' },
  'act_v_conclusions': { title: 'Part V Unlocked', subtitle: 'The final chapter' },
  'act_v_aftermath': { title: 'Part V Unlocked', subtitle: 'The final chapter' }
};

function unlockStoryGate(actKey) {
  if (!actKey) return;
  const unlocked = window.getFromLocalStorage(STORAGE_KEYS.UNLOCKED_ACTS, []);
  if (!unlocked.includes(actKey)) {
    unlocked.push(actKey);
    window.saveToLocalStorage(STORAGE_KEYS.UNLOCKED_ACTS, unlocked);
    if (window.renderActUnlockAnimation) {
      const info = ACT_DISPLAY_INFO[actKey];
      if (info) {
        window.renderActUnlockAnimation(info.title, info.subtitle);
      } else {
        const match = actKey.match(/act_([ivx]+)/i);
        const part = match ? match[1].toUpperCase() : 'II';
        window.renderActUnlockAnimation(`Part ${part} Unlocked`, 'A new chapter begins');
      }
    }
  }
}

// ============================================================================
// Clue discovery
// ============================================================================

function processClueDiscovery(clueData) {
  recordClueScan(clueData.id);
  unlockStoryGate(clueData.story_gate_for);
}

// ============================================================================
// Access control
// ============================================================================

function determineAccessState(clueData, noAccessMessages) {
  if (window.resolveClueState) {
    return window.resolveClueState(clueData, {
      unlockedClues: [],
      unlockedActs: window.getFromLocalStorage(STORAGE_KEYS.UNLOCKED_ACTS, []),
      userSkills: window.getCharacterProfile()?.skills || [],
      noAccessMessages,
      hasSkillAccessFn: window.hasSkillAccess,
      parseSkillFn: window.parseSkill
    });
  }
  return { name: AccessState.UNLOCKED };
}

// ============================================================================
// Progress tracker
// ============================================================================

function renderProgressTracker(justProgressed = false) {
  const tracker = document.querySelector('[data-progress-tracker]');
  if (!tracker) return;

  const track = getCharacterTrack();
  const trackEl = tracker.querySelector('.progress-track');
  if (!trackEl) return;

  if (!track) {
    trackEl.style.display = 'none';
    return;
  }

  const scanned = window.getScannedClues();
  const chain = track.clueChain;
  const found = chain.filter(id => scanned.all?.includes(id)).length;

  trackEl.setAttribute('data-quest', track.trackId);
  trackEl.style.display = '';

  const pipsContainer = trackEl.querySelector('[data-pips]');
  const countEl = trackEl.querySelector('[data-count]');
  if (!pipsContainer || !countEl) return;

  pipsContainer.innerHTML = '';
  countEl.textContent = `${found} / ${chain.length}`;

  for (let i = 0; i < chain.length; i++) {
    const isFilled = scanned.all?.includes(chain[i]);
    const isJustFound = justProgressed && i === found - 1;
    window.renderProgressPip(pipsContainer, isFilled, isJustFound);
  }
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
      processClueDiscovery(clueData);
      const isOnTrack = isTrackClue(clueData.id);
      if (isOnTrack && window.spawnParticles) {
        renderProgressTracker(true);
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

  renderProgressTracker();
}

window.renderProgressTracker = renderProgressTracker;
document.addEventListener('DOMContentLoaded', initCluePage);
})();
