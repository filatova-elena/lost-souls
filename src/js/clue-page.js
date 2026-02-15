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

document.addEventListener('DOMContentLoaded', initCluePage);
})();
