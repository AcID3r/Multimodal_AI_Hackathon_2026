// Shared browser controller for the local dashboard and the Next.js app.
// No third-party runtime is needed for waveform rendering or SVG charts.
const escapeHtml = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const clock = seconds => `${Math.floor(seconds / 60)}:${(seconds % 60).toFixed(1).padStart(4, '0')}`;
const rubricNames = {vocal_tone:'Vocal tone',pacing_rhythm:'Pacing / rhythm',volume_dynamics:'Volume dynamics',pause_usage:'Pause usage',vocal_clarity:'Vocal clarity proxy'};
const featureNames = {pitch_relative:'Pitch expression',energy_db:'Volume dynamics',speech_rate:'Speech rate',f0:'Raw pitch',spectral_centroid:'Spectral centroid'};

function scaffold() {
  return `<div class="shell">
    <header class="topbar"><div class="brand"><span class="brand-mark" aria-hidden="true">?????</span> cadence<span class="tag">speech lab</span></div><span class="status" id="connection" role="status">Connecting to analysis engine</span></header>
    <div class="hero"><div><div class="eyebrow">Contrastive speech analytics</div><h1>Find your voice.<br>Understand every moment.</h1><p>Compare the same words, hear the difference, and turn measured delivery changes into focused practice.</p></div><div class="hero-number" aria-hidden="true">01 /</div></div>
    <div class="layout"><aside class="panel upload-panel"><span class="step">01 / CHOOSE YOUR COMPARISON</span><h2 style="margin-top:12px">Start an analysis</h2>
      <form id="upload-form"><label for="baseline">Reference delivery</label><select id="baseline" required><option value="">Loading baselines...</option></select><p id="baseline-note" class="optional" style="margin-top:9px"></p>
      <div class="dropzone" id="dropzone"><strong>Drop your recording here</strong><p>WAV, MP3 or FLAC ? up to 50 MB<br>0.5 seconds to 10 minutes</p><input id="audio-file" type="file" accept=".wav,.mp3,.flac" aria-label="Participant audio recording"></div>
      <label for="transcript-input">Transcript ? same words as reference</label><textarea id="transcript-input" aria-describedby="transcript-note"></textarea><small id="transcript-note">Choose a reference to load its text.</small>
      <label for="alignment-mode">Word timing</label><select id="alignment-mode"><option value="forced">Forced alignment (WhisperX)</option><option value="provided">Upload reviewed timing JSON</option><option value="estimated">Approximate timing ? provisional</option></select>
      <div id="alignment-file-wrap" hidden><label for="alignment-file">Word timestamps (.json)</label><input id="alignment-file" type="file" accept=".json"></div>
      <details><summary>Transcript file & sensitivity</summary><label for="transcript-file">Optional transcript file</label><input id="transcript-file" type="file" accept=".txt"><label for="threshold">Deviation threshold</label><input id="threshold" type="number" min="0.5" max="5" step="0.1" value="1.5" style="width:100%;padding:9px;background:#0d1528;border:1px solid var(--line);border-radius:8px"></details>
      <button class="primary" id="analyze-button" type="submit">Analyze my delivery ?</button></form><div id="error" class="error" role="alert" hidden></div>
      <div class="separator"></div><span class="step">02 / EXPLORE THE CONTROLLED TEST</span><p id="demo-note" class="optional" style="margin-top:10px">Synthetic tones test the signal pipeline. These fixtures do not represent human speech accuracy.</p><div class="demo-row"><button data-level="0">Reference</button><button data-level="3">Subtle changes</button><button data-level="2">Moderate changes</button><button data-level="1">Severe changes</button></div>
    </aside><section aria-label="Analysis results"><div id="empty" class="panel empty"><div class="empty-inner"><div class="empty-icon" aria-hidden="true">?</div><div class="eyebrow">Evidence you can hear</div><h2>Every improvement starts<br>with a clear comparison.</h2><p>Upload the same speech as your reference, or explore a controlled fixture to see how pace and volume changes appear on the timeline.</p><span class="tag">Measured features ? repeatable results</span></div></div>
    <div id="results" class="result-grid" hidden><div class="result-actions"><span class="step" id="result-label">DELIVERY REPORT</span><button id="export-button">Export analysis JSON ?</button></div><div id="warnings" class="warnings"></div>
      <div class="score-grid"><div class="panel"><span class="step">OVERALL COMPARISON</span><div class="score-value" id="score"></div><p style="font-size:12px">A heuristic measure of delivery similarity. Intentional stylistic differences can also lower the score.</p><div class="score-meta" id="score-meta"></div></div><div class="panel"><h2>Delivery profile</h2><div id="radar"></div><div id="rubrics" class="rubrics"></div></div></div>
      <div class="panel"><div class="panel-title"><h2>Listen to the evidence</h2><small>Click a region or word to seek</small></div><canvas id="waveform" class="wave-canvas" role="img" aria-label="Participant waveform with detected regions highlighted"></canvas><audio id="player" controls preload="metadata"></audio><div class="playback-status" id="playback-status"></div><details><summary>Listen to the reference recording</summary><audio id="reference-player" controls preload="none"></audio></details></div>
      <div class="panel"><div class="panel-title"><h2>Feature comparison</h2><div class="legend"><span>Reference</span><span>Participant</span></div></div><div class="tabs" id="feature-tabs"></div><div id="feature-chart"></div><small id="feature-unit"></small><p class="optional" style="margin:10px 0 0">Reference time is mapped to the participant by corresponding words. Raw pitch is shown for inspection; tone scoring uses relative pitch range.</p></div>
      <div class="panel"><div class="panel-title"><h2>Moments to practice</h2><span class="tag" id="flaw-count"></span></div><div id="flaws" class="flaw-list"></div></div>
      <div class="panel"><div class="panel-title"><h2>Your words, in context</h2><small>Highlighted words intersect a detected region</small></div><div id="transcript-view" class="transcript"></div></div>
    </div></section></div><footer class="footer"><span>CADENCE / Track C ? Contrastive Speech Analytics</span><span>CPU processing ? local uploads ? no external scoring API</span></footer></div>`;
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
  for (const f of flaws) markup += `<rect x="${x(f.start_time)}" y="${top}" width="${Math.max(1,x(f.end_time)-x(f.start_time))}" height="${height-top-bottom}" fill="#fb9c9c" opacity=".045"/>`;
  for (let i=0;i<=4;i++) {
    const v = min+(max-min)*i/4, t=duration*i/4;
    markup += `<line x1="${left}" x2="${width-right}" y1="${y(v)}" y2="${y(v)}" stroke="#27344b"/><text x="${left-9}" y="${y(v)+4}" fill="#9caac4" font-size="10" text-anchor="end">${v.toFixed(1)}</text><text x="${x(t)}" y="${height-10}" fill="#9caac4" font-size="10" text-anchor="middle">${clock(t)}</text>`;
  }
  return `<svg class="feature-chart" viewBox="0 0 ${width} ${height}" role="img" aria-label="Reference and participant feature contours"><g>${markup}<path d="${path(series.baseline)}" fill="none" stroke="#80e3c2" stroke-width="2"/><path d="${path(series.participant)}" fill="none" stroke="#9ca8ff" stroke-width="2"/></g></svg>`;
}

function radarChart(scores) {
  const values = Object.values(scores), center = [155,100], radius = 70;
  const point = (i, r) => [center[0]+Math.sin(i*2*Math.PI/5)*r,center[1]-Math.cos(i*2*Math.PI/5)*r];
  const points = r => values.map((_,i)=>point(i,r).join(',')).join(' ');
  const labels = ['Tone','Pace','Volume','Pauses','Clarity'];
  return `<svg class="radar" viewBox="0 0 310 205" role="img" aria-label="Five-dimension delivery rubric"><g>${[.25,.5,.75,1].map(r=>`<polygon points="${points(radius*r)}" fill="none" stroke="#34405a"/>`).join('')}${values.map((_,i)=>{const p=point(i,radius),l=point(i,radius+20);return `<line x1="155" y1="100" x2="${p[0]}" y2="${p[1]}" stroke="#34405a"/><text x="${l[0]}" y="${l[1]+4}" text-anchor="middle" font-size="10" fill="#9caac4">${labels[i]}</text>`;}).join('')}<polygon points="${values.map((v,i)=>point(i,v/10*radius).join(',')).join(' ')}" fill="#9ca8ff30" stroke="#9ca8ff" stroke-width="2"/></g></svg>`;
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
    $('baseline-note').textContent=selected.kind==='synthetic_fixture'?'Controlled signal fixture ? not human speech':`${selected.speaker} ? ${selected.human_reviewed?'Reviewed baseline':'Review pending'}`;
  };
  const setBusy = busy => {
    state.busy=busy;
    root.querySelectorAll('button[data-level],#analyze-button,#baseline').forEach(el=>el.disabled=busy);
    $('analyze-button').textContent=busy?'Processing audio...':'Analyze my delivery ?';
    $('connection').classList.toggle('busy',busy);
    $('connection').textContent=busy?'Extracting & comparing features':'Analysis engine ready';
  };
  const selectFeature = name => {
    state.feature=name;
    if (!state.result) return;
    root.querySelectorAll('[data-feature]').forEach(el=>el.classList.toggle('active',el.dataset.feature===name));
    $('feature-chart').innerHTML=lineChart(state.result.feature_timeseries[name],state.result.flaw_regions,state.result.duration_seconds);
    $('feature-unit').textContent=`Unit: ${state.result.feature_timeseries[name].unit}`;
  };
  const drawWaveform = () => {
    if (!state.result) return;
    const canvas=$('waveform'), cssWidth=canvas.clientWidth||700, ratio=devicePixelRatio||1;
    canvas.width=cssWidth*ratio;canvas.height=130*ratio;
    const ctx=canvas.getContext('2d');ctx.scale(ratio,ratio);
    const duration=state.result.duration_seconds;
    for(const flaw of state.result.flaw_regions){ctx.fillStyle='#fb9c9c20';ctx.fillRect(flaw.start_time/duration*cssWidth,0,(flaw.end_time-flaw.start_time)/duration*cssWidth,130);}
    ctx.strokeStyle='#80e3c2';ctx.beginPath();
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
    $('flaws').innerHTML=result.flaw_regions.length?result.flaw_regions.map(f=>`<article class="flaw-card" data-flaw="${f.id}"><div class="flaw-heading"><h3>${escapeHtml(f.type.replaceAll('_',' '))}</h3><span class="badge">${escapeHtml(f.severity_label)}</span></div><small>${clock(f.start_time)} ? ${clock(f.end_time)}</small><div class="quote">?${escapeHtml(f.transcript_segment)}?</div><p>${escapeHtml(f.causal_explanation.summary)}</p><div class="advice">${escapeHtml(f.causal_explanation.recommendation)}</div><details><summary>Inspect the math</summary><div class="math">${escapeHtml(f.causal_explanation.mathematical_detail)}</div></details><button class="play-section" data-play="${f.id}">? Play this section</button></article>`).join(''):'<p>No deviations crossed the configured threshold. This indicates delivery similarity, not a guarantee of rhetorical quality.</p>';
    root.querySelectorAll('[data-play]').forEach(el=>on(el,'click',()=>{const f=result.flaw_regions.find(f=>f.id===el.dataset.play);seekAndPlay(f.start_time,f.end_time);}));
    $('transcript-view').innerHTML=result.alignment.words.map((word,i)=>{const flawed=result.flaw_regions.some(f=>f.start_time<word.end&&f.end_time>word.start);return `<button class="word ${flawed?'flawed':''}" data-word="${i}" title="${clock(word.start)} ? ${clock(word.end)}">${escapeHtml(word.word)}</button>`;}).join(' ');
    root.querySelectorAll('[data-word]').forEach(el=>on(el,'click',()=>seekAndPlay(result.alignment.words[Number(el.dataset.word)].start)));
    $('playback-status').textContent=`0:00.0 / ${clock(result.duration_seconds)}`;
    loadWaveform(url,result.analysis_id);
  };
  on($('baseline'),'change',baselineChanged);
  on($('alignment-mode'),'change',()=>{$('alignment-file-wrap').hidden=$('alignment-mode').value!=='provided';});
  on($('transcript-file'),'change',async event=>{const file=event.target.files[0];if(file) $('transcript-input').value=await file.text();});
  on($('dropzone'),'dragover',event=>{event.preventDefault();$('dropzone').classList.add('over');});
  on($('dropzone'),'dragleave',()=>{$('dropzone').classList.remove('over');});
  on($('dropzone'),'drop',event=>{event.preventDefault();$('dropzone').classList.remove('over');if(event.dataTransfer.files.length){const transfer=new DataTransfer();transfer.items.add(event.dataTransfer.files[0]);$('audio-file').files=transfer.files;}});
  on($('upload-form'),'submit',async event=>{
    event.preventDefault();if(state.busy)return;showError('');
    const file=$('audio-file').files[0],mode=$('alignment-mode').value;
    if(!file){showError('Choose an audio recording first.');return;}
    if(file.size>50*1024*1024){showError('Audio exceeds the 50 MB limit.');return;}
    if(mode==='provided'&&!$('alignment-file').files[0]){showError('Choose the word-timing JSON file.');return;}
    const data=new FormData();data.append('audio',file);data.append('baseline_id',$('baseline').value);data.append('transcript_text',$('transcript-input').value);data.append('alignment_mode',mode==='estimated'?'estimated':'forced');data.append('threshold',$('threshold').value);
    if($('alignment-file').files[0]&&mode==='provided')data.append('alignment',$('alignment-file').files[0]);
    setBusy(true);try{const result=await fetchJson('/api/analyze',{method:'POST',body:data});if(!state.disposed)render(result,URL.createObjectURL(file),true);}catch(error){if(error.name!=='AbortError')showError(error.message);}finally{if(!state.disposed)setBusy(false);}
  });
  root.querySelectorAll('[data-level]').forEach(button=>on(button,'click',async()=>{
    if(state.busy)return;showError('');const id=$('baseline').value;if(!id){showError('Choose a baseline first.');return;}
    const level=Number(button.dataset.level);setBusy(true);
    try{const result=await fetchJson(`/api/demo/${encodeURIComponent(id)}/${level}`,{method:'POST'});if(!state.disposed)render(result,`${apiBase}/api/baselines/${encodeURIComponent(id)}/audio?variant=${level?'flawed_level_'+level:'ideal'}`);}catch(error){if(error.name!=='AbortError')showError(error.message);}finally{if(!state.disposed)setBusy(false);}
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
    state.baselines=baselines;$('connection').textContent='Analysis engine ready';
    $('baseline').innerHTML=baselines.length?baselines.map(b=>`<option value="${escapeHtml(b.id)}">${escapeHtml(b.title)}</option>`).join(''):'<option value="">No baselines available</option>';
    baselineChanged();if(!baselines.length)showError('No dataset found. Run: python -m scripts.build_dataset --demo');
    if(!health.whisperx_available){$('alignment-mode').value='provided';$('alignment-file-wrap').hidden=false;$('transcript-note').textContent='WhisperX is not installed. Upload timing JSON or explicitly choose approximate mode.';}
  }).catch(error=>{if(error.name!=='AbortError'){$('connection').textContent='Analysis engine unavailable';showError(`Could not reach the backend: ${error.message}`);}});
  return ()=>{state.disposed=true;controller.abort();resize.disconnect();player.pause();$('reference-player').pause();state.context?.close();if(state.audioUrl)URL.revokeObjectURL(state.audioUrl);root.innerHTML='';};
}
