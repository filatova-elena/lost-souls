/**
 * Technical Check System
 * Performs checks for JavaScript, localStorage, and browser features
 * Used by the test clue (TEST001) to verify device compatibility
 */
(function() {
'use strict';

// Contact email for support - update this with your actual support email
const SUPPORT_EMAIL = 'inquiries@door66.events';

function getTroubleshootingSteps(failedChecks) {
  const steps = [];
  
  failedChecks.forEach(check => {
    if (check.name === 'Local Storage') {
      steps.push({
        title: 'Local Storage Issue',
        steps: [
          'If you\'re using Private/Incognito mode, try switching to a regular browsing session.',
          'Check your browser settings to ensure cookies and site data are allowed.',
          'Try clearing your browser cache and reloading the page.',
          'If using Safari, check Settings > Safari > Block All Cookies and ensure it\'s disabled.'
        ]
      });
    } else if (check.name === 'Modern Browser Features') {
      steps.push({
        title: 'Browser Compatibility Issue',
        steps: [
          'Update your browser to the latest version.',
          'If you\'re using an older device, try a different browser (Chrome, Firefox, Safari, or Edge).',
          'Check if your browser has any extensions that might be blocking features.',
          'Try disabling browser extensions temporarily to see if that resolves the issue.'
        ]
      });
    }
  });
  
  return steps;
}

function runTechnicalChecks() {
  const resultsContainer = document.getElementById('check-results');
  const statusContainer = document.getElementById('check-status');
  const checkSection = document.getElementById('technical-check-results');
  if (!resultsContainer || !statusContainer || !checkSection) return;
  
  const checks = [];
  let allPassed = true;
  const failedChecks = [];
  
  // Check 1: JavaScript (this check itself proves JS is enabled)
  checks.push({
    name: 'JavaScript Enabled',
    passed: true,
    message: 'JavaScript is working correctly.'
  });
  
  // Check 2: LocalStorage availability
  let localStorageAvailable = false;
  let localStorageMessage = '';
  try {
    const testKey = '__test_storage__';
    localStorage.setItem(testKey, 'test');
    localStorageAvailable = localStorage.getItem(testKey) === 'test';
    localStorage.removeItem(testKey);
    if (localStorageAvailable) {
      localStorageMessage = 'Local storage is available. Your progress will be saved.';
    } else {
      localStorageMessage = 'Local storage test failed.';
    }
  } catch (e) {
    localStorageMessage = 'Local storage is blocked or unavailable. This may happen in Private/Incognito mode. Your progress will not be saved.';
  }
  const localStorageCheck = {
    name: 'Local Storage',
    passed: localStorageAvailable,
    message: localStorageMessage
  };
  checks.push(localStorageCheck);
  if (!localStorageAvailable) {
    allPassed = false;
    failedChecks.push(localStorageCheck);
  }
  
  // Check 3: Modern browser features
  const modernFeatures = {
    'querySelector': typeof document.querySelector === 'function',
    'addEventListener': typeof document.addEventListener === 'function',
    'JSON': typeof JSON !== 'undefined' && typeof JSON.parse === 'function',
    'Array methods': typeof Array.prototype.find === 'function'
  };
  const missingFeatures = Object.entries(modernFeatures)
    .filter(([_, available]) => !available)
    .map(([name]) => name);
  
  const browserFeaturesCheck = {
    name: 'Modern Browser Features',
    passed: missingFeatures.length === 0,
    message: missingFeatures.length === 0 
      ? 'All required browser features are available.'
      : `Missing features: ${missingFeatures.join(', ')}. Please update your browser.`
  };
  checks.push(browserFeaturesCheck);
  if (missingFeatures.length > 0) {
    allPassed = false;
    failedChecks.push(browserFeaturesCheck);
  }
  
  // Display results
  resultsContainer.innerHTML = checks.map(check => {
    const icon = check.passed ? '✓' : '✗';
    const className = check.passed ? 'check-pass' : 'check-fail';
    return `<li class="${className}"><strong>${icon} ${check.name}:</strong> ${check.message}</li>`;
  }).join('');
  
  // Update status
  if (allPassed) {
    statusContainer.textContent = '✓ All checks passed! Your device is ready for the investigation.';
    statusContainer.className = 'check-status check-pass';
    
    // Remove troubleshooting section if it exists
    const troubleshootingSection = checkSection.querySelector('.troubleshooting-section');
    if (troubleshootingSection) {
      troubleshootingSection.remove();
    }
  } else {
    statusContainer.textContent = '⚠ Some checks failed. Please review the issues below.';
    statusContainer.className = 'check-status check-warning';
    
    // Add troubleshooting section
    let troubleshootingSection = checkSection.querySelector('.troubleshooting-section');
    if (!troubleshootingSection) {
      troubleshootingSection = document.createElement('div');
      troubleshootingSection.className = 'troubleshooting-section';
      checkSection.appendChild(troubleshootingSection);
    }
    
    const troubleshootingSteps = getTroubleshootingSteps(failedChecks);
    let troubleshootingHTML = '<h3>Troubleshooting Steps</h3>';
    
    troubleshootingSteps.forEach((section, index) => {
      troubleshootingHTML += `<div class="troubleshooting-group">`;
      troubleshootingHTML += `<h4>${section.title}</h4>`;
      troubleshootingHTML += '<ol>';
      section.steps.forEach(step => {
        troubleshootingHTML += `<li>${step}</li>`;
      });
      troubleshootingHTML += '</ol>';
      troubleshootingHTML += '</div>';
    });
    
    troubleshootingHTML += `
      <div class="contact-section">
        <h4>Still Having Issues?</h4>
        <p>If these steps don't resolve the problem, please contact us for assistance. Include details about which checks failed and what device/browser you're using.</p>
        <p><strong>Contact:</strong> <a href="mailto:${SUPPORT_EMAIL}">${SUPPORT_EMAIL}</a></p>
      </div>
    `;
    
    troubleshootingSection.innerHTML = troubleshootingHTML;
  }
}

// Run checks when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', function() {
    // Only run if we're on the test clue page
    if (document.getElementById('technical-check-results')) {
      runTechnicalChecks();
    }
  });
} else {
  // DOM already loaded
  if (document.getElementById('technical-check-results')) {
    runTechnicalChecks();
  }
}

})();
