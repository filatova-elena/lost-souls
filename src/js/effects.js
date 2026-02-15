(function() {
'use strict';

/**
 * SVG for progress pip (diamond with keyhole)
 */
function pipSVG() {
  return `<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
    <rect class="diamond-bg" x="4" y="4" width="16" height="16" rx="1.8" transform="rotate(45 12 12)"/>
    <circle class="keyhole-circle" cx="12" cy="10.5" r="2.8"/>
    <rect class="keyhole-rect" x="10.6" y="11.5" width="2.8" height="4.8" rx="0.8"/>
  </svg>`;
}

/**
 * Render a single progress pip
 * @param {HTMLElement} container - Container element to append pip to
 * @param {boolean} isFilled - Whether the pip should be filled
 * @param {boolean} isJustFound - Whether this pip was just found (for animation)
 */
function renderProgressPip(container, isFilled, isJustFound = false) {
  const pip = document.createElement('div');
  pip.className = `pip ${isFilled ? 'filled' : 'empty'}${isJustFound ? ' just-found' : ''}`;
  pip.innerHTML = pipSVG();
  container.appendChild(pip);
}

/**
 * Render progress tracker with pips for main and side quests
 * Reads progress data from data attributes on the tracker element
 * Filters side quest by current character from localStorage
 * @param {string} newlyFoundQuestHashtag - Optional quest hashtag for the clue that was just found (for animation)
 */
function renderProgressTracker(newlyFoundQuestHashtag = null) {
  const tracker = document.querySelector('[data-progress-tracker]');
  if (!tracker) return;
  
  // Get progress data from window global (pre-computed at build time)
  const progressData = window.__progressData;
  if (!progressData) {
    console.error('Progress data not found');
    return;
  }
  
  const mainQuestHashtag = progressData.mainQuestHashtag || 'main_quest';
  const mainQuestTotal = progressData.mainQuestTotal || 0;
  
  // Use side quests object directly (pre-computed at build time)
  const characterSideQuests = progressData.sideQuests || {};
  
  // Get current character from localStorage (only client-side dependency)
  const characterProfile = window.getCharacterProfile ? window.getCharacterProfile() : null;
  const currentCharacterId = characterProfile?.characterId || null;
  
  // Get scanned clues from localStorage (only client-side dependency)
  const scanned = window.getScannedClues ? window.getScannedClues() : { all: [] };
  
  // Render main quest progress (always show)
  const mainTrack = tracker.querySelector('.progress-track.main');
  if (mainTrack) {
    const found = scanned[mainQuestHashtag]?.length || 0;
    // If this quest just had a clue found, animate the last pip
    const newlyFoundIndex = (newlyFoundQuestHashtag === mainQuestHashtag) ? found - 1 : -1;
    renderQuestProgress(mainTrack, found, mainQuestTotal, newlyFoundIndex);
  }
  
  // Render side quest progress for current character
  const sideTrack = tracker.querySelector('.progress-track.side');
  if (sideTrack && currentCharacterId && characterSideQuests[currentCharacterId]) {
    const sideQuestData = characterSideQuests[currentCharacterId];
    const found = scanned[sideQuestData.hashtag]?.length || 0;
    
    // Update side track label with objective_short
    const sideLabel = sideTrack.querySelector('.progress-label');
    if (sideLabel && sideQuestData.objectiveShort) {
      sideLabel.textContent = sideQuestData.objectiveShort;
    }
    
    // Update side track attributes and show it
    sideTrack.setAttribute('data-quest', sideQuestData.hashtag);
    sideTrack.style.display = '';
    // If this quest just had a clue found, animate the last pip
    const newlyFoundIndex = (newlyFoundQuestHashtag === sideQuestData.hashtag) ? found - 1 : -1;
    renderQuestProgress(sideTrack, found, sideQuestData.total, newlyFoundIndex);
  } else if (sideTrack) {
    // Hide side quest if no character selected or no side quest for character
    sideTrack.style.display = 'none';
  }
}

/**
 * Render progress pips for a single quest track
 * @param {HTMLElement} trackElement - The progress track element
 * @param {number} found - Number of found key clues
 * @param {number} total - Total number of key clues
 * @param {number} newlyFoundIndex - Index of the pip that was just found (for animation), or -1 if none
 */
function renderQuestProgress(trackElement, found, total, newlyFoundIndex = -1) {
  const pipsContainer = trackElement.querySelector('[data-pips]');
  const countElement = trackElement.querySelector('[data-count]');
  
  if (!pipsContainer || !countElement) return;
  
  // Clear existing pips
  pipsContainer.innerHTML = '';
  
  // Update count
  countElement.textContent = `${found} / ${total}`;
  
  // Render pips
  for (let i = 0; i < total; i++) {
    const isFilled = i < found;
    const isJustFound = i === newlyFoundIndex;
    renderProgressPip(pipsContainer, isFilled, isJustFound);
  }
}

/**
 * Join array with Oxford comma "or"
 */
function joinWithOr(items) {
  if (items.length === 0) return '';
  if (items.length === 1) return items[0];
  if (items.length === 2) return `${items[0]} or ${items[1]}`;
  const last = items[items.length - 1];
  const rest = items.slice(0, -1);
  return `${rest.join(', ')}, or ${last}`;
}

/**
 * Generate lock HTML structure
 * @param {string} message - The lock message
 * @param {Array<string>} suggestedCharacters - Optional array of suggested character names
 * @returns {string} HTML string for the lock
 */
function generateLockHTML(message, suggestedCharacters = null) {
  let lockHTML = `
    <div class="lock-assembly">
      <div class="lock-glow"></div>
      <div class="lock-shackle"></div>
      <div class="lock-body"><div class="keyhole"></div></div>
    </div>
  `;
  
  if (message) {
    lockHTML += `<p>${message}</p>`;
  }
  
  if (suggestedCharacters && suggestedCharacters.length > 0) {
    // Wrap each character name in <strong> tags
    const boldCharacters = suggestedCharacters.map(name => `<strong>${name}</strong>`);
    const characterList = joinWithOr(boldCharacters);
    lockHTML += `<span class="locked-seek">Seek out ${characterList}</span>`;
  }
  
  return lockHTML;
}

/**
 * Spawn celebration particles when a key clue is found
 * Creates golden particles that fall from the top of the screen
 */
function spawnParticles() {
  // Get or create celebration container
  let container = document.getElementById('celebrationContainer');
  if (!container) {
    container = document.createElement('div');
    container.id = 'celebrationContainer';
    container.style.cssText = 'position:fixed;inset:0;pointer-events:none;z-index:1000;overflow:hidden;';
    document.body.appendChild(container);
  }
  
  const colors = ['#d4a574', '#e8be8a', '#f0d080', '#c9a060', '#ffe4c4'];
  for (let i = 0; i < 30; i++) {
    const el = document.createElement('div');
    const sz = 3 + Math.random() * 5;
    const x = 15 + Math.random() * 70;
    const drift = -40 + Math.random() * 80;
    const dur = 1400 + Math.random() * 1200;
    const delay = Math.random() * 500;
    el.style.cssText = `position:absolute;left:${x}%;top:-5px;width:${sz}px;height:${sz}px;background:${colors[Math.floor(Math.random() * colors.length)]};border-radius:${Math.random() > 0.4 ? '50%' : '1px'};pointer-events:none;`;
    el.animate([
      { transform: 'translateX(0) translateY(0) rotate(0deg)', opacity: 1 },
      { transform: `translateX(${drift}px) translateY(${250 + Math.random() * 200}px) rotate(${300 + Math.random() * 400}deg)`, opacity: 0 }
    ], { duration: dur, delay: delay, easing: 'cubic-bezier(0.25,0.46,0.45,0.94)', fill: 'forwards' });
    container.appendChild(el);
    setTimeout(() => el.remove(), dur + delay + 100);
  }
}

/**
 * Trigger unlock animation on a clue page
 * @param {HTMLElement} cluePage - The clue page element (main container)
 * @param {HTMLElement} lockSection - The .clue-no-access section
 * @param {boolean} isKeyClue - Whether this is a key clue (for special effects)
 */
function triggerUnlockAnimation(cluePage, lockSection, isKeyClue = false) {
  if (!cluePage || !lockSection) return;
  
  // Add unlocking class to trigger CSS animations
  cluePage.classList.add('unlocking');
  
  // After animation completes, hide lock and show content
  setTimeout(() => {
    lockSection.style.display = 'none';
    cluePage.classList.remove('unlocking');
    
    // Show content sections (make them visible so CSS animations can run)
    const narrationSections = cluePage.querySelectorAll('.clue-narration');
    const contentSections = cluePage.querySelectorAll('.clue-content');
    narrationSections.forEach(section => section.style.display = '');
    contentSections.forEach(section => section.style.display = '');
    
    // Add just-unlocked class to trigger CSS reveal animation
    // Use requestAnimationFrame to ensure display change is applied first
    requestAnimationFrame(() => {
      cluePage.classList.add('just-unlocked');
    });
    
    // If key clue, add special styling, flash effect, and particles
    if (isKeyClue) {
      cluePage.classList.add('is-key-clue');
      // Show key clue badge if it exists
      const badge = cluePage.querySelector('.key-clue-badge');
      if (badge) {
        badge.classList.add('visible');
      }
      // Add flash effect
      const flash = document.createElement('div');
      flash.className = 'key-flash';
      document.body.appendChild(flash);
      setTimeout(() => flash.remove(), 1200);
      // Spawn celebration particles
      spawnParticles();
    }
  }, 1500); // Total animation duration (matches CSS timing)
}

// Expose to global scope
window.pipSVG = pipSVG;
window.renderProgressPip = renderProgressPip;
window.renderProgressTracker = renderProgressTracker;
window.generateLockHTML = generateLockHTML;
window.triggerUnlockAnimation = triggerUnlockAnimation;
window.spawnParticles = spawnParticles;

})();
