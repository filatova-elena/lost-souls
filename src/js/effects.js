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
 * Symbols for the octogram lock (8 alchemical symbols)
 */
const LOCK_SYMBOLS = ['🝪', '🝮', '☿', '🝣', '♀', '♃', '🝭', '🝰'];

/**
 * Generate SVG ring for octogram lock
 * @param {number} radius - Radius of the circle
 * @param {number} nodeRadius - Visual radius of each node
 * @param {number} numNodes - Number of nodes (8)
 * @returns {string} SVG string
 */
function generateRingSVG(radius, nodeRadius, numNodes) {
  const area = (radius + nodeRadius + 8) * 2;
  const cx = area / 2;
  const cy = area / 2;
  
  function nodeAngle(i) {
    return (i / numNodes) * Math.PI * 2 - Math.PI / 2;
  }
  
  function symPos(i) {
    const a = nodeAngle(i);
    return { x: cx + Math.cos(a) * radius, y: cy + Math.sin(a) * radius };
  }
  
  const halfGap = Math.asin(nodeRadius / radius);
  let svg = `<svg class="ring-svg" width="${area}" height="${area}" viewBox="0 0 ${area} ${area}" fill="none" xmlns="http://www.w3.org/2000/svg">`;
  
  // Draw arcs between nodes
  for (let i = 0; i < numNodes; i++) {
    const startAngle = nodeAngle(i) + halfGap;
    const endAngle = nodeAngle((i + 1) % numNodes) - halfGap;
    const x1 = cx + Math.cos(startAngle) * radius;
    const y1 = cy + Math.sin(startAngle) * radius;
    const x2 = cx + Math.cos(endAngle) * radius;
    const y2 = cy + Math.sin(endAngle) * radius;
    svg += `<path d="M ${x1} ${y1} A ${radius} ${radius} 0 0 1 ${x2} ${y2}" stroke="rgba(212,165,116,0.15)" stroke-width="1" stroke-linecap="round"/>`;
  }
  
  // Faint octagram
  const sq1 = [0, 2, 4, 6].map(i => symPos(i));
  const sq2 = [1, 3, 5, 7].map(i => symPos(i));
  svg += `<polygon points="${sq1.map(p => p.x + ',' + p.y).join(' ')}" stroke="rgba(212,165,116,0.05)" stroke-width="0.6" fill="none"/>`;
  svg += `<polygon points="${sq2.map(p => p.x + ',' + p.y).join(' ')}" stroke="rgba(212,165,116,0.05)" stroke-width="0.6" fill="none"/>`;
  svg += `</svg>`;
  
  return svg;
}

/**
 * Build interactive octogram lock
 * @param {HTMLElement} container - Container element
 * @param {string} unlockCode - 4-digit string like "0257"
 * @param {Function} onUnlock - Callback when unlocked
 */
function buildOctogramLock(container, unlockCode, onUnlock) {
  const radius = 90;
  const nodeRadius = 21;
  const area = (radius + nodeRadius + 8) * 2;
  const cx = area / 2;
  const cy = area / 2;
  const numNodes = 8;
  const required = 4;
  
  // Parse unlock code to set of indices
  const correctSet = new Set(Array.from(unlockCode).map(Number));
  
  container.innerHTML = '';
  container.style.width = area + 'px';
  container.style.height = area + 'px';
  container.style.position = 'relative';
  
  // Add ring SVG
  container.insertAdjacentHTML('beforeend', generateRingSVG(radius, nodeRadius, numNodes));
  
  // Add lock center
  const center = document.createElement('div');
  center.className = 'lock-center';
  center.innerHTML = `
    <div class="lock-glow"></div>
    <div class="lock-shackle"></div>
    <div class="lock-body"><div class="keyhole"></div></div>
  `;
  container.appendChild(center);
  
  // Add hint and result divs to parent (clue-no-access section)
  const parent = container.parentElement;
  const hintDiv = document.createElement('div');
  hintDiv.className = 'selection-hint';
  parent.appendChild(hintDiv);
  
  const resultDiv = document.createElement('div');
  resultDiv.className = 'lock-result idle';
  resultDiv.textContent = 'Select the 4 symbols shown by another investigator';
  parent.appendChild(resultDiv);
  
  // Add symbol nodes
  const selected = new Set();
  let unlocked = false;
  
  function nodeAngle(i) {
    return (i / numNodes) * Math.PI * 2 - Math.PI / 2;
  }
  
  function symPos(i) {
    const a = nodeAngle(i);
    return { x: cx + Math.cos(a) * radius, y: cy + Math.sin(a) * radius };
  }
  
  function updateHint() {
    hintDiv.innerHTML = `<strong>${selected.size}</strong> of ${required} selected`;
  }
  
  function checkSelection() {
    if (unlocked) return;
    
    const correct = selected.size === correctSet.size && 
                    Array.from(selected).every(i => correctSet.has(i));
    
    if (correct) {
      unlocked = true;
      resultDiv.className = 'lock-result success';
      resultDiv.textContent = '✓ The symbols align';
      setTimeout(() => {
        if (onUnlock) onUnlock();
      }, 700);
    } else {
      resultDiv.className = 'lock-result fail';
      resultDiv.textContent = '✗ The circle remains silent';
      setTimeout(() => {
        selected.clear();
        updateHint();
        container.querySelectorAll('.sym-node').forEach(node => {
          node.classList.remove('selected');
          node.style.borderColor = '';
          node.style.boxShadow = '';
        });
        resultDiv.className = 'lock-result idle';
        resultDiv.textContent = 'Select the 4 symbols shown by another investigator';
      }, 900);
    }
  }
  
  for (let i = 0; i < numNodes; i++) {
    const pos = symPos(i);
    const node = document.createElement('div');
    node.className = 'sym-node';
    node.textContent = LOCK_SYMBOLS[i];
    node.style.position = 'absolute';
    node.style.left = pos.x + 'px';
    node.style.top = pos.y + 'px';
    node.style.transform = 'translate(-50%, -50%)';
    node.dataset.idx = i;
    
    node.addEventListener('click', () => {
      if (unlocked) return;
      
      const idx = parseInt(node.dataset.idx);
      if (selected.has(idx)) {
        selected.delete(idx);
        node.classList.remove('selected');
      } else if (selected.size < required) {
        selected.add(idx);
        node.classList.add('selected');
        if (selected.size === required) {
          setTimeout(checkSelection, 350);
        }
      }
      updateHint();
    });
    
    container.appendChild(node);
  }
  
  updateHint();
}

/**
 * Build static ring (for unlocked clues to show which symbols to share)
 * @param {HTMLElement} container - Container element
 * @param {string} unlockCode - 4-digit string like "0257"
 */
function buildStaticRing(container, unlockCode) {
  const radius = 90;
  const nodeRadius = 21;
  const area = (radius + nodeRadius + 8) * 2;
  const cx = area / 2;
  const cy = area / 2;
  const numNodes = 8;
  
  const correctSet = new Set(Array.from(unlockCode).map(Number));
  
  container.innerHTML = '';
  container.style.width = area + 'px';
  container.style.height = area + 'px';
  container.style.position = 'relative';
  
  container.insertAdjacentHTML('beforeend', generateRingSVG(radius, nodeRadius, numNodes));
  
  function nodeAngle(i) {
    return (i / numNodes) * Math.PI * 2 - Math.PI / 2;
  }
  
  function symPos(i) {
    const a = nodeAngle(i);
    return { x: cx + Math.cos(a) * radius, y: cy + Math.sin(a) * radius };
  }
  
  for (let i = 0; i < numNodes; i++) {
    const pos = symPos(i);
    const node = document.createElement('div');
    node.className = 'sym-node' + (correctSet.has(i) ? ' in-path' : '');
    node.textContent = LOCK_SYMBOLS[i];
    node.style.position = 'absolute';
    node.style.left = pos.x + 'px';
    node.style.top = pos.y + 'px';
    node.style.transform = 'translate(-50%, -50%)';
    container.appendChild(node);
  }
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
 * Render unlock animation for next act
 * Creates a banner overlay with title and subtitle that appears at the top,
 * drifts down, and fades out, similar to the particle animation
 * @param {string} title - The main title text (e.g., "Part II Unlocked")
 * @param {string} subtitle - The subtitle text (e.g., "The investigation deepens")
 */
function renderActUnlockAnimation(title, subtitle) {
  // Get or create overlay container
  let container = document.getElementById('actUnlockContainer');
  if (!container) {
    container = document.createElement('div');
    container.id = 'actUnlockContainer';
    container.style.cssText = 'position:fixed;inset:0;pointer-events:none;z-index:1000;overflow:hidden;';
    document.body.appendChild(container);
  }
  
  // Create banner
  const banner = document.createElement('div');
  banner.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding-top: 12vh;
    pointer-events: none;
    z-index: 1001;
    opacity: 0;
  `;
  
  // Create title
  const titleEl = document.createElement('div');
  titleEl.textContent = title;
  titleEl.style.cssText = `
    font-size: clamp(2.2rem, 6vw, 4.5rem);
    font-weight: 700;
    letter-spacing: 0.25em;
    text-transform: uppercase;
    color: #d4a574;
    text-shadow: 0 0 30px rgba(212, 165, 116, 0.5), 0 0 60px rgba(212, 165, 116, 0.2);
    white-space: nowrap;
    font-family: 'Cinzel', serif;
  `;
  
  // Create decorative line
  const line = document.createElement('div');
  line.style.cssText = `
    width: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, #d4a574, transparent);
    margin-top: 14px;
    opacity: 0;
  `;
  
  // Create subtitle
  const subtitleEl = document.createElement('div');
  subtitleEl.textContent = subtitle;
  subtitleEl.style.cssText = `
    font-size: clamp(0.7rem, 1.8vw, 1rem);
    letter-spacing: 0.5em;
    color: rgba(212, 165, 116, 0.5);
    margin-top: 12px;
    opacity: 0;
    text-transform: uppercase;
    font-family: 'Cinzel', serif;
  `;
  
  banner.appendChild(titleEl);
  banner.appendChild(line);
  banner.appendChild(subtitleEl);
  container.appendChild(banner);
  
  // Animate banner: appear at top, drift down, fade out
  banner.animate([
    { opacity: 0, transform: 'translateY(-20px)' },
    { opacity: 1, transform: 'translateY(0)', offset: 0.08 },
    { opacity: 1, transform: 'translateY(30px)', offset: 0.55 },
    { opacity: 0, transform: 'translateY(80px)' }
  ], {
    duration: 4000,
    easing: 'ease-out',
    fill: 'forwards'
  });
  
  // Animate line expansion
  line.animate([
    { width: '0px', opacity: 0 },
    { width: 'min(320px, 50vw)', opacity: 1 }
  ], {
    duration: 600,
    delay: 300,
    easing: 'ease-out',
    fill: 'forwards'
  });
  
  // Animate subtitle fade in
  subtitleEl.animate([
    { opacity: 0 },
    { opacity: 1 }
  ], {
    duration: 500,
    delay: 500,
    easing: 'ease-out',
    fill: 'forwards'
  });
  
  // Spawn particles
  const particleCount = 12;
  for (let i = 0; i < particleCount; i++) {
    const particle = document.createElement('div');
    const x = 30 + Math.random() * 40; // cluster around center
    const startY = 10 + Math.random() * 8;
    const delay = 200 + Math.random() * 800;
    const drift = -15 + Math.random() * 30;
    
    particle.style.cssText = `
      position: fixed;
      width: 2px;
      height: 2px;
      background: #d4a574;
      border-radius: 50%;
      pointer-events: none;
      opacity: 0;
      z-index: 1000;
      left: ${x}%;
      top: ${startY}vh;
    `;
    
    container.appendChild(particle);
    
    particle.animate([
      { opacity: 0, transform: 'translate(0, 0) scale(1)' },
      { opacity: 0.6, transform: `translate(${drift * 0.3}px, 20px) scale(1)`, offset: 0.15 },
      { opacity: 0.4, transform: `translate(${drift * 0.7}px, 60px) scale(0.8)`, offset: 0.6 },
      { opacity: 0, transform: `translate(${drift}px, 120px) scale(0.3)` }
    ], {
      duration: 3000,
      delay: delay,
      easing: 'ease-out',
      fill: 'forwards'
    });
    
    setTimeout(() => particle.remove(), 4000);
  }
  
  // Clean up after animation
  setTimeout(() => {
    banner.remove();
    // Only remove container if it's empty
    if (container.children.length === 0) {
      container.remove();
    }
  }, 4200);
}

/**
 * Render typewriter confirmation animation
 * Creates an overlay with typewriter effect showing name, typewriter text, and status
 * @param {string} name - The name to display (e.g., "Margaret Ashworth")
 * @param {string} typewriterText - The text to type out character by character (e.g., "You are now investigating as")
 * @param {string} statusText - The status/ready text to display (e.g., "Ready to scan clues")
 */
function renderTypewriterAnimation(name, typewriterText, statusText) {
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
    }, 5000);
  }
  
  // Close overlay
  function closeOverlay() {
    overlay.style.transition = 'opacity 0.6s ease';
    overlay.style.opacity = '0';
    
    setTimeout(() => {
      if (overlay && overlay.parentElement) {
        overlay.remove();
      }
    }, 600);
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
    
    // Show static ring if unlock_code exists
    const clueData = window.__clueData || {};
    if (clueData.unlock_code && window.buildStaticRing) {
      const staticRing = cluePage.querySelector('.static-ring[data-unlock-code]');
      if (staticRing) {
        const seanceSection = staticRing.closest('.seance-section');
        if (seanceSection) {
          seanceSection.style.display = '';
          window.buildStaticRing(staticRing, clueData.unlock_code);
        }
      }
    }
    
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
window.triggerUnlockAnimation = triggerUnlockAnimation;
window.spawnParticles = spawnParticles;
window.renderActUnlockAnimation = renderActUnlockAnimation;
window.renderTypewriterAnimation = renderTypewriterAnimation;
window.buildOctogramLock = buildOctogramLock;
window.buildStaticRing = buildStaticRing;

})();
