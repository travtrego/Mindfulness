import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
const source = readFileSync('docs/audio-timeline.js','utf8') + '\n' +
  readFileSync('docs/elevenlabs-player.js','utf8').split('  prepareSession = function')[0];
const flush = async()=>{for(let i=0;i<100;i++) await Promise.resolve();};
function setup(mode, full=false) {
  const timers = new Map(); let timerId=0, finish;
  const audio = {paused:true,currentTime:0,ended:false,play(){this.paused=false;return Promise.resolve();},pause(){this.paused=true;},removeAttribute(){this.src='';},load(){},
    readyState:mode==='decode-hang'?0:1,duration:14,addEventListener(){},removeEventListener(){}};
  const calls=[];
  const response=()=>({ok:true,headers:{get:n=>n==='X-Narration-Voice'?'voice':'24000'},
    arrayBuffer:async()=>new ArrayBuffer(48000)});
  const context={prepareSession(session){context.playback.beats=session.beats;},Audio:function(){return audio;},
    URL:{createObjectURL(){return 'blob:test';},revokeObjectURL(){}},
    AbortController,ArrayBuffer,Uint8Array,DataView,Blob,
    currentSession:{script:'First. *[12s]* Second.'},voicePreference:'lower',
    cleanNarration:t=>t.trim(),formatTime:s=>String(s),
    startSessionBtn:{dataset:{}},genNote:{},playback:{},updatePlayer(){},
    cur:'generate',go(name){context.cur=name;},document:{addEventListener(){},
      querySelectorAll(){return [];}, getElementById(){return {}; }},
    window:{addEventListener(){}},startGeneration(){},
    wave:{querySelectorAll(){return [];}},rail:{querySelectorAll(){return [];}},
    elapsedEl:{},remainEl:{},narr:{},paceLabel:{},hint:{style:{}},
    controls:{classList:{add(){}}},updateMediaPosition(){},holdWakeLock(){},releaseWakeLock(){},
    setMediaState(){},setPauseIcon(){},finishSession(){},setInterval(){return 1;},clearInterval(){},
    setTimeout(fn){timers.set(++timerId,fn);return timerId;},clearTimeout(id){timers.delete(id);},
    fetch(url,options){
      calls.push(JSON.parse(options.body)); context.signal=options.signal;
      if(mode==='network') return Promise.reject(new Error('network'));
      if(mode==='hang') return new Promise(resolve=>{finish=resolve;});
      if(mode==='second-fails' && calls.length===2) return Promise.reject(new Error('network'));
      return Promise.resolve(response());
    }};
  vm.createContext(context);
  vm.runInContext(full ? readFileSync('docs/audio-timeline.js','utf8') + '\n' +
    readFileSync('docs/elevenlabs-player.js','utf8') : source, context);
  return {context,timers,calls,late(){finish(response());}};
}
for(const mode of ['network','hang','decode-hang']) {
  const {context,timers,late}=setup(mode);
  context.prepareNaturalAudio(context.currentSession); await flush();
  if(mode!=='network') {for(const fn of Array.from(timers.values())) fn();await flush();}
  // Aborting fetch rejects in browsers. The hang stub deliberately ignores abort,
  // so resolve late to verify it still cannot become playable.
  if(mode==='hang') {late();await flush();}
  assert.equal(context.startSessionBtn.disabled,false,mode);
  assert.equal(context.startSessionBtn.dataset.action,'retry-voice',mode);
  assert.equal(context.naturalAudioReady,false);
  assert.equal(context.signal.aborted,true);
  assert.equal(timers.size,0);
}
const success=setup('success');
await success.context.prepareNaturalAudio(success.context.currentSession);
assert.equal(success.context.naturalAudioReady,true);
assert.equal(success.context.playback.total,14);
assert.equal(success.calls[0].pinned_voice,null);
assert.equal(success.calls[1].pinned_voice,'voice');
assert.equal(success.timers.size,0);
const retry=setup('second-fails');
await retry.context.prepareNaturalAudio(retry.context.currentSession);
assert.equal(retry.context.startSessionBtn.dataset.action,'retry-voice');
await retry.context.prepareNaturalAudio(retry.context.currentSession);
assert.equal(retry.context.naturalAudioReady,true);
assert.equal(retry.calls.filter(c=>c.text==='First.').length,1,'successful clips reused on retry');
const cancelled=setup('hang');
cancelled.context.prepareNaturalAudio(cancelled.context.currentSession);
cancelled.context.go('home');cancelled.late();await flush();
assert.equal(cancelled.context.signal.aborted,true);
assert.equal(cancelled.context.naturalAudioReady,false);
assert.equal(cancelled.timers.size,0);
console.log('Voice loading: PCM success, pinned voice, failures, cancellation and cached retry passed.');

const controls=setup('success',true);
controls.context.currentSession.beats=[{text:'First. *[12s]* Second.'}];
controls.context.playback.beats=controls.context.currentSession.beats;
await controls.context.prepareNaturalAudio(controls.context.currentSession);
controls.context.startPlayback();
assert.equal(controls.context.cur,'play');
assert.equal(controls.context.naturalAudio.paused,false);
controls.context.seekBy(10); // Seeking INTO real silence uses the same media clock.
assert.equal(controls.context.naturalAudio.currentTime,10);
controls.context.pausePlayback();
assert.equal(controls.context.naturalAudio.paused,true);
controls.context.resumePlayback();
assert.equal(controls.context.naturalAudio.paused,false);
controls.context.seekBy(-5);
assert.equal(controls.context.naturalAudio.currentTime,5);
controls.context.stopPlayback();
assert.equal(controls.context.naturalAudio.currentTime,0);
assert.equal(controls.context.playback.playing,false);
console.log('Full player adapter: begin, seek into silence, pause, resume and stop passed (simulated media element).');
