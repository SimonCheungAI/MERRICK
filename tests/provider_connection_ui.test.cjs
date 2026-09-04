const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync(`${__dirname}/../web/app.js`, 'utf8');

function display(state, runtime, attempt = null, online = true) {
  const context = {
    PROVIDERS: {codex: {title: 'Codex'}, custom: {title: 'Custom'}},
    providerCurrent: {dataset: {}}, providerConnectionSummary: {dataset: {}},
    providerActiveModel: {textContent: ''}, providerRuntimeLabel: {textContent: ''},
    providerAttempt: attempt, providerConnectionState: state,
    providerRuntimeState: runtime, providerAuthRequired: false,
    conversationLanguage: 'en', CONNECTION_STAGES: {failed: 'failed'},
    connectionFailureCopy: () => 'verification failed',
    ws: {readyState: online ? 1 : 3}, WebSocket: {OPEN: 1},
  };
  vm.createContext(context);
  vm.runInContext(source.slice(source.indexOf('function displayProviderConnection('), source.indexOf('function applyProviderConnectionState(')), context);
  context.displayProviderConnection(state);
  return context;
}

test('unconfigured account is not connected when local gateway is ready', () => {
  const result = display({provider: 'codex', model: 'gpt-test', configured: false}, {ready: true});
  assert.equal(result.providerConnectionSummary.dataset.state, 'pending');
  assert.match(result.providerConnectionSummary.textContent, /NOT CONNECTED/);
});

test('connection attempt has a visible connecting state', () => {
  const result = display({provider: 'codex', configured: false}, {ready: true}, {status: 'connecting', provider: 'custom', model: 'demo'});
  assert.match(result.providerConnectionSummary.textContent, /CONNECTING.*Custom.*demo/);
});
test('disconnected transport never displays connected', () => {
  const result = display({provider: 'codex', model: 'demo', configured: true}, {ready: true}, null, false);
  assert.equal(result.providerConnectionSummary.dataset.state, 'error');
});
test('failed new connection keeps the existing active model separate', () => {
  const result = display({provider: 'codex', model: 'old', configured: true}, {ready: true}, {status: 'error', provider: 'custom', model: 'new'});
  assert.match(result.providerConnectionSummary.textContent, /CONNECTION FAILED/);
  assert.match(result.providerActiveModel.textContent, /old/);
});

test('a partial login progress message preserves the visible device code and URL', () => {
  const context = {
    selectedProvider: 'codex', providerModelInput: {value: 'demo'}, providerAttempt: null,
    providerConnectionState: {}, providerCancelBtn: {}, providerAuthCard: {hidden: true, scrollIntoView() {}},
    providerDeviceCode: {textContent: '', hidden: true},
    providerVerificationLink: {hidden: true, dataset: {}},
    setProviderSetupStatus() {}, displayProviderConnection() {}, renderProviderForm() {},
    t: key => key,
  };
  context.window = context;
  vm.createContext(context);
  vm.runInContext(source.slice(source.indexOf('window.merrickNativeProviderSetupProgress ='), source.indexOf('function setConversationLanguage(')), context);
  context.merrickNativeProviderSetupProgress({deviceCode: 'ABCD-EFGH', verificationURL: 'https://example.test/device'});
  context.merrickNativeProviderSetupProgress({message: 'Still waiting for browser authorization'});
  assert.match(context.providerDeviceCode.textContent, /ABCD-EFGH/);
  assert.equal(context.providerDeviceCode.hidden, false);
  assert.equal(context.providerVerificationLink.hidden, false);
});
