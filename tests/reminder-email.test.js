/** @jest-environment jsdom */
const fs = require('fs');
const path = require('path');

// Use the real page markup and the real email so the tests can't drift from either
const page = fs.readFileSync(path.join(__dirname, '../src/reminder-email/index.njk'), 'utf8')
  .replace(/^---[\s\S]*?---/, '')
  .replace(/\{\{[^}]*\}\}/g, '/site/');
const email = fs.readFileSync(path.join(__dirname, '../marketing/reminder_email/reminder_email.html'), 'utf8');

class FakeClipboardItem {
  constructor(data) {
    this.data = data;
    this.types = Object.keys(data);
  }

  async getType(type) {
    return this.data[type];
  }
}

const readBlob = blob => new Promise(resolve => {
  const reader = new FileReader();
  reader.onload = () => resolve(reader.result);
  reader.readAsText(blob);
});

let written;
let fetchEmail;

function load() {
  document.body.innerHTML = page;
  written = [];
  window.ClipboardItem = FakeClipboardItem;
  // Like the real clipboard, the write fails if the content it was promised fails
  Object.defineProperty(navigator, 'clipboard', {
    configurable: true,
    value: {
      write: jest.fn(async items => {
        for (const item of items) {
          for (const type of item.types) written.push({ type, text: await readBlob(await item.getType(type)) });
        }
      })
    }
  });
  window.fetch = fetchEmail;

  // Capture the script's own listener so earlier loads can't also react
  const domReady = [];
  jest.spyOn(document, 'addEventListener').mockImplementation((type, fn) => {
    if (type === 'DOMContentLoaded') domReady.push(fn);
  });
  jest.resetModules();
  require('../src/js/reminder-email');
  document.addEventListener.mockRestore();
  domReady.forEach(fn => fn());
}

const status = () => document.querySelector('.reminder-status').textContent;
const flush = () => new Promise(resolve => setTimeout(resolve, 0));
const click = async which => {
  document.querySelector(`[data-copy="${which}"]`).click();
  await flush();
  await flush();
};

beforeEach(() => {
  fetchEmail = jest.fn().mockResolvedValue({ ok: true, text: async () => email });
  load();
});

afterEach(() => jest.restoreAllMocks());

test('Copy email puts the formatted email body on the clipboard, without the head', async () => {
  await click('email');
  expect(written).toHaveLength(1);
  expect(written[0].type).toBe('text/html');
  expect(written[0].text).toContain('Prepare my phone');
  expect(written[0].text).toContain('href="https://lostsouls.door66.events/check/"');
  expect(written[0].text).toContain('qr-check.png');
  expect(written[0].text).not.toMatch(/<title|<style|<html/i);
  expect(status()).toContain('Copied');
});

test('Copy HTML code puts the same markup on the clipboard as text', async () => {
  await click('code');
  expect(written).toHaveLength(1);
  expect(written[0].type).toBe('text/plain');
  expect(written[0].text).toContain('<table');
  expect(written[0].text).toContain('Prepare my phone');
  expect(status()).toContain('HTML code');
});

test('loads the email from the address the page names', async () => {
  await click('email');
  expect(fetchEmail).toHaveBeenCalledWith('/site/reminder-email/email.html');
});

test('starts the copy inside the click, before the email has loaded', () => {
  // Safari only allows a clipboard write that begins during the click itself
  fetchEmail.mockReturnValue(new Promise(() => {}));
  document.querySelector('[data-copy="email"]').click();
  expect(navigator.clipboard.write).toHaveBeenCalledTimes(1);
});

test('says so when the email cannot be loaded', async () => {
  fetchEmail.mockResolvedValue({ ok: false, status: 404, text: async () => '<html><body>Not found</body></html>' });
  await click('email');
  expect(written).toHaveLength(0);
  expect(status()).toContain('Couldn’t copy');
});

test('says so when the browser refuses the copy', async () => {
  navigator.clipboard.write.mockRejectedValue(new Error('denied'));
  await click('email');
  expect(status()).toContain('Couldn’t copy');
});

describe('staying out of search engines', () => {
  const robots = html => (html.match(/<meta name="robots" content="([^"]*)"/) || [])[1] || '';

  test('the hosted email asks search engines to skip it and the images in it', () => {
    expect(robots(email)).toContain('noindex');
    expect(robots(email)).toContain('noimageindex');
  });

  test('the page itself gets noindex from the shared layout', () => {
    const base = fs.readFileSync(path.join(__dirname, '../src/_includes/base.njk'), 'utf8');
    const layout = fs.readFileSync(path.join(__dirname, '../src/_includes/standalone.njk'), 'utf8');
    expect(robots(base)).toContain('noindex');
    expect(layout).toContain('extends "base.njk"');
  });
});
