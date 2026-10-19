/**
 * Reminder email page (/reminder-email/)
 * Two buttons copy the finished email, for pasting into Eventbrite: one as the
 * formatted email, one as its HTML code. The email is fetched from the same file
 * the preview shows, so there is one copy to keep up to date.
 */
(function() {
'use strict';

const COPIED = {
  email: 'Copied. Now paste it into Eventbrite’s message box.',
  code: 'Copied the HTML code. Now paste it into Eventbrite’s HTML view.'
};
const FAILED = 'Couldn’t copy. Select the email below and copy it by hand.';

// Everything inside the email's <body>, which is what goes into a message box
async function fetchEmailBody(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Could not load the email (${response.status})`);
  const doc = new DOMParser().parseFromString(await response.text(), 'text/html');
  return doc.body.innerHTML.trim();
}

// The clipboard write must start inside the click (Safari refuses it otherwise),
// so it is given a promise for the content, not the content itself.
function copy(type, mime, bodyPromise) {
  const blob = bodyPromise.then(body => new Blob([body], { type: mime }));
  return navigator.clipboard.write([new ClipboardItem({ [mime]: blob })]);
}

document.addEventListener('DOMContentLoaded', function() {
  const page = document.querySelector('.reminder-email');
  const status = page.querySelector('.reminder-status');
  let bodyPromise = null;

  page.querySelectorAll('[data-copy]').forEach(button => {
    button.addEventListener('click', async () => {
      const type = button.dataset.copy;
      bodyPromise = bodyPromise || fetchEmailBody(page.dataset.emailUrl);
      try {
        await copy(type, type === 'email' ? 'text/html' : 'text/plain', bodyPromise);
        status.textContent = COPIED[type];
      } catch (e) {
        bodyPromise = null;
        status.textContent = FAILED;
      }
    });
  });
});

})();
