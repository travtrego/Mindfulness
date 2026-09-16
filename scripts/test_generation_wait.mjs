// Execute the actual fetch wrapper with a virtual clock: no model calls or long sleeps.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

const liveUrl = process.argv[2];
const source = liveUrl
  ? await (await fetch(liveUrl)).text()
  : readFileSync(new URL('./serve.py', import.meta.url), 'utf8');
const script = source.match(/<script>\s*(\(function \(\) \{[\s\S]*?\}\)\(\);)\s*<\/script>/)?.[1];
assert.ok(script, 'production fetch wrapper found');

function harness(mode) {
  let clock = 0, id = 0;
  const timers = new Map(), calls = [];
  let resolveLive, rejectLive;
  const live = new Promise((resolve, reject) => { resolveLive = resolve; rejectLive = reject; });
  const window = {
    location: { href: 'https://example.com/' },
    fetch(resource, options) {
      calls.push({ resource, options });
      if (resource === '/api/reference') return Promise.resolve({ ok: true, reference: true });
      if (resource !== '/api/generate') return Promise.resolve({ ok: true, unrelated: true });
      options.signal.addEventListener('abort', () => rejectLive(new Error('aborted')));
      if (mode === 'network') rejectLive(new Error('offline'));
      if (mode === 'http') resolveLive({ ok: false, status: 504 });
      return live;
    },
  };
  vm.runInNewContext(script, {
    window, URL, AbortController,
    setTimeout(fn, delay) { timers.set(++id, { fn, at: clock + delay }); return id; },
    clearTimeout(key) { timers.delete(key); },
  });
  return {
    window, calls, resolveLive, timers,
    async advance(ms) {
      clock += ms;
      for (const [key, timer] of timers) if (timer.at <= clock) { timers.delete(key); timer.fn(); }
      for (let n = 0; n < 10; n++) await Promise.resolve();
    },
  };
}

const slow = harness();
const body = JSON.stringify({ category: 'Nature', answers: [{ answer: '10 min' }] });
const pending = slow.window.fetch('/api/generate', { method: 'POST', body });
await slow.advance(134000);
assert.equal(slow.calls.length, 1, '134-second live generation must not fall back');
assert.equal(slow.calls[0].options.signal.aborted, false);
slow.resolveLive({ ok: true, quality_layer: { active: true } });
assert.equal((await pending).quality_layer.active, true);
assert.equal(slow.timers.size, 0, 'successful request clears watchdog');

const hung = harness();
const timeoutResult = hung.window.fetch('/api/generate', { method: 'POST', body });
await hung.advance(300000);
assert.equal(hung.calls.length, 1, 'browser must allow entire server budget');
await hung.advance(10000);
assert.equal((await timeoutResult).reference, true);
assert.equal(hung.calls[1].options.body, body, 'fallback retains selected category');

for (const mode of ['network', 'http']) {
  const failed = harness(mode);
  assert.equal((await failed.window.fetch('/api/generate', { body })).reference, true);
  assert.equal(failed.calls.length, 2);
}
const other = harness();
assert.equal((await other.window.fetch('/api/questions', {})).unrelated, true);
assert.equal(other.timers.size, 0);
console.log(`Generation wait checks passed (${liveUrl ? 'deployed' : 'local'} wrapper): slow success, deadline, HTTP/network fallback, unrelated requests.`);
