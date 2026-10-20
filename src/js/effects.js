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
 * Render typewriter confirmation animation
 * Creates an overlay with typewriter effect showing name, typewriter text, and status
 * @param {string} name - The name to display (e.g., "Margaret Ashworth")
 * @param {string} typewriterText - The text to type out character by character (e.g., "You are now investigating as")
 * @param {string} statusText - The status/ready text to display (e.g., "Ready to scan clues")
 */
function renderTypewriterAnimation(name, typewriterText, statusText, onClosed) {
  // Get or create overlay container
  let overlay = document.getElementById('typewriterOverlay');
  if (overlay) {
    // If overlay exists, remove it first to reset
    overlay.remove();
  }
  
  overlay = document.createElement('div');
  overlay.id = 'typewriterOverlay';
  overlay.style.cssText = `
    position: fixed;
    inset: 0;
    z-index: 1000;
    pointer-events: none;
    opacity: 0;
    transition: opacity 0.3s ease;
  `;
  
  // Create backdrop
  const backdrop = document.createElement('div');
  backdrop.style.cssText = `
    position: absolute;
    inset: 0;
    background: rgba(5, 5, 10, 0);
    transition: background 0.5s ease;
  `;
  
  // Create content container
  const content = document.createElement('div');
  content.style.cssText = `
    position: absolute;
    inset: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 6px;
  `;
  
  // Create typewriter line
  const typeLine = document.createElement('div');
  typeLine.style.cssText = `
    font-family: 'Special Elite', monospace;
    font-size: clamp(0.8rem, 2vw, 1.1rem);
    letter-spacing: 0.2em;
    color: rgba(212, 165, 116, 0.6);
    white-space: nowrap;
    min-height: 1.4em;
  `;
  
  // Create name element
  const nameEl = document.createElement('div');
  nameEl.textContent = name;
  nameEl.style.cssText = `
    font-family: 'Cinzel', serif;
    font-size: clamp(1.6rem, 4.5vw, 3rem);
    font-weight: 700;
    letter-spacing: 0.18em;
    color: #d4a574;
    text-shadow: 0 0 50px rgba(212, 165, 116, 0.25);
    opacity: 0;
    transform: translateY(6px);
    transition: opacity 0.6s ease, transform 0.6s ease;
  `;
  
  // Create carriage return line
  const carriage = document.createElement('div');
  carriage.style.cssText = `
    height: 1px;
    background: rgba(212, 165, 116, 0.4);
    margin: 14px 0;
    width: 0;
    transition: width 0.15s linear;
  `;
  
  // Create status text
  const statusEl = document.createElement('div');
  statusEl.textContent = statusText;
  statusEl.style.cssText = `
    font-family: 'Special Elite', monospace;
    font-size: clamp(0.65rem, 1.4vw, 0.85rem);
    letter-spacing: 0.3em;
    text-transform: uppercase;
    color: rgba(212, 165, 116, 0.35);
    opacity: 0;
    transition: opacity 0.5s ease;
  `;
  
  // Create dismiss hint
  const dismissHint = document.createElement('div');
  dismissHint.textContent = 'tap anywhere to continue';
  dismissHint.style.cssText = `
    position: absolute;
    bottom: 12vh;
    left: 50%;
    transform: translateX(-50%);
    font-size: 0.6rem;
    letter-spacing: 0.4em;
    text-transform: uppercase;
    color: rgba(212, 165, 116, 0.2);
    opacity: 0;
    transition: opacity 0.5s ease;
  `;
  
  content.appendChild(typeLine);
  content.appendChild(nameEl);
  content.appendChild(carriage);
  content.appendChild(statusEl);
  overlay.appendChild(backdrop);
  overlay.appendChild(content);
  overlay.appendChild(dismissHint);
  document.body.appendChild(overlay);
  
  // Activate overlay
  requestAnimationFrame(() => {
    overlay.style.pointerEvents = 'auto';
    overlay.style.opacity = '1';
    backdrop.style.background = 'rgba(5, 5, 10, 0.85)';
    
    // Start typing after backdrop fades in
    setTimeout(() => {
      // Add typing cursor
      typeLine.style.borderRight = '2px solid rgba(212, 165, 116, 0.5)';
      typeLine.style.animation = 'cursorBlink 0.6s step-end infinite';
      
      // Add cursor blink keyframes if not already present
      if (!document.getElementById('cursorBlinkKeyframes')) {
        const style = document.createElement('style');
        style.id = 'cursorBlinkKeyframes';
        style.textContent = `
          @keyframes cursorBlink {
            50% { border-right-color: transparent; }
          }
        `;
        document.head.appendChild(style);
      }
      
      // Type the text
      typeText(typewriterText, typeLine, 45, () => {
        // Typing done — remove cursor
        typeLine.style.borderRight = 'none';
        typeLine.style.animation = '';
        
        // Reveal name
        setTimeout(() => {
          nameEl.style.opacity = '1';
          nameEl.style.transform = 'translateY(0)';
          
          // Carriage line
          setTimeout(() => {
            carriage.style.width = 'min(280px, 45vw)';
            
            // Status text
            setTimeout(() => {
              statusEl.style.opacity = '1';
              
              // Dismiss hint
              setTimeout(() => {
                dismissHint.style.opacity = '1';
                enableDismiss();
              }, 400);
            }, 200);
          }, 500);
        }, 300);
      });
    }, 500);
  });
  
  // Typewriter effect function
  function typeText(text, element, speed, callback) {
    let i = 0;
    element.textContent = '';
    const interval = setInterval(() => {
      element.textContent += text[i];
      i++;
      if (i >= text.length) {
        clearInterval(interval);
        if (callback) callback();
      }
    }, speed);
  }
  
  // Enable dismiss functionality
  function enableDismiss() {
    let dismissTimeout;
    
    const dismiss = () => {
      overlay.removeEventListener('click', dismiss);
      clearTimeout(dismissTimeout);
      closeOverlay();
    };
    
    overlay.addEventListener('click', dismiss);
    
    // Auto-dismiss after 5 seconds
    dismissTimeout = setTimeout(() => {
      if (overlay && overlay.parentElement) {
        overlay.removeEventListener('click', dismiss);
        closeOverlay();
      }
    }, 1500);
  }
  
  // Close overlay
  function closeOverlay() {
    overlay.style.transition = 'opacity 0.5s ease'; // Change 0.6s to adjust fade speed
    overlay.style.opacity = '0';
    
    setTimeout(() => {
      if (overlay && overlay.parentElement) {
        overlay.remove();
        if (onClosed) onClosed();
      }
    }, 200);
  }
}

// Expose to global scope
window.pipSVG = pipSVG;
window.renderProgressPip = renderProgressPip;
window.spawnParticles = spawnParticles;
window.renderTypewriterAnimation = renderTypewriterAnimation;

})();
