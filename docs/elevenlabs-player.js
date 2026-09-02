
  // ---- ElevenLabs narration adapter -----------------------------------------
  // This file is injected inside the app's existing IIFE by scripts/serve.py, so it can
  // reuse the player UI/state while replacing browser speechSynthesis with one real MP3.
  var devicePrepareSession = prepareSession;
  var naturalAudio = new Audio();
  var naturalAudioUrl = null;
  var naturalAudioReady = false;
  var naturalAudioPending = false;
  var naturalAudioToken = 0;

  naturalAudio.preload = "auto";

  function sessionNarrationText(session) {
    if (session && session.script) return String(session.script);
    return (session && session.beats ? session.beats : []).map(function (beat) {
      return beat && beat.text ? beat.text : "";
    }).filter(Boolean).join("\n\n");
  }

  function clearNaturalAudio() {
    naturalAudio.pause();
    naturalAudio.removeAttribute("src");
    naturalAudio.load();
    if (naturalAudioUrl) URL.revokeObjectURL(naturalAudioUrl);
    naturalAudioUrl = null;
    naturalAudioReady = false;
    naturalAudioPending = false;
  }

  function prepareNaturalAudio(session) {
    var text = sessionNarrationText(session);
    var token = ++naturalAudioToken;
    clearNaturalAudio();
    naturalAudioPending = true;
    startSessionBtn.disabled = true;
    startSessionBtn.textContent = "Preparing voice…";

    fetch("/api/tts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: text, voice: voicePreference })
    }).then(function (response) {
      if (!response.ok) throw new Error("Natural voice unavailable (" + response.status + ")");
      return response.blob();
    }).then(function (blob) {
      if (token !== naturalAudioToken) return;
      if (!blob || !blob.size) throw new Error("Natural voice returned no audio");
      naturalAudioUrl = URL.createObjectURL(blob);
      naturalAudio.src = naturalAudioUrl;
      naturalAudio.load();
      return new Promise(function (resolve, reject) {
        if (naturalAudio.readyState >= 1 && isFinite(naturalAudio.duration)) return resolve();
        var done = function () {
          naturalAudio.removeEventListener("loadedmetadata", done);
          naturalAudio.removeEventListener("error", failed);
          resolve();
        };
        var failed = function () {
          naturalAudio.removeEventListener("loadedmetadata", done);
          naturalAudio.removeEventListener("error", failed);
          reject(new Error("Natural voice could not be decoded"));
        };
        naturalAudio.addEventListener("loadedmetadata", done);
        naturalAudio.addEventListener("error", failed);
      });
    }).then(function () {
      if (token !== naturalAudioToken) return;
      naturalAudioPending = false;
      naturalAudioReady = true;
      playback.total = naturalAudio.duration || playback.total;
      startSessionBtn.disabled = false;
      startSessionBtn.textContent = "Begin session";
      genNote.textContent = "Natural ElevenLabs narration is ready.";
      updatePlayer();
    }).catch(function (error) {
      if (token !== naturalAudioToken) return;
      naturalAudioPending = false;
      naturalAudioReady = false;
      startSessionBtn.disabled = true;
      startSessionBtn.textContent = "Voice unavailable";
      genNote.textContent = error.message + ". Check the ElevenLabs API connection.";
    });
  }

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
    var beatIndex = beatCount ? Math.min(beatCount - 1, Math.floor(ratio * beatCount)) : 0;
    rail.querySelectorAll("i").forEach(function (item, index) {
      item.className = index < beatIndex ? "done" : (index === beatIndex ? "now" : "");
    });

    var beat = playback.beats[beatIndex];
    if (beat && beat.text) {
      var visible = cleanNarration(String(beat.text).replace(/\*\[\s*\d+(?:\.\d+)?\s*s\s*\]\*/gi, " "));
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
