// Shared browser controller for the local dashboard and the Next.js app.
// No third-party runtime is needed for waveform rendering or SVG charts.
const escapeHtml = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const clock = seconds => `${Math.floor(seconds / 60)}:${(seconds % 60).toFixed(1).padStart(4, '0')}`;
const rubricNames = {vocal_tone:'Vocal tone',pacing_rhythm:'Pacing / rhythm',volume_dynamics:'Volume dynamics',pause_usage:'Pause usage',vocal_clarity:'Vocal clarity proxy'};
const featureNames = {pitch_relative:'Pitch expression',energy_db:'Volume dynamics',speech_rate:'Speech rate',f0:'Raw pitch',spectral_centroid:'Spectral centroid'};

// Inline interface icons keep both entry points self-contained.
const logoUrl = new URL('./cadence-logo.png', import.meta.url).href;
function icon(name, size = 18) {
  const paths = {
    arrow: '<path d="M5 12h14m-6-6 6 6-6 6"/>',
    diagonal: '<path d="M6 18 18 6M6 6h12v12"/>',
    upload: '<path d="M12 16V4m-5 5 5-5 5 5M4 16v4h16v-4"/>',
    play: '<path d="m9 5 11 7-11 7z"/>',
    wave: '<path d="M3 10v4m4-8v12m5-16v20m5-16v12m4-8v4"/>',
    file: '<path d="M14 2H6v20h12V6zm0 0v5h5M9 12h6m-6 4h6"/>',
    target: '<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3"/><path d="M12 1v3m0 16v3M1 12h3m16 0h3"/>',
    download: '<path d="M12 3v12m-5-5 5 5 5-5M4 17v4h16v-4"/>',
    check: '<path d="m5 12 4 4L19 6"/>',
    microphone: '<rect x="9" y="2" width="6" height="12" rx="3"/><path d="M5 10v2a7 7 0 0 0 14 0v-2m-7 9v3m-4 0h8"/>',
  };
  return `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths[name] || paths.wave}</svg>`;
}

function scaffold() {
  return `<div class="shell">
    <a class="skip-link" href="#workspace">Skip to speech analysis</a>
    <header class="topbar">
      <a class="brand" href="#top" aria-label="Cadence home"><span class="brand-logo"><img src="${logoUrl}" width="72" height="48" alt=""></span><span>cadence<span class="brand-period">.</span></span><span class="brand-caption">THE SPEECH LAB</span></a>
      <nav class="topnav" aria-label="Main navigation"><a href="#workspace">Workspace</a><a href="#how-it-works">The process</a><a class="nav-cta" href="#workspace">Find your voice ${icon('diagonal',14)}</a></nav>
    </header>
    <section class="hero" id="top" aria-labelledby="hero-title">
      <div class="hero-copy"><div class="eyebrow"><span class="live-dot"></span> A little practice. A lasting impression.</div>
      <h1 id="hero-title">Make every<br>word <span class="hero-emphasis">land.</span><span class="title-star" aria-hidden="true">*</span></h1>
      <p class="hero-description">Great delivery is in the details. Hear the difference, find your rhythm, and turn your next recording into your next breakthrough.</p>
      <div class="hero-actions"><a class="button hero-primary" href="#workspace">Enter the practice room ${icon('arrow')}</a><button class="text-button" id="hero-demo" type="button"><span class="play-orbit">${icon('play',13)}</span> Explore a sample</button></div>
      <div class="hero-note"><span class="tiny-cross" aria-hidden="true">+</span> Your words. Your voice. A clearer perspective.</div></div>
      <div class="hero-art" aria-label="Cadence speech and sound logo"><span class="art-corner top-left"></span><span class="art-corner top-right"></span><span class="art-corner bottom-left"></span><span class="art-corner bottom-right"></span>
        <div class="art-topline"><span>VOICE, IN FOCUS</span><span>CD / 01</span></div><img class="hero-logo" src="${logoUrl}" width="768" height="512" alt="Cadence logo: a speaker profile surrounded by a blue and cyan sound wave">
        <div class="art-bottomline"><span><i class="live-dot"></i> Built for better delivery</span><span class="art-coordinates">LISTEN / REFLECT / REPEAT</span></div>
      </div>
    </section>
    <div class="capability-strip" aria-label="Speech evaluation dimensions"><span class="strip-label">THE DETAILS THAT MATTER</span><span>${icon('wave',15)} Vocal tone</span><span>${icon('arrow',15)} Pacing & rhythm</span><span>${icon('microphone',15)} Volume dynamics</span><span>${icon('target',15)} Pause placement</span><span>${icon('file',15)} Clarity proxy</span></div>
    <section class="process-strip" id="how-it-works" aria-label="How Cadence works"><div class="process-label"><span class="eyebrow">THE PROCESS</span><p>From a recording<br>to a little more confidence.</p></div><div class="process-step"><span class="process-number">01</span><div><h2>Bring your words.</h2><p>Choose a reference and upload your reading of the same text.</p></div></div><div class="process-step"><span class="process-number">02</span><div><h2>See the difference.</h2><p>Compare the details of your delivery, moment by moment.</p></div></div><div class="process-step"><span class="process-number">03</span><div><h2>Make it yours.</h2><p>Listen to specific sections and focus your next practice.</p></div></div></section>
    <section id="workspace" class="workspace" aria-labelledby="workspace-title"><div class="workspace-heading"><div><span class="eyebrow">A SPACE TO GET BETTER</span><h2 id="workspace-title">The practice room<span>.</span></h2></div><span class="status" id="connection" role="status">Connecting to analysis engine</span></div>
    <div class="layout"><aside class="panel upload-panel"><div class="upload-heading"><span class="step">01 / YOUR RECORDING</span>${icon('microphone',20)}</div><h3>Let's hear it.</h3><p class="panel-intro">Start with a reference. Then add your take.</p>
      <form id="upload-form"><label for="baseline">Reference delivery <span>01</span></label><select id="baseline" required><option value="">Loading references...</option></select><p id="baseline-note" class="optional baseline-note"></p>
      <div class="dropzone" id="dropzone"><span class="upload-icon">${icon('upload',24)}</span><strong id="file-label">Drop your audio here</strong><p id="file-description">WAV, MP3 or FLAC <span aria-hidden="true">&middot;</span> up to 50 MB</p><span class="browse-label">or browse files ${icon('diagonal',12)}</span><input id="audio-file" type="file" accept=".wav,.mp3,.flac" aria-label="Participant audio recording" aria-describedby="file-description"></div>
      <label for="transcript-input">Your words <span>02</span></label><textarea id="transcript-input" aria-describedby="transcript-note" placeholder="Your reference transcript will appear here."></textarea><small id="transcript-note">Read the same words as your reference.</small>
      <label for="alignment-mode">Word timing <span>03</span></label><select id="alignment-mode"><option value="forced">Forced alignment (WhisperX)</option><option value="provided">Upload reviewed timing JSON</option><option value="estimated">Approximate timing - provisional</option></select>
      <div id="alignment-file-wrap" hidden><label for="alignment-file">Word timestamps (.json)</label><input id="alignment-file" type="file" accept=".json"></div>
      <details class="advanced-options"><summary>Fine-tune your session</summary><label for="transcript-file">Optional transcript file</label><input id="transcript-file" type="file" accept=".txt"><label for="threshold">Deviation threshold</label><input id="threshold" type="number" min="0.5" max="5" step="0.1" value="1.5"></details>
      <button class="primary" id="analyze-button" type="submit"><span>Analyze my delivery</span>${icon('arrow')}</button></form><div id="error" class="error" role="alert" hidden></div>
      <div class="sample-section"><div class="sample-heading"><span class="step">JUST EXPLORING?</span><span class="sample-tag">SAMPLE LAB</span></div><p id="demo-note" class="optional">Synthetic tones test the signal pipeline. These fixtures do not represent human speech accuracy.</p><div class="demo-row"><button data-level="0" type="button" aria-pressed="false"><span class="sample-dot reference"></span>Reference</button><button data-level="3" type="button" aria-pressed="false"><span class="sample-dot subtle"></span>Subtle changes</button><button data-level="2" type="button" aria-pressed="false"><span class="sample-dot moderate"></span>Moderate changes</button><button data-level="1" type="button" aria-pressed="false"><span class="sample-dot severe"></span>Severe changes</button></div></div>
    </aside><section class="analysis-column" aria-label="Analysis results"><div id="empty" class="panel empty"><div class="empty-topline"><span class="step">02 / THE BIGGER PICTURE</span><span class="empty-state-label"><span class="live-dot"></span> READY WHEN YOU ARE</span></div>
      <div class="empty-inner"><div class="empty-graphic" aria-hidden="true"><span class="orbit orbit-one"></span><span class="orbit orbit-two"></span><span class="orbit orbit-three"></span><div class="signal-bars">${Array.from({length:25},(_,i)=>`<i style="--bar:${16 + Math.round((Math.sin(i * 1.7) ** 2) * (1 - Math.abs(i - 12) / 15) * 72)}px;--delay:${i*35}ms"></i>`).join('')}</div><span class="signal-axis horizontal"></span><span class="signal-axis vertical"></span></div><span class="eyebrow">A FRESH PERSPECTIVE</span><h3>Your delivery.<br>Under the lens.</h3><p>Your recordings hold a story. Add yours to see where your rhythm, expression, and emphasis differ from the reference.</p><button id="empty-upload" class="text-button" type="button">Start with your recording ${icon('arrow',16)}</button></div>
      <div class="empty-features"><div>${icon('wave',19)}<span>See the signal<small>Aligned feature comparisons</small></span></div><div>${icon('target',19)}<span>Find the moment<small>Feedback tied to timestamps</small></span></div><div>${icon('play',19)}<span>Hear it again<small>Focused section playback</small></span></div></div>
    </div>
    <div id="results" class="result-grid" hidden><div class="result-actions"><span class="step" id="result-label">YOUR DELIVERY REPORT</span><button id="export-button" class="export-button" type="button">${icon('download',15)} Export report</button></div><details class="warnings disclosure" id="warnings-wrap"><summary>About your results <span id="warning-count"></span></summary><div id="warnings"></div></details>
      <div class="score-grid"><div class="panel score-panel"><div class="panel-kicker"><span class="step">DELIVERY SIMILARITY</span>${icon('target',20)}</div><div class="score-value" id="score"></div><div class="score-scale"><span>ROOM TO EXPLORE</span><span>CLOSER MATCH</span></div><div class="score-meter"><i id="score-meter-fill"></i></div><p class="score-description">A measure of similarity to the reference. Intentional stylistic differences can also lower this score.</p><div class="score-meta" id="score-meta"></div></div><div class="panel profile-panel"><div class="panel-kicker"><h3>Your delivery profile</h3><span class="step">5 DIMENSIONS</span></div><div id="radar"></div><div id="rubrics" class="rubrics"></div></div></div>
      <div class="panel playback-panel"><div class="panel-title"><div><span class="step">LISTEN CLOSER</span><h3>Every moment matters.</h3></div><small>Click a region or word to seek</small></div><canvas id="waveform" class="wave-canvas" role="img" aria-label="Participant waveform with detected regions highlighted"></canvas><audio id="player" controls preload="metadata"></audio><div class="playback-status" id="playback-status"></div><details><summary>Compare with the reference recording</summary><audio id="reference-player" controls preload="none"></audio></details></div>
      <div class="panel"><div class="panel-title"><div><span class="step">SIDE BY SIDE</span><h3>Read between the waves.</h3></div><div class="legend"><span>Reference</span><span>Participant</span></div></div><div class="tabs" id="feature-tabs" role="group" aria-label="Choose a feature"></div><div id="feature-chart"></div><small id="feature-unit"></small><p class="optional chart-note">Reference time is mapped to your recording by corresponding words. Tone scoring uses relative pitch range.</p></div>
      <div class="panel"><div class="panel-title"><div><span class="step">YOUR NEXT STEP</span><h3>Moments worth another take.</h3></div><span class="tag" id="flaw-count"></span></div><div id="flaws" class="flaw-list"></div></div>
      <div class="panel"><div class="panel-title"><div><span class="step">WORD BY WORD</span><h3>The story in your transcript.</h3></div><small>Click a word to listen</small></div><div id="transcript-view" class="transcript"></div></div>
    </div></section></div></section><footer class="footer"><a class="brand footer-brand" href="#top"><span class="brand-logo"><img src="${logoUrl}" width="72" height="48" alt=""></span><span>cadence<span class="brand-period">.</span></span></a><p>A little more intention.<br>A little more you.</p><span class="footer-meta">CONTRASTIVE SPEECH ANALYTICS<br>TRACK C / 2026</span><a class="back-to-top" href="#top" aria-label="Back to top">${icon('diagonal',20)}</a></footer></div>`;
}

function lineChart(series, flaws, duration) {
  const width = 820, height = 245, left = 52, top = 18, right = 16, bottom = 34;
  const values = [...series.baseline, ...series.participant].filter(Number.isFinite);
  if (!values.length) return '<p>No reliable data for this feature.</p>';
  let min = Math.min(...values), max = Math.max(...values);
  const padding = Math.max(.2, (max - min) * .12); min -= padding; max += padding;
  const x = t => left + t / duration * (width - left - right);
  const y = v => height - bottom - (v - min) / (max - min) * (height - top - bottom);
  const path = vals => {let drawing = false; return vals.map((v, i) => {
    if (!Number.isFinite(v)) {drawing = false; return '';}
    const point = `${drawing ? 'L' : 'M'}${x(series.timestamps[i]).toFixed(2)},${y(v).toFixed(2)}`; drawing = true; return point;
  }).join(' ');};
  let markup = '';
  for (const f of flaws) markup += `<rect x="${x(f.start_time)}" y="${top}" width="${Math.max(1,x(f.end_time)-x(f.start_time))}" height="${height-top-bottom}" fill="#f4a69b" opacity=".045"/>`;
  for (let i=0;i<=4;i++) {
    const v = min+(max-min)*i/4, t=duration*i/4;
    markup += `<line x1="${left}" x2="${width-right}" y1="${y(v)}" y2="${y(v)}" stroke="#252a2e"/><text x="${left-9}" y="${y(v)+4}" fill="#898f95" font-size="10" text-anchor="end">${v.toFixed(1)}</text><text x="${x(t)}" y="${height-10}" fill="#898f95" font-size="10" text-anchor="middle">${clock(t)}</text>`;
  }
  return `<svg class="feature-chart" viewBox="0 0 ${width} ${height}" role="img" aria-label="Reference and participant feature contours"><g>${markup}<path d="${path(series.baseline)}" fill="none" stroke="#6be4f5" stroke-width="2"/><path d="${path(series.participant)}" fill="none" stroke="#91a7ff" stroke-width="2"/></g></svg>`;
}

function radarChart(scores) {
  const values = Object.values(scores), center = [155,100], radius = 70;
  const point = (i, r) => [center[0]+Math.sin(i*2*Math.PI/5)*r,center[1]-Math.cos(i*2*Math.PI/5)*r];
  const points = r => values.map((_,i)=>point(i,r).join(',')).join(' ');
  const labels = ['Tone','Pace','Volume','Pauses','Clarity'];
  return `<svg class="radar" viewBox="0 0 310 205" role="img" aria-label="Five-dimension delivery rubric"><g>${[.25,.5,.75,1].map(r=>`<polygon points="${points(radius*r)}" fill="none" stroke="#30373b"/>`).join('')}${values.map((_,i)=>{const p=point(i,radius),l=point(i,radius+20);return `<line x1="155" y1="100" x2="${p[0]}" y2="${p[1]}" stroke="#30373b"/><text x="${l[0]}" y="${l[1]+4}" text-anchor="middle" font-size="10" fill="#898f95">${labels[i]}</text>`;}).join('')}<polygon points="${values.map((v,i)=>point(i,v/10*radius).join(',')).join(' ')}" fill="#91a7ff30" stroke="#91a7ff" stroke-width="2"/></g></svg>`;
}

export function mountDashboard(root, apiBase) {
  root.innerHTML = scaffold();
  apiBase = apiBase.replace(/\/$/, '');
  const $ = id => root.querySelector(`#${id}`);
  const controller = new AbortController();
  const state = {baselines:[],result:null,busy:false,feature:'pitch_relative',audioUrl:null,samples:null,sectionEnd:null,context:null,disposed:false};
  const player = $('player');
  const events = {signal:controller.signal};
  const on = (element, type, handler) => element.addEventListener(type, handler, events);
  const showError = message => { $('error').textContent=message; $('error').hidden=!message; };
  const fetchJson = async (path, options={}) => {
    const response = await fetch(`${apiBase}${path}`, {...options,signal:controller.signal});
    const body = await response.json();
    if (!response.ok) throw new Error(typeof body.detail==='string' ? body.detail : JSON.stringify(body.detail));
    return body;
  };
  const baselineChanged = () => {
    const selected = state.baselines.find(b=>b.id===$('baseline').value);
    if (!selected) return;
    $('transcript-input').value=selected.transcript;
    $('demo-note').textContent=selected.kind==='synthetic_fixture'?'Synthetic tones test the signal pipeline. These fixtures do not represent human speech accuracy.':'Prebuilt variants use known pace and volume transformations. Review their word timings and labels before treating them as evaluation ground truth.';
    $('baseline-note').textContent=selected.kind==='synthetic_fixture'?'Synthetic signal fixture / not human speech':`${selected.speaker} / ${selected.human_reviewed?'Reviewed baseline':'Review pending'}`;
  };
  const setBusy = busy => {
    state.busy=busy;
    root.querySelectorAll('button[data-level],#analyze-button,#baseline,#hero-demo').forEach(el=>el.disabled=busy);
    $('analyze-button').innerHTML=busy?'<span>Listening for the details...</span><span class="button-spinner" aria-hidden="true"></span>':`<span>Analyze my delivery</span>${icon('arrow')}`;
    root.setAttribute('aria-busy',String(busy));
    $('connection').classList.toggle('busy',busy);
    $('connection').dataset.state=busy?'processing':'ready';
    $('connection').textContent=busy?'Extracting & comparing features':'Analysis engine ready';
  };
  const selectFeature = name => {
    state.feature=name;
    if (!state.result) return;
    root.querySelectorAll('[data-feature]').forEach(el=>{el.classList.toggle('active',el.dataset.feature===name);el.setAttribute('aria-pressed',String(el.dataset.feature===name));});
    $('feature-chart').innerHTML=lineChart(state.result.feature_timeseries[name],state.result.flaw_regions,state.result.duration_seconds);
    $('feature-unit').textContent=`Unit: ${state.result.feature_timeseries[name].unit}`;
  };
  const drawWaveform = () => {
    if (!state.result) return;
    const canvas=$('waveform'), cssWidth=canvas.clientWidth||700, ratio=devicePixelRatio||1;
    canvas.width=cssWidth*ratio;canvas.height=130*ratio;
    const ctx=canvas.getContext('2d');ctx.scale(ratio,ratio);
    const duration=state.result.duration_seconds;
    for(const flaw of state.result.flaw_regions){ctx.fillStyle='#f4a69b20';ctx.fillRect(flaw.start_time/duration*cssWidth,0,(flaw.end_time-flaw.start_time)/duration*cssWidth,130);}
    ctx.strokeStyle='#6be4f5';ctx.beginPath();
    if(state.samples){const data=state.samples,step=Math.max(1,Math.floor(data.length/cssWidth));for(let x=0;x<cssWidth;x++){let peak=0;for(let j=x*step;j<Math.min(data.length,(x+1)*step);j++)peak=Math.max(peak,Math.abs(data[j]));const amp=Math.max(1,peak*170);ctx.moveTo(x,65-amp);ctx.lineTo(x,65+amp);}}
    else{ctx.moveTo(0,65);ctx.lineTo(cssWidth,65);}
    ctx.stroke();ctx.strokeStyle='#fff';const x=player.currentTime/duration*cssWidth;ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,130);ctx.stroke();
  };
  const loadWaveform = async (url, reportId) => {
    state.samples=null;drawWaveform();
    try{const response=await fetch(url,{signal:controller.signal});if(!response.ok)throw new Error('Audio is unavailable');
      const Context=window.AudioContext||window.webkitAudioContext;
      state.context ||= new Context();const buffer=await state.context.decodeAudioData(await response.arrayBuffer());
      if(state.result?.analysis_id===reportId){state.samples=buffer.getChannelData(0);drawWaveform();}
    }catch(error){if(error.name!=='AbortError')$('playback-status').textContent='Waveform decoding is unavailable; use the audio player.';}
  };
  const seekAndPlay = async (start,end=null) => {
    player.currentTime=start;state.sectionEnd=end;
    try{await player.play();}catch{$('playback-status').textContent='Press play in the audio controls to listen.';}
  };
  const render = (result,url,isObjectUrl=false) => {
    player.pause();state.sectionEnd=null;
    if(state.audioUrl)URL.revokeObjectURL(state.audioUrl);
    state.audioUrl=isObjectUrl?url:null;state.result=result;
    $('empty').hidden=true;$('results').hidden=false;
    $('result-label').textContent=`DELIVERY REPORT / ${result.analysis_id.slice(0,8)}`;
    $('score').innerHTML=`${result.overall_score.toFixed(0)}<span>/ 100</span>`;
    $('score-meter-fill').style.width=`${Math.max(0,Math.min(100,result.overall_score))}%`;
    $('warning-count').textContent=`${result.warnings.length} notes`;
    $('warnings-wrap').open=result.warnings.some(w=>/Approximate timing|synthetic|few frames/i.test(w));
    $('score-meta').innerHTML=`<span class="tag">${clock(result.duration_seconds)}</span><span class="tag">${escapeHtml(result.alignment.method)} timing</span>`;
    $('warnings').innerHTML=result.warnings.map(w=>`<div>${escapeHtml(w)}</div>`).join('');
    $('radar').innerHTML=radarChart(result.rubric_scores);
    $('rubrics').innerHTML=Object.entries(result.rubric_scores).map(([key,value])=>`<div><div class="rubric-row"><span>${rubricNames[key]||escapeHtml(key)}</span><strong>${value.toFixed(1)} / 10</strong></div><div class="rubric-track"><div class="rubric-fill" style="width:${value*10}%"></div></div></div>`).join('');
    player.src=url;
    $('reference-player').src=`${apiBase}/api/baselines/${encodeURIComponent(result.baseline_id)}/audio`;
    $('feature-tabs').innerHTML=Object.keys(featureNames).map(key=>`<button data-feature="${key}" class="${key===state.feature?'active':''}">${featureNames[key]}</button>`).join('');
    root.querySelectorAll('[data-feature]').forEach(el=>on(el,'click',()=>selectFeature(el.dataset.feature)));
    selectFeature(state.feature);
    $('flaw-count').textContent=`${result.flaw_regions.length} regions`;
    $('flaws').innerHTML=result.flaw_regions.length?result.flaw_regions.map(f=>`<article class="flaw-card" data-flaw="${f.id}"><div class="flaw-heading"><h3>${escapeHtml(f.type.replaceAll('_',' '))}</h3><span class="badge">${escapeHtml(f.severity_label)}</span></div><small>${clock(f.start_time)} &ndash; ${clock(f.end_time)}</small><div class="quote">&ldquo;${escapeHtml(f.transcript_segment)}&rdquo;</div><p>${escapeHtml(f.causal_explanation.summary)}</p><div class="advice">${escapeHtml(f.causal_explanation.recommendation)}</div><details><summary>Inspect the math</summary><div class="math">${escapeHtml(f.causal_explanation.mathematical_detail)}</div></details><button class="play-section" data-play="${f.id}">${icon('play',13)} Play this section</button></article>`).join(''):'<p>No deviations crossed the configured threshold. This indicates delivery similarity, not a guarantee of rhetorical quality.</p>';
    root.querySelectorAll('[data-play]').forEach(el=>on(el,'click',()=>{const f=result.flaw_regions.find(f=>f.id===el.dataset.play);seekAndPlay(f.start_time,f.end_time);}));
    $('transcript-view').innerHTML=result.alignment.words.map((word,i)=>{const flawed=result.flaw_regions.some(f=>f.start_time<word.end&&f.end_time>word.start);return `<button class="word ${flawed?'flawed':''}" data-word="${i}" title="${clock(word.start)} - ${clock(word.end)}">${escapeHtml(word.word)}</button>`;}).join(' ');
    root.querySelectorAll('[data-word]').forEach(el=>on(el,'click',()=>seekAndPlay(result.alignment.words[Number(el.dataset.word)].start)));
    $('playback-status').textContent=`0:00.0 / ${clock(result.duration_seconds)}`;
    loadWaveform(url,result.analysis_id);
  };
  const updateFileLabel = () => {
    const file=$('audio-file').files[0];
    $('file-label').textContent=file?file.name:'Drop your audio here';
    $('file-description').textContent=file?`${(file.size/1024/1024).toFixed(2)} MB / ready to compare`:'WAV, MP3 or FLAC / up to 50 MB';
    $('dropzone').classList.toggle('has-file',Boolean(file));
  };
  on($('audio-file'),'change',updateFileLabel);
  on($('empty-upload'),'click',()=>{$('audio-file').focus({preventScroll:true});$('dropzone').scrollIntoView({behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth',block:'center'});$('audio-file').click();});
  on($('hero-demo'),'click',()=>{if(state.busy)return;root.querySelector('[data-level="2"]').click();$('workspace').scrollIntoView({behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth',block:'start'});});
  on($('baseline'),'change',baselineChanged);
  on($('alignment-mode'),'change',()=>{$('alignment-file-wrap').hidden=$('alignment-mode').value!=='provided';});
  on($('transcript-file'),'change',async event=>{const file=event.target.files[0];if(file) $('transcript-input').value=await file.text();});
  on($('dropzone'),'dragover',event=>{event.preventDefault();$('dropzone').classList.add('over');});
  on($('dropzone'),'dragleave',()=>{$('dropzone').classList.remove('over');});
  on($('dropzone'),'drop',event=>{event.preventDefault();$('dropzone').classList.remove('over');if(event.dataTransfer.files.length){const transfer=new DataTransfer();transfer.items.add(event.dataTransfer.files[0]);$('audio-file').files=transfer.files;updateFileLabel();}});
  on($('upload-form'),'submit',async event=>{
    event.preventDefault();if(state.busy)return;showError('');
    const file=$('audio-file').files[0],mode=$('alignment-mode').value;
    if(!file){showError('Choose an audio recording first.');return;}
    if(file.size>50*1024*1024){showError('Audio exceeds the 50 MB limit.');return;}
    if(mode==='provided'&&!$('alignment-file').files[0]){showError('Choose the word-timing JSON file.');return;}
    const data=new FormData();data.append('audio',file);data.append('baseline_id',$('baseline').value);data.append('transcript_text',$('transcript-input').value);data.append('alignment_mode',mode==='estimated'?'estimated':'forced');data.append('threshold',$('threshold').value);
    if($('alignment-file').files[0]&&mode==='provided')data.append('alignment',$('alignment-file').files[0]);
    setBusy(true);try{const result=await fetchJson('/api/analyze',{method:'POST',body:data});if(!state.disposed){render(result,URL.createObjectURL(file),true);root.querySelectorAll('[data-level]').forEach(el=>el.setAttribute('aria-pressed','false'));}}catch(error){if(error.name!=='AbortError')showError(error.message);}finally{if(!state.disposed)setBusy(false);}
  });
  root.querySelectorAll('[data-level]').forEach(button=>on(button,'click',async()=>{
    if(state.busy)return;showError('');const id=$('baseline').value;if(!id){showError('Choose a baseline first.');return;}
    const level=Number(button.dataset.level);setBusy(true);
    try{const result=await fetchJson(`/api/demo/${encodeURIComponent(id)}/${level}`,{method:'POST'});if(!state.disposed){render(result,`${apiBase}/api/baselines/${encodeURIComponent(id)}/audio?variant=${level?'flawed_level_'+level:'ideal'}`);root.querySelectorAll('[data-level]').forEach(el=>el.setAttribute('aria-pressed',String(el===button)));}}catch(error){if(error.name!=='AbortError')showError(error.message);}finally{if(!state.disposed)setBusy(false);}
  }));
  on(player,'timeupdate',()=>{
    if(!state.result)return;const t=player.currentTime;if(state.sectionEnd!==null&&t>=state.sectionEnd){player.pause();state.sectionEnd=null;}
    $('playback-status').textContent=`${clock(t)} / ${clock(state.result.duration_seconds)}`;
    root.querySelectorAll('[data-word]').forEach(el=>{const w=state.result.alignment.words[Number(el.dataset.word)];el.classList.toggle('active',w.start<=t&&w.end>=t);});
    root.querySelectorAll('[data-flaw]').forEach(el=>{const f=state.result.flaw_regions.find(f=>f.id===el.dataset.flaw);el.classList.toggle('active',f.start_time<=t&&f.end_time>=t);});drawWaveform();
  });
  on($('waveform'),'click',event=>{if(!state.result)return;const bounds=event.currentTarget.getBoundingClientRect();player.currentTime=Math.max(0,Math.min(state.result.duration_seconds,(event.clientX-bounds.left)/bounds.width*state.result.duration_seconds));state.sectionEnd=null;drawWaveform();});
  on($('export-button'),'click',()=>{if(!state.result)return;const url=URL.createObjectURL(new Blob([JSON.stringify(state.result,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download=`cadence-${state.result.analysis_id}.json`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
  const resize=new ResizeObserver(drawWaveform);resize.observe($('waveform'));
  Promise.all([fetchJson('/api/health'),fetchJson('/api/baselines')]).then(([health,baselines])=>{
    state.baselines=baselines;$('connection').textContent='Analysis engine ready';$('connection').dataset.state='ready';
    $('baseline').innerHTML=baselines.length?baselines.map(b=>`<option value="${escapeHtml(b.id)}">${escapeHtml(b.title)}</option>`).join(''):'<option value="">No baselines available</option>';
    baselineChanged();if(!baselines.length)showError('No dataset found. Run: python -m scripts.build_dataset --demo');
    if(!health.whisperx_available){$('alignment-mode').value='provided';$('alignment-file-wrap').hidden=false;$('transcript-note').textContent='WhisperX is not installed. Upload timing JSON or explicitly choose approximate mode.';}
  }).catch(error=>{if(error.name!=='AbortError'){$('connection').textContent='Analysis engine unavailable';$('connection').dataset.state='offline';showError(`Could not reach the backend: ${error.message}`);}});
  return ()=>{state.disposed=true;controller.abort();resize.disconnect();player.pause();$('reference-player').pause();state.context?.close();if(state.audioUrl)URL.revokeObjectURL(state.audioUrl);root.innerHTML='';};
}
