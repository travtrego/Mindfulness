import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

const source = readFileSync(new URL('../docs/elevenlabs-player.js', import.meta.url), 'utf8')
  .split('  prepareSession = function')[0];
const flush = async () => { for (let i = 0; i < 30; i++) await Promise.resolve(); };
function setup(mode) {
  const timers = new Map(); let timerId = 0, finish;
  const audio = { pause() {}, removeAttribute() { this.src = ''; }, load() {},
    readyState: mode === 'decode-hang' ? 0 : 1, duration: 60,
    addEventListener() {}, removeEventListener() {} };
  const context = {
    prepareSession() {}, Audio: function () { return audio; },
    URL: { createObjectURL() { return 'blob:test'; }, revokeObjectURL() {} },
    AbortController, currentSession: {script:'test narration'}, voicePreference:'lower',
    startSessionBtn: {dataset:{}}, genNote:{}, playback:{}, updatePlayer() {},
    cur:'generate', go(name) { context.cur = name; },
    document: {addEventListener() {}},
    setTimeout(fn) { timers.set(++timerId, fn); return timerId; },
    clearTimeout(id) { timers.delete(id); },
    fetch(url, options) {
      context.signal = options.signal;
      if (mode === 'network') return Promise.reject(new Error('network'));
      if (mode === 'hang') return new Promise(resolve => { finish = resolve; });
      return Promise.resolve({ok:true, blob:async () => ({size:1})});
    },
  };
  vm.createContext(context); vm.runInContext(source, context);
  return {context, timers, late() { finish({ok:true,blob:async()=>({size:1})}); }};
}
for (const mode of ['network','hang','decode-hang']) {
  const {context, timers, late} = setup(mode);
  context.prepareNaturalAudio(context.currentSession);
  await flush();
  if (mode !== 'network') { for (const timer of timers.values()) timer(); await flush(); }
  assert.equal(context.startSessionBtn.disabled, false, mode);
  assert.equal(context.startSessionBtn.dataset.action, 'retry-voice', mode);
  assert.equal(context.naturalAudioReady, false);
  assert.equal(context.signal.aborted, true);
  if (mode === 'hang') { late(); await flush(); assert.equal(context.naturalAudioReady, false); }
}
const success = setup('success');
success.context.prepareNaturalAudio(success.context.currentSession);
await flush();
assert.equal(success.context.naturalAudioReady, true);
assert.equal(success.timers.size, 0);
const cancelled = setup('hang');
cancelled.context.prepareNaturalAudio(cancelled.context.currentSession);
cancelled.context.go('home');
assert.equal(cancelled.context.signal.aborted, true);
assert.equal(cancelled.timers.size, 0);
console.log('Voice loading checks passed: success, network failure, deadline, decode stall, cancellation, late response.');
