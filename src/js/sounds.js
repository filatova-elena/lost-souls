/**
 * Sound effects
 * Preloads the short UI cues and plays them by name.
 *
 * Mobile browsers block audio until the user has interacted with the page, and
 * that permission does not survive a page navigation. A clue page opened by
 * scanning a QR code is a fresh document with no gesture behind it, so the
 * first play() there can be rejected. When that happens we hold the cue and
 * fire it on the first tap instead of dropping it silently.
 */
(function() {
'use strict';

var SOUNDS = {
  clue_found: 'assets/audio/clue_found.mp3',
  key_clue_found: 'assets/audio/key_clue_found.mp3'
};

var MUTE_KEY = 'sound_muted';

// Derive the site root from this script's own URL so the deploy path prefix works
var baseUrl = '/';
var self = document.currentScript;
if (self && self.src) {
  baseUrl = self.src.replace(/js\/sounds\.js.*$/, '');
}

var players = {};
var pending = null;
var listening = false;

function isMuted() {
  try {
    return localStorage.getItem(MUTE_KEY) === 'true';
  } catch (e) {
    return false;
  }
}

function setMuted(muted) {
  try {
    localStorage.setItem(MUTE_KEY, muted ? 'true' : 'false');
  } catch (e) {}
  return muted;
}

function toggleSound() {
  return !setMuted(!isMuted());
}

function preload() {
  Object.keys(SOUNDS).forEach(function(name) {
    var audio = new Audio(baseUrl + SOUNDS[name]);
    audio.preload = 'auto';
    audio.volume = 1;
    players[name] = audio;
  });
}

// Replay the cue that a browser refused, as soon as the player touches anything
function listenForGesture() {
  if (listening) return;
  listening = true;

  var events = ['pointerdown', 'touchend', 'keydown'];
  var fire = function() {
    events.forEach(function(type) {
      document.removeEventListener(type, fire, true);
    });
    listening = false;
    var name = pending;
    pending = null;
    if (name) playSound(name);
  };

  events.forEach(function(type) {
    document.addEventListener(type, fire, true);
  });
}

function playSound(name) {
  if (isMuted()) return;

  var audio = players[name];
  if (!audio) return;

  try {
    audio.currentTime = 0;
  } catch (e) {}

  var attempt = audio.play();
  if (attempt && typeof attempt.catch === 'function') {
    attempt.catch(function() {
      pending = name;
      listenForGesture();
    });
  }
}

/**
 * Called from a real tap (the scan button) to satisfy mobile autoplay policy,
 * so a cue triggered later in the same document plays without being blocked.
 */
function unlockSound() {
  Object.keys(players).forEach(function(name) {
    var audio = players[name];
    var previous = audio.volume;
    audio.volume = 0;
    var attempt = audio.play();
    var restore = function() {
      audio.pause();
      try {
        audio.currentTime = 0;
      } catch (e) {}
      audio.volume = previous;
    };
    if (attempt && typeof attempt.then === 'function') {
      attempt.then(restore).catch(restore);
    } else {
      restore();
    }
  });
}

preload();

window.playSound = playSound;
window.unlockSound = unlockSound;
window.toggleSound = toggleSound;
window.isSoundMuted = isMuted;

})();
