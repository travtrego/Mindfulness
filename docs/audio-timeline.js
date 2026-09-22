  // Speech is synthesized separately from silence. A single PCM/WAV timeline keeps
  // pauses, seeking and background playback on the media clock, not JS timers.
  var narrationSampleRate = 24000;

  function narrationPlan(session) {
    var parts = [], clips = [];
    var beats = session.beats && session.beats.length ? session.beats
      : [{text: String(session.script || "")}];
    function addSpeech(text, beat) {
      text = cleanNarration(text);
      // Prefer complete sentences; fall back to a word boundary for unusually long ones.
      while (text) {
        var end = Math.min(600, text.length);
        if (text.length > end) {
          var prefix = text.slice(0, end);
          var sentence = /[.!?][\"'’”)]*\s+/g, match, boundary = 0;
          while ((match = sentence.exec(prefix))) boundary = match.index + match[0].length;
          end = boundary || prefix.lastIndexOf(" ");
          if (end <= 0) throw new Error("Narration contains an oversized word");
        }
        var piece = text.slice(0, end).trim();
        if (piece) {
          parts.push({type: "speech", clip: clips.length, beat: beat});
          clips.push({text: piece});
        }
        text = text.slice(end).trim();
      }
    }
    beats.forEach(function (beat, index) {
      var text = String(beat.text || "");
      var marker = /\*\[\s*(\d+(?:\.\d+)?)\s*s\b[^\]]*\]\*/gi, match, cursor = 0;
      while ((match = marker.exec(text))) {
        addSpeech(text.slice(cursor, match.index), index);
        var seconds = Number(match[1]);
        if (seconds > 120) throw new Error("Narration contains an oversized pause");
        if (seconds > 0) parts.push({type: "silence", samples: Math.round(seconds * narrationSampleRate), beat: index});
        cursor = marker.lastIndex;
      }
      addSpeech(text.slice(cursor), index);
    });
    if (!clips.length || clips.length > 200) throw new Error("Invalid narration length");
    clips.forEach(function (clip, index) {
      clip.previous_text = index ? clips[index - 1].text : "";
      clip.next_text = index + 1 < clips.length ? clips[index + 1].text : "";
    });
    return {parts: parts, clips: clips};
  }

  function narrationWav(plan, buffers) {
    var samples = 0, spans = [], body = [];
    var secondOfSilence = new Uint8Array(narrationSampleRate * 2);
    plan.parts.forEach(function (part) {
      var count;
      if (part.type === "silence") {
        count = part.samples;
        var left = count * 2;
        while (left > 0) {
          var length = Math.min(left, secondOfSilence.length);
          body.push(secondOfSilence.subarray(0, length));
          left -= length;
        }
      } else {
        var pcm = buffers[part.clip];
        if (!(pcm instanceof ArrayBuffer) || !pcm.byteLength || pcm.byteLength % 2)
          throw new Error("Invalid narration samples");
        count = pcm.byteLength / 2;
        body.push(pcm);
      }
      var start = samples / narrationSampleRate;
      samples += count;
      if (samples > narrationSampleRate * 3600) throw new Error("Narration exceeds one hour");
      spans.push({start: start, end: samples / narrationSampleRate, beat: part.beat});
    });
    var header = new ArrayBuffer(44), view = new DataView(header);
    function label(offset, value) {
      for (var i = 0; i < value.length; i++) view.setUint8(offset + i, value.charCodeAt(i));
    }
    label(0, "RIFF"); view.setUint32(4, 36 + samples * 2, true);
    label(8, "WAVE"); label(12, "fmt "); view.setUint32(16, 16, true);
    view.setUint16(20, 1, true); view.setUint16(22, 1, true);
    view.setUint32(24, narrationSampleRate, true); view.setUint32(28, narrationSampleRate * 2, true);
    view.setUint16(32, 2, true); view.setUint16(34, 16, true);
    label(36, "data"); view.setUint32(40, samples * 2, true);
    return {blob: new Blob([header].concat(body), {type: "audio/wav"}),
      duration: samples / narrationSampleRate, spans: spans};
  }
