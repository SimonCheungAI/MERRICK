// Isolated UI fixtures: no user credentials, provider requests, or live App state.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const { chromium } = require('playwright');

(async () => {
  const root = path.resolve(__dirname, '../web');
  const output = process.env.MERRICK_UI_EVIDENCE || '/tmp/merrick-provider-ui-evidence';
  fs.mkdirSync(output, {recursive: true});
  const server = http.createServer((req, res) => {
    const file = path.resolve(root, '.' + new URL(req.url, 'http://localhost').pathname.replace(/\/$/, '/index.html'));
    if (!file.startsWith(root + '/') || !fs.existsSync(file)) { res.writeHead(404).end(); return; }
    res.setHeader('Content-Type', ({'.js':'text/javascript', '.css':'text/css', '.html':'text/html'})[path.extname(file)] || 'application/octet-stream');
    res.end(fs.readFileSync(file));
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  let browser;
  try {
    browser = await chromium.launch({headless: true, channel: 'chrome'});
    const page = await browser.newPage({viewport: {width: 1100, height: 1000}});
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.addInitScript(() => {
      window.nativeMessages = [];
      window.webkit = {messageHandlers: {jarvis: {postMessage(message) { window.nativeMessages.push(message); }}}};
      window.WebSocket = class {
        static OPEN = 1;
        constructor() { this.readyState = 1; window.testSocket = this; setTimeout(() => this.onopen?.(), 0); }
        send(raw) {
          const msg = JSON.parse(raw);
          if (msg.type === 'provider_models_request') queueMicrotask(() => this.onmessage?.({data: JSON.stringify({
            type: 'provider_models', provider: msg.provider, request_id: msg.request_id, status: 'ready',
            models: [{id: 'fixture-model-a', name: 'Fixture model A'}, {id: 'fixture-model-b', name: 'Fixture model B'}],
          })}));
        }
        close() { this.readyState = 3; }
      };
    });
    await page.goto(`http://127.0.0.1:${server.address().port}/#desktop=1&bridge=fixture`);
    await page.evaluate(() => {
      window.testSocket.onmessage({data: JSON.stringify({type: 'model_runtime_status', ready: true})});
      window.merrickNativeProviderSetupState({provider: 'codex', model: 'fixture-model-a', configured: false, onboardingRequired: true});
    });
    await page.locator('#provider-connection-summary').filter({hasText: 'NOT CONNECTED'}).waitFor();
    await page.screenshot({path: `${output}/desktop-en.png`});
    await page.evaluate(() => {
      window.merrickNativeProviderSetupProgress({deviceCode: 'TEST-CODE1', verificationURL: 'https://fixture.invalid/device'});
      window.merrickNativeProviderSetupProgress({message: 'Waiting for approval'});
    });
    assert.equal(await page.locator('#provider-device-code').innerText(), 'TEST-CODE1');
    assert.equal(await page.locator('#provider-auth-card').isVisible(), true);
    await page.setViewportSize({width: 390, height: 844});
    await page.evaluate(() => window.merrickNativeSpeechLanguage('zh'));
    await page.locator('#provider-auth-card').scrollIntoViewIfNeeded();
    await page.screenshot({path: `${output}/narrow-zh-device-code.png`});
    await page.evaluate(() => window.merrickNativeProviderSetupResult({ok: false, provider: 'codex', configured: false, onboardingRequired: true, message: 'Fixture sign-in expired. Connect again for a new code.'}));
    assert.equal(await page.locator('#provider-auth-card').isVisible(), false);
    assert.equal(await page.locator('#provider-device-code').innerText(), '');
    await page.setViewportSize({width: 1100, height: 1000});
    await page.evaluate(() => window.merrickNativeSpeechLanguage('en'));
    await page.locator('[data-provider="custom"]').click();
    await page.locator('#provider-model-select').selectOption('fixture-model-b');
    await page.locator('#provider-base-url-input').fill('https://fixture.invalid/v1');
    await page.locator('#provider-key-input').fill('fixture-not-a-real-key');
    await page.evaluate(() => window.merrickNativeProviderSetupState({provider: 'codex', model: 'old', configured: false, onboardingRequired: true}));
    assert.equal(await page.locator('#provider-model-input').inputValue(), 'fixture-model-b');
    assert.equal(await page.locator('#provider-key-input').inputValue(), 'fixture-not-a-real-key');
    await page.locator('#provider-connect-btn').click();
    assert.equal(await page.locator('#provider-connect-btn').isDisabled(), true);
    assert.match(await page.locator('#provider-connection-summary').innerText(), /CONNECTING.*Custom/);
    await page.evaluate(() => window.merrickNativeProviderSetupResult({ok: false, provider: 'codex', model: 'old', configured: false, onboardingRequired: true, message: 'Fixture endpoint timed out.'}));
    assert.equal(await page.locator('#provider-model-input').inputValue(), 'fixture-model-b');
    assert.match(await page.locator('#provider-setup-status').innerText(), /Fixture endpoint timed out/);
    assert.equal(await page.locator('#provider-connect-btn').isEnabled(), true);
    await page.setViewportSize({width: 390, height: 844});
    await page.evaluate(() => window.merrickNativeSpeechLanguage('zh'));
    assert.equal(await page.locator('#provider-model-input').inputValue(), 'fixture-model-b');
    await page.locator('.onboarding-card').evaluate(node => { node.scrollTop = 0; });
    await page.screenshot({path: `${output}/narrow-zh-status.png`});
    await page.locator('#provider-model-select').scrollIntoViewIfNeeded();
    await page.screenshot({path: `${output}/narrow-zh-models.png`});
    const overflow = await page.locator('.onboarding-card').evaluate(node => node.scrollWidth > node.clientWidth + 1);
    assert.equal(overflow, false, 'Connection card must not overflow horizontally');
    await page.evaluate(() => window.merrickNativeProviderSetupResult({ok: true, provider: 'custom', model: 'fixture-model-b', baseURL: 'https://fixture.invalid/v1', configured: true, message: 'Verified fixture'}));
    assert.match(await page.locator('#provider-active-model').innerText(), /fixture-model-b/);
    assert.equal(await page.locator('#provider-key-input').inputValue(), '');
    await page.locator('#provider-model-select').selectOption('fixture-model-a');
    await page.locator('#provider-connect-btn').click();
    const request = await page.evaluate(() => window.nativeMessages.filter(msg => msg.action === 'saveProviderAPIKey').at(-1));
    assert.equal(request.reuseSavedKey, true);
    assert.equal(request.model, 'fixture-model-a');
    assert.equal(request.apiKey, '');
    assert.deepEqual(errors, []);
    console.log(JSON.stringify({passed: true, screenshots: output, checks: ['unconfigured', 'catalog selection', 'draft preservation', 'connecting', 'failure retained', 'bilingual narrow layout', 'safe credential reuse'], pageErrors: errors}));
  } finally {
    await browser?.close();
    await new Promise(resolve => server.close(resolve));
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
