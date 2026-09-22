
  // ---- ElevenLabs narration adapter -----------------------------------------
  // This file is injected inside the app's existing IIFE by scripts/serve.py, so it can
  // reuse the player UI/state while replacing browser speechSynthesis with one measured WAV with real silence.
  var devicePrepareSession = prepareSession;
  var naturalAudio = new Audio();
  var naturalAudioUrl = null;
  var naturalAudioReady = false;
  var naturalAudioPending = false;
  var naturalAudioToken = 0;
  var naturalAudioController = null;
  var naturalSpans = [];
  var naturalClipCache = null;
  var naturalMetadataCleanup = function () {};

  naturalAudio.preload = "auto";

  function sessionNarrationText(session) {
    if (session && session.script) return String(session.script);
    return (session && session.beats ? session.beats : []).map(function (beat) {
      return beat && beat.text ? beat.text : "";
    }).filter(Boolean).join("\n\n");
  }

  function clearNaturalAudio() {
    if (naturalAudioController) naturalAudioController.abort();
    naturalMetadataCleanup();
    naturalAudio.pause();
    naturalAudio.removeAttribute("src");
    naturalAudio.load();
    if (naturalAudioUrl) URL.revokeObjectURL(naturalAudioUrl);
    naturalAudioUrl = null;
    naturalAudioReady = false;
    naturalAudioPending = false;
  }

  async function prepareNaturalAudio(session) {
    var token = ++naturalAudioToken;
    clearNaturalAudio();
    naturalSpans = [];
    naturalAudioPending = true;
    var controller = new AbortController();
    naturalAudioController = controller;
    startSessionBtn.disabled = true;
    startSessionBtn.dataset.action = "play-ready";
    startSessionBtn.textContent = "Preparing voice…";

    try {
      var plan = narrationPlan(session);
      var cacheKey = JSON.stringify(plan.clips);
      if (!naturalClipCache || naturalClipCache.key !== cacheKey)
        naturalClipCache = {key: cacheKey, buffers: [], voice: null};
      var cache = naturalClipCache;
      var completed = cache.buffers.filter(Boolean).length;
      async function loadClip(index) {
        if (cache.buffers[index]) return;
        if (controller.signal.aborted) throw new Error("Cancelled");
        var clip = plan.clips[index];
        var timer = setTimeout(function () { controller.abort(); }, 110000);
        try {
          var response = await fetch("/api/tts", {
            method: "POST", headers: {"Content-Type": "application/json"},
            body: JSON.stringify({text: clip.text, voice: voicePreference,
              previous_text: clip.previous_text, next_text: clip.next_text,
              pinned_voice: cache.voice}),
            signal: controller.signal
          });
          if (!response.ok) throw new Error("Voice unavailable");
          var voice = response.headers.get("X-Narration-Voice");
          if (!voice || Number(response.headers.get("X-Audio-Sample-Rate")) !== narrationSampleRate)
            throw new Error("Unsupported narration format");
          if (cache.voice && voice !== cache.voice) throw new Error("Narration voice changed");
          var pcm = await response.arrayBuffer();
          if (token !== naturalAudioToken || controller.signal.aborted) throw new Error("Cancelled");
          if (!pcm.byteLength || pcm.byteLength % 2 || pcm.byteLength > 3600000)
            throw new Error("Invalid narration audio");
          cache.voice = voice;
          cache.buffers[index] = pcm;
          completed++;
          startSessionBtn.textContent = "Preparing voice · " + completed + "/" + plan.clips.length;
        } finally { clearTimeout(timer); }
      }
      // Resolve one voice first, then pin it for every clip. Two requests at a time
      // avoid a burst against the provider and keep all responses small.
      await loadClip(0);
      var next = 1;
      async function worker() {
        while (next < plan.clips.length && !controller.signal.aborted) {
          var index = next++;
          await loadClip(index);
        }
      }
      await Promise.all([worker(), worker()]);
      if (token !== naturalAudioToken || controller.signal.aborted) return;
      var rendered = narrationWav(plan, cache.buffers);
      naturalSpans = rendered.spans;
      naturalAudioUrl = URL.createObjectURL(rendered.blob);
      naturalAudio.src = naturalAudioUrl;
      naturalAudio.defaultPlaybackRate = 1;
      naturalAudio.playbackRate = 1;
      naturalAudio.load();
      await new Promise(function (resolve, reject) {
        var timer;
        function cleanup() {
          clearTimeout(timer);
          naturalAudio.removeEventListener("loadedmetadata", done);
          naturalAudio.removeEventListener("error", failed);
          controller.signal.removeEventListener("abort", failed);
        }
        function done() { cleanup(); resolve(); }
        function failed() { cleanup(); reject(new Error("Narration could not be loaded")); }
        naturalMetadataCleanup = failed;
        if (naturalAudio.readyState >= 1 && isFinite(naturalAudio.duration)) return done();
        naturalAudio.addEventListener("loadedmetadata", done);
        naturalAudio.addEventListener("error", failed);
        controller.signal.addEventListener("abort", failed, {once: true});
        timer = setTimeout(failed, 15000);
      });
      if (token !== naturalAudioToken || controller.signal.aborted) return;
      naturalMetadataCleanup = function () {};
      naturalAudioPending = false;
      naturalAudioReady = true;
      playback.total = rendered.duration;
      startSessionBtn.disabled = false;
      startSessionBtn.textContent = "Begin · " + formatTime(rendered.duration);
      var requested = Number(session.requested_duration_s || session.duration_s);
      genNote.textContent = "Recording length: " + formatTime(rendered.duration) + ".";
      if (requested > 0 && Math.abs(rendered.duration - requested) > Math.max(30, requested * .1)) {
        genNote.textContent += " You selected about " + Math.round(requested / 60) +
          " minutes. This recording is " + (rendered.duration < requested ? "shorter" : "longer") +
          "; you can play it or return to choose another session.";
      }
      updatePlayer();
    } catch (error) {
      if (token !== naturalAudioToken) return;
      ++naturalAudioToken;
      clearNaturalAudio();
      startSessionBtn.disabled = false;
      startSessionBtn.dataset.action = "retry-voice";
      startSessionBtn.textContent = "Retry voice";
      genNote.textContent = "Your session text is saved here. Voice preparation did not finish. Retry voice or return to the menu.";
    }
  }

  document.addEventListener("click", function (event) {
    var button = event.target.closest("[data-action='retry-voice']");
    if (!button || !currentSession) return;
    event.preventDefault();
    prepareNaturalAudio(currentSession);
  });

  var naturalBaseGo = go;
  go = function (name) {
    if (cur === "generate" && name !== "generate" && name !== "play") {
      ++naturalAudioToken;
      clearNaturalAudio();
    }
    return naturalBaseGo(name);
  };

  prepareSession = function (session) {
    devicePrepareSession(session);
    prepareNaturalAudio(session);
  };

  function naturalClockTick() {
    if (!naturalAudioReady) return;
    playback.elapsed = naturalAudio.currentTime || 0;
    playback.total = naturalAudio.duration || playback.total;
    playback.playing = !naturalAudio.paused && !naturalAudio.ended;
    updatePlayer();
  }

  startPlayback = function () {
    if (!currentSession || !naturalAudioReady) return;
    go("play");
    clearInterval(playback.clock);
    playback.elapsed = 0;
    playback.total = naturalAudio.duration || playback.total;
    playback.playing = true;
    naturalAudio.currentTime = 0;
    playback.clock = setInterval(naturalClockTick, 200);
    holdWakeLock();
    setMediaState("playing");
    controls.classList.add("on");
    hint.style.opacity = "0";
    setPauseIcon(true);
    naturalAudio.play().catch(function () {
      playback.playing = false;
      setPauseIcon(false);
      paceLabel.textContent = "tap play";
    });
    updatePlayer();
  };

  pausePlayback = function () {
    if (!naturalAudioReady || !playback.playing) return;
    naturalAudio.pause();
    playback.playing = false;
    playback.elapsed = naturalAudio.currentTime || playback.elapsed;
    setPauseIcon(false);
    setMediaState("paused");
    paceLabel.textContent = "paused";
    updatePlayer();
  };

  resumePlayback = function () {
    if (!naturalAudioReady || playback.playing) return;
    playback.playing = true;
    holdWakeLock();
    setPauseIcon(true);
    setMediaState("playing");
    naturalAudio.play().catch(function () {
      playback.playing = false;
      setPauseIcon(false);
    });
  };

  seekBy = function (delta) {
    if (!naturalAudioReady || !isFinite(naturalAudio.duration)) return;
    naturalAudio.currentTime = Math.max(0, Math.min(naturalAudio.duration - .05,
      (naturalAudio.currentTime || 0) + delta));
    playback.elapsed = naturalAudio.currentTime;
    updatePlayer();
  };

  stopPlayback = function (reset) {
    clearTimeout(playback.segmentTimer);
    clearInterval(playback.clock);
    playback.segmentTimer = null;
    playback.clock = null;
    playback.playing = false;
    if (naturalAudioReady) {
      naturalAudio.pause();
      if (reset !== false) naturalAudio.currentTime = 0;
    }
    releaseWakeLock();
    setMediaState("none");
    if (reset !== false) playback.elapsed = 0;
    setPauseIcon(false);
  };

  clockTick = naturalClockTick;

  updatePlayer = function () {
    var total = naturalAudioReady && isFinite(naturalAudio.duration)
      ? naturalAudio.duration : (playback.total || 0);
    var elapsed = naturalAudioReady ? (naturalAudio.currentTime || playback.elapsed || 0)
      : (playback.elapsed || 0);
    playback.total = total;
    playback.elapsed = elapsed;
    elapsedEl.textContent = formatTime(elapsed);
    remainEl.textContent = "−" + formatTime(Math.max(0, total - elapsed));

    var ratio = total ? Math.max(0, Math.min(1, elapsed / total)) : 0;
    var bars = wave.querySelectorAll("span");
    bars.forEach(function (bar, index) {
      bar.classList.toggle("p", index / bars.length <= ratio);
    });

    var beatCount = playback.beats.length;
    var span = naturalSpans.find(function (item) { return elapsed < item.end; });
    var beatIndex = span ? span.beat : Math.max(0, beatCount - 1);
    rail.querySelectorAll("i").forEach(function (item, index) {
      item.className = index < beatIndex ? "done" : (index === beatIndex ? "now" : "");
    });

    var beat = playback.beats[beatIndex];
    if (beat && beat.text) {
      var visible = cleanNarration(String(beat.text).replace(/\*\[\s*\d+(?:\.\d+)?\s*s\b[^\]]*\]\*/gi, " "));
      narr.textContent = visible.length > 180 ? visible.slice(0, 177) + "…" : visible;
    }
    updateMediaPosition();
  };

  naturalAudio.addEventListener("ended", function () {
    if (cur === "play") finishSession();
  });

  naturalAudio.addEventListener("play", function () {
    playback.playing = true;
    setPauseIcon(true);
    setMediaState("playing");
  });

  naturalAudio.addEventListener("pause", function () {
    if (naturalAudio.ended) return;
    playback.playing = false;
    setPauseIcon(false);
  });

  window.addEventListener("beforeunload", function () {
    naturalAudio.pause();
    if (naturalAudioUrl) URL.revokeObjectURL(naturalAudioUrl);
  });

  // ---- Product-flow safeguards ----------------------------------------------
  // Every session gets the question/duration screen. Earlier prototype shortcuts for
  // "Just breathing" and "Return to your safe place" jumped directly into generation,
  // which meant the listener could not choose today's duration or add context.
  document.querySelectorAll("#s-home [data-action='generate']").forEach(function (button) {
    button.removeAttribute("data-action");
    button.setAttribute("data-go", "ask");
  });

  // Today's explicit duration becomes the remembered duration used by generation. This is
  // intentionally updated on Create rather than on chip tap, so browsing options does not
  // silently change a preference.
  var baseStartGeneration = startGeneration;
  startGeneration = function (surprise) {
    if (!surprise) {
      var duration = collectAnswers().filter(function (item) {
        return item.fills === "duration";
      })[0];
      if (duration) {
        var match = String(duration.answer).match(/\d+/);
        if (match) writeStore("preferredDurationS", String(Number(match[0]) * 60));
      }
    }
    return baseStartGeneration(surprise);
  };

  // Playback must never be a dead end. "End" still reaches reflection; this is the direct
  // escape hatch for someone who simply wants to leave the session and return to the menu.
  if (!document.getElementById("back-home")) {
    var backHome = document.createElement("button");
    backHome.className = "escape";
    backHome.id = "back-home";
    backHome.textContent = "← Back to main menu";
    backHome.onclick = function (event) {
      event.preventDefault();
      event.stopPropagation();
      stopPlayback();
      go("home");
    };
    controls.insertBefore(backHome, breathingBtn);
  }
