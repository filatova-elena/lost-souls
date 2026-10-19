/**
 * First-time tour
 * Points at the scan button, the status bar and the history button, one after
 * another. It starts when the "Begin investigation" animation closes, and only
 * once per device. Skip, Esc and the last button all end it the same way.
 *
 * The tour is a nicety, so nothing in it may get in the game's way: whatever
 * goes wrong, it ends quietly and takes its overlay with it.
 */
(function() {
'use strict';

const SEEN_KEY = 'tour_seen';

const STEPS = [
  { selector: '#qr-scan-btn', text: 'Tap here to scan a QR code and open a clue.' },
  { selector: '.progress-tracker', text: 'Your character and how far along you are.' },
  { selector: '.progress-history', text: 'Every clue you’ve found, newest first.' }
];

const PADDING = 6;
const MARGIN = 12;

function startTour() {
  if (window.getFromLocalStorage(SEEN_KEY, false)) return;

  // A step whose target is not on the page is left out
  const steps = STEPS
    .map(step => ({ text: step.text, target: document.querySelector(step.selector) }))
    .filter(step => step.target);
  if (steps.length === 0) return;

  const tour = document.createElement('div');
  tour.className = 'tour';
  tour.innerHTML = `
    <div class="tour-spotlight"></div>
    <div class="tour-card">
      <p class="eyebrow tour-count"></p>
      <p class="tour-text"></p>
      <div class="tour-actions">
        <button type="button" class="button-ghost tour-skip">Skip</button>
        <button type="button" class="button tour-next"></button>
      </div>
    </div>
  `;
  document.body.appendChild(tour);

  let index = 0;

  // The targets are fixed to the screen, so the card always sits just above its target
  function show() {
    const step = steps[index];
    const rect = step.target.getBoundingClientRect();
    const cardWidth = Math.min(300, window.innerWidth - 2 * MARGIN);
    const cardLeft = Math.min(
      Math.max(rect.left + rect.width / 2 - cardWidth / 2, MARGIN),
      window.innerWidth - cardWidth - MARGIN
    );

    const set = (name, value) => tour.style.setProperty(name, value);
    set('--tour-x', `${rect.left - PADDING}px`);
    set('--tour-y', `${rect.top - PADDING}px`);
    set('--tour-w', `${rect.width + 2 * PADDING}px`);
    set('--tour-h', `${rect.height + 2 * PADDING}px`);
    set('--tour-radius', window.getComputedStyle(step.target).borderRadius);
    set('--tour-card-left', `${cardLeft}px`);
    set('--tour-card-width', `${cardWidth}px`);
    set('--tour-card-bottom', `${window.innerHeight - rect.top + PADDING + MARGIN}px`);

    const isLast = index === steps.length - 1;
    tour.dataset.last = String(isLast);
    tour.querySelector('.tour-count').textContent = `${index + 1} / ${steps.length}`;
    tour.querySelector('.tour-text').textContent = step.text;
    tour.querySelector('.tour-next').textContent = isLast ? 'Got it' : 'Next';
  }

  // Removes the tour and everything it listens to
  function end() {
    window.removeEventListener('resize', showOrEnd);
    document.removeEventListener('keydown', onKeydown);
    tour.remove();
  }

  // The tour was seen: it will not come back
  function finish() {
    end();
    window.saveToLocalStorage(SEEN_KEY, true);
  }

  // A step that cannot be drawn ends the tour; it does not stay stuck on the screen
  function showOrEnd() {
    try {
      show();
    } catch (error) {
      console.error('The tour stopped:', error);
      end();
    }
  }

  function onKeydown(event) {
    if (event.key === 'Escape') finish();
  }

  try {
    tour.querySelector('.tour-next').addEventListener('click', () => {
      if (index === steps.length - 1) {
        finish();
      } else {
        index += 1;
        showOrEnd();
      }
    });
    tour.querySelector('.tour-skip').addEventListener('click', finish);
    window.addEventListener('resize', showOrEnd);
    document.addEventListener('keydown', onKeydown);
    show();
  } catch (error) {
    console.error('The tour could not start:', error);
    end();
  }
}

// Called from the game, so a failure here must never reach it
window.startTour = function() {
  try {
    startTour();
  } catch (error) {
    console.error('The tour could not start:', error);
  }
};

})();
