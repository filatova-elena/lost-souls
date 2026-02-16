/**
 * Clue page initialization
 * Handles clue access control and progress tracking
 */
(function() {
'use strict';

function initCluePage() {
  const clueData = window.__clueData;
  const noAccessMessages = window.__noAccessMessages;
  const progressData = window.__progressData;
  
  if (!clueData) return;
  
  logDebugInfo(clueData, progressData);
  initClueAccess(clueData, noAccessMessages);
  renderProgressTracker();
}

function logDebugInfo(clueData, progressData) {
  const characterProfile = getCharacterProfile();
  const scanned = getScannedClues();
  const currentCharacterId = characterProfile?.characterId;
  const characterSideQuests = progressData?.sideQuests || {};
  const sideQuestInfo = currentCharacterId ? characterSideQuests[currentCharacterId] : null;
  const mainQuestFound = scanned[progressData?.mainQuestHashtag || 'main_quest']?.length || 0;
  const sideQuestHashtag = sideQuestInfo?.hashtag;

  console.log('=== Clue Page Debug ===');
  console.log('Current character:', currentCharacterId || 'None');
  console.log('Private objective:', sideQuestInfo?.objectiveShort || 'None');
  console.log('Progress towards main objective:', `${mainQuestFound}/${progressData?.mainQuestTotal || 0}`);
  console.log('Progress towards private objective:', sideQuestHashtag ? `${scanned[sideQuestHashtag]?.length || 0}/${sideQuestInfo?.total || 0}` : 'N/A');
  console.log('Character skills:', characterProfile?.skills || []);
  console.log('Clue required skills:', clueData.skills || []);
  console.log('======================');
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
  
  // Render pips (using utility from effects.js)
  for (let i = 0; i < total; i++) {
    const isFilled = i < found;
    const isJustFound = i === newlyFoundIndex;
    window.renderProgressPip(pipsContainer, isFilled, isJustFound);
  }
}

/**
 * Initialize clue access control on page load
 * @param {Object} clueData - Clue data object with skills, type, accessChars (pre-computed), etc.
 * @param {Object} noAccessMessages - The no_access_messages data structure
 */
function initClueAccess(clueData, noAccessMessages) {
  const access = checkAccess(clueData, noAccessMessages);
  
  // Check if this clue was already scanned
  const scanned = getScannedClues();
  const wasAlreadyScanned = scanned.all && scanned.all.includes(clueData.id);
  
  // If user has access, show content immediately - NO lock animation ever
  if (access.hasAccess) {
    renderClueAccess(access, false);
    
    // Mark as scanned if not already scanned
    if (!wasAlreadyScanned) {
      markClueAsScanned(clueData.id, clueData);
      
      // Check if this is a key clue relevant to current character
      const isKey = clueData.is_key || [];
      const keyHashtags = Array.isArray(isKey) ? isKey : (isKey ? [isKey] : []);
      
      // Get current character's quests
      const characterProfile = getCharacterProfile();
      const currentCharacterId = characterProfile?.characterId;
      const progressData = window.__progressData || {};
      const characterSideQuests = progressData.sideQuests || {};
      const sideQuestInfo = currentCharacterId ? characterSideQuests[currentCharacterId] : null;
      const mainQuestHashtag = progressData.mainQuestHashtag || 'main_quest';
      const sideQuestHashtag = sideQuestInfo?.hashtag;
      
      // Find which quest this clue is key for (if any) - only main quest or current character's side quest
      let newlyFoundQuestHashtag = null;
      if (keyHashtags.includes(mainQuestHashtag)) {
        newlyFoundQuestHashtag = mainQuestHashtag;
      } else if (sideQuestHashtag && keyHashtags.includes(sideQuestHashtag)) {
        newlyFoundQuestHashtag = sideQuestHashtag;
      }
      
      // If relevant key clue, update tracker with animation and spawn particles
      if (newlyFoundQuestHashtag && window.renderProgressTracker && window.spawnParticles) {
        window.renderProgressTracker(newlyFoundQuestHashtag);
        window.spawnParticles();
      } else if (window.renderProgressTracker) {
        // Still update tracker even if not a key clue
        window.renderProgressTracker();
      }
    }
    
    return access;
  }
  
  // User doesn't have access - show lock (no animation, just locked state)
  renderClueAccess(access, false);
  
  return access;
}

// Expose for use by unlock callbacks
window.renderProgressTracker = renderProgressTracker;

document.addEventListener('DOMContentLoaded', initCluePage);
})();
