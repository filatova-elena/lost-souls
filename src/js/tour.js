/**
 * First-time tour
 * Points at the scan button, the status bar and the history button, one after
 * another. It starts when the "Begin investigation" animation closes, and only
 * once per device. Skip, Esc and the last button all end it the same way.
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

  const count = tour.querySelector('.tour-count');
  const text = tour.querySelector('.tour-text');
  const next = tour.querySelector('.tour-next');
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
    count.textContent = `${index + 1} / ${steps.length}`;
    text.textContent = step.text;
    next.textContent = isLast ? 'Got it' : 'Next';
  }

  function finish() {
    window.removeEventListener('resize', show);
    document.removeEventListener('keydown', onKeydown);
    tour.remove();
    window.saveToLocalStorage(SEEN_KEY, true);
  }

  function onKeydown(event) {
    if (event.key === 'Escape') finish();
  }

  next.addEventListener('click', () => {
    if (index === steps.length - 1) {
      finish();
    } else {
      index += 1;
      show();
    }
  });
  tour.querySelector('.tour-skip').addEventListener('click', finish);
  window.addEventListener('resize', show);
  document.addEventListener('keydown', onKeydown);

  show();
}

window.startTour = startTour;

})();
