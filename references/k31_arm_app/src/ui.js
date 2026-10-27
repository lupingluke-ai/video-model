/*
 * FORM / 01 — product UI controller.
 * Apple-inspired, original implementation. Pure DOM: imports no model internals,
 * touches no renderer/scene nodes, makes no network requests. Talks only to the
 * runtime `api` object exposed by the application.
 */

const MODES = [
  ['product', 'Product'],
  ['transparent', 'Transparent'],
  ['open', 'Open'],
  ['section', 'Section'],
  ['wiring', 'Wiring'],
  ['explode', 'Explode'],
];
const SKINS = [
  ['frost', 'Frost', '#e6ebf1'],
  ['crystal', 'Crystal', '#f5f9fc'],
  ['smoke', 'Smoke', '#63666b'],
  ['glacier', 'Glacier', '#c2dcea'],
  ['amber', 'Amber', '#e2a75c'],
];
const GESTURES = [
  ['three', 'Three · 3'],
  ['one', 'One · 1'],
  ['relaxed', 'Relaxed'],
  ['open', 'Open'],
  ['fist', 'Fist'],
  ['pinch', 'Pinch'],
  ['point', 'Point'],
  ['peace', 'Peace'],
  ['ripple', 'Ripple'],
  ['wave', 'Wave'],
];
const ARM_POSES_UI = [
  ['rest', 'Rest'],
  ['reach', 'Reach'],
  ['greeting', 'Greeting'],
  ['fold', 'Fold'],
  ['precision', 'Precision'],
];
const VIEWS = [
  ['arm', 'Full arm'],
  ['hand', 'Hand'],
  ['palm', 'Palm'],
  ['forearm', 'Forearm'],
];

const ICON_PAUSE = '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M7 5h3.6v14H7zM13.4 5H17v14h-3.6z"/></svg>';
const ICON_PLAY = '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M8 5.5v13l11-6.5z"/></svg>';

export function initUI(api) {
  api = api || {};
  const $ = (s) => document.querySelector(s);
  const qa = (s) => Array.from(document.querySelectorAll(s));

  /* ------------------------------------------------------------ state */
  const state = {
    mode: 'transparent',
    skin: 'frost',
    gesture: 'relaxed',
    playing: false,
    time: 0,
    shellDepth: 1,
    curl: 0,
    focus: 'arm',
    armAngles: new Array(7).fill(0),
    handAngles: new Array(20).fill(0),
    stats: null,
  };
  const armInfo = normalizeJointInfo(api.armJointInfo, 7, (i) => 'J' + (i + 1), -Math.PI, Math.PI);
  const handInfo = normalizeJointInfo(api.handJointInfo, 20, (i) => 'Joint ' + (i + 1), 0, 1.8);

  function normalizeJointInfo(list, count, fallbackLabel, fbMin, fbMax) {
    const out = [];
    for (let i = 0; i < count; i++) {
      const src = Array.isArray(list) && list[i] ? list[i] : {};
      const min = Number.isFinite(src.min) ? src.min : fbMin;
      const max = Number.isFinite(src.max) && src.max > min ? src.max : fbMax;
      out.push({
        id: typeof src.id === 'string' ? src.id : fallbackLabel(i),
        label: typeof src.label === 'string' && src.label.trim() ? src.label : fallbackLabel(i),
        min, max,
        // contract: joint values are always degrees (metadata.unit === 'deg')
        degrees: src.unit ? src.unit === 'deg' : true,
      });
    }
    return out;
  }

  const listeners = []; // [target, type, fn, opts] for dispose()
  function on(target, type, fn, opts) {
    if (!target) return;
    target.addEventListener(type, fn, opts);
    listeners.push([target, type, fn, opts]);
  }
  function callApi(name, args, failLabel) {
    const fn = api[name];
    if (typeof fn !== 'function') return undefined;
    try { return fn.apply(api, args); }
    catch (err) { toast(failLabel + ' failed: ' + errText(err), true); return undefined; }
  }
  function errText(err) { return (err && err.message) ? err.message : 'unexpected error'; }

  /* ------------------------------------------------------------ toast */
  const toastEl = $('#toast');
  let toastTimer = 0;
  function toast(msg, isErr, sticky) {
    if (!toastEl) return;
    toastEl.textContent = msg;
    toastEl.classList.toggle('err', !!isErr);
    toastEl.classList.add('show');
    clearTimeout(toastTimer);
    if (!sticky) toastTimer = setTimeout(() => toastEl.classList.remove('show'), isErr ? 5200 : 2600);
  }

  /* ------------------------------------------------------------ tour rail */
  const chaptersNav = $('#chapters');
  const btnFree = $('#btnFreeExplore');
  const btnOrbit = $('#btnOrbit');
  let storyState = null;
  const chapterBtns = [];
  function buildChapters() {
    if (!chaptersNav) return;
    const st = api.getStoryState ? api.getStoryState() : null;
    if (!st) return;
    storyState = st;
    chaptersNav.textContent = '';
    chapterBtns.length = 0;
    st.chapters.forEach((c, i) => {
      const b = document.createElement('button');
      b.type = 'button';
      b.dataset.chapter = String(i);
      const dot = document.createElement('span');
      dot.className = 'dot';
      dot.setAttribute('aria-hidden', 'true');
      const lab = document.createElement('span');
      lab.className = 'clabel';
      lab.textContent = c.label;
      b.append(dot, lab);
      b.setAttribute('aria-label', `Chapter ${i + 1}: ${c.label}`);
      on(b, 'click', () => {  callApi('setChapter', [i], 'Chapter'); renderTour(); });
      chaptersNav.appendChild(b);
      chapterBtns.push(b);
    });
    renderTour();
  }
  function renderTour() {
    const st = api.getStoryState ? api.getStoryState() : storyState;
    if (!st) return;
    storyState = st;
    chapterBtns.forEach((b, i) => b.classList.toggle('on', st.active && i === st.chapter));
    if (btnFree) {
      btnFree.setAttribute('aria-pressed', st.active ? 'false' : 'true');
      btnFree.textContent = st.active ? 'Free explore' : 'Resume tour';
    }
    if (btnOrbit) btnOrbit.style.display = st.active ? 'none' : '';
  }
  on(btnFree, 'click', () => {
    
    if (storyState && storyState.active) callApi('freeExplore', [], 'Free explore');
    else callApi('resumeTour', [], 'Resume tour');
    setTimeout(renderTour, 60);
  });
  on(btnOrbit, 'click', () => {  callApi('orbit360', [], 'Orbit'); });
  buildChapters();

  /* ------------------------------------------------------------ capsule groups */
  function makeCapsule(container, group, value, label, swatchColor) {
    if (!container) return null;
    const b = document.createElement('button');
    b.type = 'button';
    b.dataset.group = group;
    b.dataset.value = value;
    b.setAttribute('aria-pressed', 'false');
    if (swatchColor) {
      const s = document.createElement('span');
      s.className = 'swatch';
      s.style.background = swatchColor;
      s.setAttribute('aria-hidden', 'true');
      b.appendChild(s);
    }
    b.appendChild(document.createTextNode(label));
    on(b, 'click', () => selectValue(group, value));
    container.appendChild(b);
    return b;
  }
  function fillGroup(ids, group, pairs, withSwatch) {
    ids.forEach((id) => {
      const c = document.getElementById(id);
      pairs.forEach(([value, label, color]) => makeCapsule(c, group, value, label, withSwatch ? color : null));
    });
  }
  const modeNav = $('#modeNav');
  MODES.forEach(([v, l]) => makeCapsule(modeNav, 'mode', v, l));
  fillGroup(['modeCapsM'], 'mode', MODES);
  fillGroup(['skinCaps', 'skinCapsM'], 'skin', SKINS, true);
  fillGroup(['gestureCaps', 'gestureCapsM'], 'gesture', GESTURES);
  fillGroup(['viewCaps', 'viewCapsM'], 'view', VIEWS);

  function selectValue(group, value) {
    if (group === 'mode') {
      if (api.getStoryState?.().active) callApi('freeExplore', [], 'Free explore');
      setMode(value);
    }
    else if (group === 'skin') { state.skin = value; callApi('setSkin', [value], 'Material change'); }
    else if (group === 'gesture') {
      if (api.getStoryState?.().active) callApi('freeExplore', [], 'Free explore');
      state.gesture = value; callApi('setGesture', [value], 'Gesture change');
    }
    else if (group === 'view') { state.focus = value; callApi('focus', [value], 'Camera move'); }
    closePopovers();
    render();
  }
  function setMode(m) { state.mode = m; callApi('setMode', [m], 'Display mode change'); }

  /* ------------------------------------------------------------ transport */
  const playButtons = [
    { el: $('#btnPlay'), timeline: $('#timeline'), label: $('#tlabel') },
    { el: $('#btnPlayM'), timeline: $('#timelineM'), label: $('#tlabelM') },
    { el: $('#btnMPlay'), timeline: null, label: null },
  ].filter((p) => p.el);
  const timelines = [$('#timeline'), $('#timelineM')].filter(Boolean);
  const tlabels = [$('#tlabel'), $('#tlabelM')].filter(Boolean);
  let scrubbing = false;

  playButtons.forEach((p) => on(p.el, 'click', () => {
    
    state.playing = !state.playing;
    callApi('setPlaying', [state.playing], 'Playback toggle');
    armPoll();
    render();
  }));
  timelines.forEach((t) => {
    on(t, 'pointerdown', () => { scrubbing = true; });
    on(t, 'input', () => {
      state.time = parseFloat(t.value) || 0;
      callApi('setTime', [state.time], 'Timeline scrub');
      renderTime();
    });
    on(t, 'change', () => { scrubbing = false; renderTime(); });
    on(t, 'keyup', () => { scrubbing = false; });
    on(t, 'keydown', () => { scrubbing = true;  });
  });

  /* ------------------------------------------------------------ popovers (mobile) */
  const popButtons = qa('.mpop');
  let openPop = null;
  function closePopovers() {
    if (!openPop) return;
    const panel = document.getElementById(openPop);
    if (panel) panel.hidden = true;
    popButtons.forEach((b) => b.setAttribute('aria-expanded', 'false'));
    openPop = null;
  }
  popButtons.forEach((b) => on(b, 'click', () => {
    
    const id = b.dataset.pop;
    if (openPop === id) { closePopovers(); return; }
    closePopovers();
    const panel = document.getElementById(id);
    if (panel) { panel.hidden = false; openPop = id; b.setAttribute('aria-expanded', 'true'); }
  }));
  on(document, 'pointerdown', (e) => {
    if (!openPop) return;
    const mobile = $('.dock-mobile');
    if (mobile && !mobile.contains(e.target)) closePopovers();
  });

  /* ------------------------------------------------------------ drawer */
  const drawer = $('#drawer');
  const btnDrawer = $('#btnDrawer');
  const scrim = $('#scrim');
  let drawerOpen = false;
  let focusBeforeDrawer = null;

  function openDrawer() {
    if (drawerOpen || !drawer) return;
    
    closePopovers();
    drawerOpen = true;
    focusBeforeDrawer = document.activeElement;
    drawer.classList.add('open');
    drawer.inert = false;
    if (scrim) scrim.classList.add('show');
    if (btnDrawer) btnDrawer.setAttribute('aria-expanded', 'true');
    const closeBtn = $('#btnCloseDrawer');
    if (closeBtn) closeBtn.focus();
  }
  function closeDrawer() {
    if (!drawerOpen || !drawer) return;
    drawerOpen = false;
    drawer.classList.remove('open');
    drawer.inert = true;
    if (scrim) scrim.classList.remove('show');
    if (btnDrawer) btnDrawer.setAttribute('aria-expanded', 'false');
    if (focusBeforeDrawer && focusBeforeDrawer.focus) focusBeforeDrawer.focus();
  }
  on(btnDrawer, 'click', () => (drawerOpen ? closeDrawer() : openDrawer()));
  on($('#btnCloseDrawer'), 'click', closeDrawer);
  on(scrim, 'click', closeDrawer);
  on(drawer, 'keydown', (e) => {
    if (e.key !== 'Tab') return;
    const items = drawer.querySelectorAll('button, input, select, a[href], [tabindex]:not([tabindex="-1"])');
    const list = Array.from(items).filter((el) => !el.disabled && el.offsetParent !== null);
    if (!list.length) return;
    const first = list[0], last = list[list.length - 1];
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
  });

  /* ------------------------------------------------------------ drawer content */
  const drawerBody = $('#drawerBody');
  const jointSliders = []; // {input, out, info, arr:'arm'|'hand', index}

  function section(title, hint) {
    const s = document.createElement('section');
    s.className = 'sect';
    const h = document.createElement('h3');
    h.textContent = title;
    if (hint) {
      const span = document.createElement('span');
      span.className = 'hint';
      span.textContent = hint;
      h.appendChild(span);
    }
    s.appendChild(h);
    drawerBody.appendChild(s);
    return s;
  }
  function fmtAngle(info, v) {
    const deg = info.degrees ? v : v * 180 / Math.PI;
    return (Math.abs(deg) < 0.05 ? 0 : deg).toFixed(Math.abs(deg) < 10 ? 1 : 0) + '°';
  }
  function buildJointRows(sectEl, infos, arrKey, count) {
    infos.forEach((info, i) => {
      const row = document.createElement('div');
      row.className = 'jrow';
      const lab = document.createElement('label');
      lab.htmlFor = 'jr-' + arrKey + '-' + i;
      lab.textContent = info.label;
      lab.title = info.label;
      const input = document.createElement('input');
      input.type = 'range';
      input.className = 'slider';
      input.id = 'jr-' + arrKey + '-' + i;
      input.min = String(info.min);
      input.max = String(info.max);
      input.step = String((info.max - info.min) / 240 || 0.01);
      input.value = '0';
      const out = document.createElement('output');
      out.htmlFor = input.id;
      out.textContent = fmtAngle(info, 0);
      row.append(lab, input, out);
      sectEl.appendChild(row);
      jointSliders.push({ input, out, info, arr: arrKey, index: i });

      let dirty = false, queued = false;
      on(input, 'input', () => {
        const arr = arrKey === 'arm' ? state.armAngles : state.handAngles;
        arr[i] = parseFloat(input.value);
        out.textContent = fmtAngle(info, arr[i]);
        dirty = true;
        if (!queued) {
          queued = true;
          requestAnimationFrame(() => {
            queued = false;
            if (!dirty) return;
            dirty = false;
            sendAngles(arrKey, count);
          });
        }
      });
    });
  }
  function sendAngles(arrKey, count) {
    if (arrKey === 'arm') callApi('setArmAngles', [state.armAngles.slice(0, count)], 'Arm pose update');
    else callApi('setHandAngles', [state.handAngles.slice(0, count)], 'Hand pose update');
  }

  const sectArm = section('Arm pose', '7 axes');
  buildJointRows(sectArm, armInfo, 'arm', 7);
  const sectHand = section('Hand pose', '20 DOF');
  buildJointRows(sectHand, handInfo, 'hand', 20);

  const sectShell = section('Shell', 'section depth');
  {
    const row = document.createElement('div');
    row.className = 'jrow';
    row.style.gridTemplateColumns = '104px 1fr 50px';
    const lab = document.createElement('label');
    lab.htmlFor = 'shellDepth';
    lab.textContent = 'Shell depth';
    const input = document.createElement('input');
    input.type = 'range';
    input.className = 'slider';
    input.id = 'shellDepth';
    input.min = '0'; input.max = '1'; input.step = '0.01'; input.value = '1';
    const out = document.createElement('output');
    out.htmlFor = input.id;
    out.textContent = '100%';
    row.append(lab, input, out);
    sectShell.appendChild(row);
    let queued = false;
    on(input, 'input', () => {
      state.shellDepth = parseFloat(input.value);
      out.textContent = Math.round(state.shellDepth * 100) + '%';
      if (!queued) {
        queued = true;
        requestAnimationFrame(() => {
          queued = false;
          callApi('setShellDepth', [state.shellDepth], 'Shell update');
        });
      }
    });
    jointSliders.push({ input, out, info: null, arr: 'shell', index: 0 });
  }

  const sectCam = section('Camera');
  {
    const row = document.createElement('div');
    row.className = 'chiprow';
    VIEWS.forEach(([v, l]) => {
      const b = document.createElement('button');
      b.type = 'button';
      b.className = 'chip';
      b.dataset.group = 'view';
      b.dataset.value = v;
      b.setAttribute('aria-pressed', 'false');
      b.textContent = l;
      on(b, 'click', () => selectValue('view', v));
      row.appendChild(b);
    });
    sectCam.appendChild(row);
  }

  const sectPoses = section('Arm poses', 'animated');
  {
    const row = document.createElement('div');
    row.className = 'chiprow';
    ARM_POSES_UI.forEach(([v, l]) => {
      const b = document.createElement('button');
      b.type = 'button';
      b.className = 'chip';
      b.textContent = l;
      on(b, 'click', () => {  callApi('setPose', [v], 'Arm pose'); });
      row.appendChild(b);
    });
    sectPoses.appendChild(row);
  }

  const sectCurl = section('Hand curl', 'all fingers');
  {
    const row = document.createElement('div');
    row.className = 'jrow';
    row.style.gridTemplateColumns = '104px 1fr 50px';
    const lab = document.createElement('label');
    lab.htmlFor = 'handCurl';
    lab.textContent = 'Global curl';
    const input = document.createElement('input');
    input.type = 'range';
    input.className = 'slider';
    input.id = 'handCurl';
    input.min = '0'; input.max = '1'; input.step = '0.01'; input.value = '0';
    const out = document.createElement('output');
    out.htmlFor = input.id;
    out.textContent = '0%';
    row.append(lab, input, out);
    sectCurl.appendChild(row);
    let queued = false;
    on(input, 'input', () => {
      state.curl = parseFloat(input.value);
      out.textContent = Math.round(state.curl * 100) + '%';
      if (!queued) {
        queued = true;
        requestAnimationFrame(() => {
          queued = false;
          callApi('setHandCurl', [state.curl], 'Hand curl');
        });
      }
    });
    jointSliders.push({ input, out, info: null, arr: 'curl', index: 0 });
  }

  const sectExplode = section('Parts layout', 'exploded view');
  const explodeLocal = { active: false, scope: 'all', layout: 'exploded', amount: 0.65 };
  {
    const row = document.createElement('div');
    row.className = 'chiprow';
    const btnEnter = document.createElement('button');
    btnEnter.type = 'button';
    btnEnter.className = 'chip';
    btnEnter.id = 'btnExplodeToggle';
    btnEnter.textContent = 'Lay out parts';
    on(btnEnter, 'click', () => {
      
      if (!explodeLocal.active) {
        const ok = callApi('enterExplode', [{ scope: explodeLocal.scope, layout: explodeLocal.layout, amount: explodeLocal.amount }], 'Parts layout');
        explodeLocal.active = ok !== false;
      } else {
        callApi('exitExplode', [], 'Reassemble');
        explodeLocal.active = false;
      }
      syncExplodeUI();
    });
    row.appendChild(btnEnter);
    sectExplode.appendChild(row);

    const row2 = document.createElement('div');
    row2.className = 'jrow';
    row2.style.gridTemplateColumns = '104px 1fr';
    const lab = document.createElement('label');
    lab.textContent = 'Module';
    const sel = document.createElement('select');
    sel.id = 'explodeScope';
    sel.style.cssText = 'font:inherit;font-size:12.5px;padding:7px 10px;border-radius:10px;border:1px solid var(--line);background:rgba(255,255,255,.7)';
    const mk = (v, l) => { const o = document.createElement('option'); o.value = v; o.textContent = l; sel.appendChild(o); };
    mk('all', 'Full assembly');
    mk('hand', 'Hand (module)');
    const stats = typeof api.getExplodeStats === 'function' ? api.getExplodeStats() : null;
    if (stats && Array.isArray(stats.groups)) {
      for (const g of stats.groups) mk(g.id, g.label || g.id);
    }
    on(sel, 'change', () => {
      explodeLocal.scope = sel.value;
      if (explodeLocal.active) callApi('setExplodeProgress', [explodeLocal.amount, { scope: explodeLocal.scope, layout: explodeLocal.layout }], 'Module');
    });
    row2.append(lab, sel);
    sectExplode.appendChild(row2);

    const row3 = document.createElement('div');
    row3.className = 'jrow';
    row3.style.gridTemplateColumns = '104px 1fr 50px';
    const lab3 = document.createElement('label');
    lab3.htmlFor = 'explodeAmount';
    lab3.textContent = 'Separation';
    const amount = document.createElement('input');
    amount.type = 'range';
    amount.className = 'slider';
    amount.id = 'explodeAmount';
    amount.min = '0'; amount.max = '1'; amount.step = '0.01'; amount.value = String(explodeLocal.amount);
    const out3 = document.createElement('output');
    out3.htmlFor = amount.id;
    out3.textContent = '65%';
    row3.append(lab3, amount, out3);
    sectExplode.appendChild(row3);
    let q3 = false;
    on(amount, 'input', () => {
      explodeLocal.amount = parseFloat(amount.value);
      out3.textContent = Math.round(explodeLocal.amount * 100) + '%';
      if (!q3) {
        q3 = true;
        requestAnimationFrame(() => {
          q3 = false;
          if (explodeLocal.active) callApi('setExplodeProgress', [explodeLocal.amount, { scope: explodeLocal.scope, layout: explodeLocal.layout }], 'Separation');
        });
      }
    });

    const seg = document.createElement('div');
    seg.className = 'seg';
    seg.style.marginTop = '8px';
    [['exploded', 'Exploded'], ['flat', 'Flat layout']].forEach(([v, l]) => {
      const b = document.createElement('button');
      b.type = 'button';
      b.textContent = l;
      b.dataset.layout = v;
      b.classList.toggle('on', v === explodeLocal.layout);
      on(b, 'click', () => {
        explodeLocal.layout = v;
        seg.querySelectorAll('button').forEach(x => x.classList.toggle('on', x.dataset.layout === v));
        if (explodeLocal.active) callApi('setExplodeProgress', [explodeLocal.amount, { scope: explodeLocal.scope, layout: explodeLocal.layout }], 'Layout');
      });
      seg.appendChild(b);
    });
    sectExplode.appendChild(seg);
  }
  function syncExplodeUI() {
    const b = document.getElementById('btnExplodeToggle');
    if (b) b.textContent = explodeLocal.active ? 'Reassemble' : 'Lay out parts';
  }

  const sectExport = section('Export');
  let exportStatusEl = null;
  {
    const row = document.createElement('div');
    row.className = 'export-row';
    const bPng = document.createElement('button');
    bPng.type = 'button'; bPng.className = 'btn primary'; bPng.textContent = 'Save PNG';
    const bGlb = document.createElement('button');
    bGlb.type = 'button'; bGlb.className = 'btn secondary'; bGlb.textContent = 'Export GLB';
    row.append(bPng, bGlb);
    sectExport.appendChild(row);
    exportStatusEl = document.createElement('div');
    exportStatusEl.className = 'export-status';
    exportStatusEl.setAttribute('aria-live', 'polite');
    sectExport.appendChild(exportStatusEl);
    on(bPng, 'click', () => runExport('PNG', bPng));
    on(bGlb, 'click', () => runExport('GLB', bGlb));
  }

  const sectStats = section('Runtime');
  const statRows = {};
  {
    [['Mode', 'mode'], ['Finish', 'skin'], ['Gesture', 'gesture'], ['Time', 'time'],
     ['Meshes', 'meshCount'], ['Wires', 'wireCount']].forEach(([label, key]) => {
      const div = document.createElement('div');
      div.className = 'kv';
      const a = document.createElement('span'); a.textContent = label;
      const b = document.createElement('b'); b.textContent = '—';
      div.append(a, b);
      sectStats.appendChild(div);
      statRows[key] = b;
    });
  }

  /* ------------------------------------------------------------ export */
  let exporting = false;
  async function runExport(kind, btn) {
    if (exporting) return;
    const fn = api['export' + kind];
    if (typeof fn !== 'function') {
      toast(kind + ' export is not available yet.', true);
      return;
    }
    exporting = true;
    
    if (btn) btn.disabled = true;
    setExportStatus('Preparing ' + kind + '…', false);
    toast('Preparing ' + kind + ' export…', false, true);
    try {
      await fn.call(api);
      setExportStatus(kind + ' export complete.', false);
      toast(kind + ' exported — check your downloads.');
    } catch (err) {
      setExportStatus(kind + ' export failed: ' + errText(err), true);
      toast(kind + ' export failed: ' + errText(err), true);
    } finally {
      exporting = false;
      if (btn) btn.disabled = false;
    }
  }
  function setExportStatus(msg, isErr) {
    if (!exportStatusEl) return;
    exportStatusEl.textContent = msg;
    exportStatusEl.classList.toggle('err', !!isErr);
  }
  on($('#btnPng'), 'click', () => runExport('PNG', null));

  /* ------------------------------------------------------------ part card */
  const partcard = $('#partcard');
  function showPart(info) {
    if (!partcard || !info) return;
    $('#partRole').textContent = info.role || 'Component';
    $('#partName').textContent = info.name || 'Selected part';
    $('#partDesc').textContent = info.description || '';
    const meta = $('#partMeta');
    meta.textContent = '';
    const details = Array.isArray(info.details) ? info.details : [];
    details.forEach((d) => {
      if (!d) return;
      const div = document.createElement('div');
      div.className = 'kv';
      const a = document.createElement('span'); a.textContent = String(d.label != null ? d.label : '');
      const b = document.createElement('b'); b.textContent = String(d.value != null ? d.value : '');
      div.append(a, b);
      meta.appendChild(div);
    });
    meta.style.display = details.length ? '' : 'none';
    partcard.classList.add('show');
    partcard.inert = false;
  }
  function hidePart() {
    if (!partcard) return;
    partcard.classList.remove('show');
    partcard.inert = true;
  }
  if (partcard) partcard.inert = true;
  on($('#partClose'), 'click', hidePart);

  /* ------------------------------------------------------------ keyboard */
  on(document, 'keydown', (e) => {
    if (e.key !== 'Escape') return;
    if (drawerOpen) closeDrawer();
    else if (openPop) closePopovers();
    else if (partcard && partcard.classList.contains('show')) hidePart();
  });

  /* ------------------------------------------------------------ snapshot sync */
  function update(snapshot) {
    if (!snapshot || typeof snapshot !== 'object') return;
    const s = snapshot;
    if (typeof s.mode === 'string') state.mode = s.mode;
    if (typeof s.skin === 'string') state.skin = s.skin;
    if (typeof s.gesture === 'string') state.gesture = s.gesture;
    if (typeof s.playing === 'boolean' && s.playing !== state.playing) { state.playing = s.playing; armPoll(); }
    if (Number.isFinite(s.time) && !scrubbing) state.time = s.time;
    if (Number.isFinite(s.shellDepth)) state.shellDepth = s.shellDepth;
    if (Number.isFinite(s.curl)) state.curl = s.curl;
    if (s.story && typeof s.story === 'object') {
      const changed = !storyState || storyState.chapter !== s.story.chapter || storyState.active !== s.story.active;
      storyState = s.story;
      if (changed) renderTour();
    }
    if (Array.isArray(s.armAngles)) s.armAngles.slice(0, 7).forEach((v, i) => { if (Number.isFinite(v)) state.armAngles[i] = v; });
    if (Array.isArray(s.handAngles)) s.handAngles.slice(0, 20).forEach((v, i) => { if (Number.isFinite(v)) state.handAngles[i] = v; });
    if (s.stats && typeof s.stats === 'object') state.stats = s.stats;
    render();
  }

  let pollTimer = 0;
  function poll() {
    if (document.hidden || typeof api.snapshot !== 'function') return;
    let snap;
    try { snap = api.snapshot(); } catch (_) { return; }
    update(snap);
  }
  function armPoll() {
    clearInterval(pollTimer);
    pollTimer = setInterval(poll, state.playing ? 220 : 1200);
  }
  armPoll();
  on(document, 'visibilitychange', () => { if (!document.hidden) poll(); });

  /* ------------------------------------------------------------ render */
  function render() {
    qa('[data-group]').forEach((b) => {
      const g = b.dataset.group;
      const current = g === 'mode' ? state.mode : g === 'skin' ? state.skin
        : g === 'gesture' ? state.gesture : g === 'view' ? state.focus : null;
      const onNow = current === b.dataset.value;
      b.classList.toggle('on', onNow);
      b.setAttribute('aria-pressed', onNow ? 'true' : 'false');
    });
    playButtons.forEach((p) => {
      p.el.innerHTML = state.playing ? ICON_PAUSE : ICON_PLAY;
      p.el.setAttribute('aria-pressed', state.playing ? 'true' : 'false');
      p.el.setAttribute('aria-label', state.playing ? 'Pause motion' : 'Play motion');
      p.el.title = state.playing ? 'Pause motion' : 'Play motion';
    });
    renderTime();
    jointSliders.forEach((js) => {
      if (document.activeElement === js.input) return;
      if (js.arr === 'shell') {
        js.input.value = String(state.shellDepth);
        js.out.textContent = Math.round(state.shellDepth * 100) + '%';
        return;
      }
      if (js.arr === 'curl') {
        js.input.value = String(state.curl || 0);
        js.out.textContent = Math.round((state.curl || 0) * 100) + '%';
        return;
      }
      const arr = js.arr === 'arm' ? state.armAngles : state.handAngles;
      const v = arr[js.index];
      if (!Number.isFinite(v)) return;
      js.input.value = String(v);
      js.out.textContent = fmtAngle(js.info, v);
    });
    if (statRows.mode) {
      statRows.mode.textContent = labelFor(MODES, state.mode);
      statRows.skin.textContent = labelFor(SKINS, state.skin);
      statRows.gesture.textContent = labelFor(GESTURES, state.gesture);
      statRows.time.textContent = state.time.toFixed(2) + ' s';
      statRows.meshCount.textContent = state.stats && Number.isFinite(state.stats.meshCount) ? String(state.stats.meshCount) : '—';
      statRows.wireCount.textContent = state.stats && Number.isFinite(state.stats.wireCount) ? String(state.stats.wireCount) : '—';
    }
  }
  function renderTime() {
    timelines.forEach((t) => {
      if (state.time > parseFloat(t.max)) t.max = String(Math.ceil(state.time));
      if (!scrubbing && document.activeElement !== t) t.value = String(state.time);
    });
    tlabels.forEach((l) => { l.textContent = state.time.toFixed(1) + 's'; });
  }
  function labelFor(pairs, value) {
    const hit = pairs.find((p) => p[0] === value);
    return hit ? hit[1] : value;
  }

  render();

  /* ------------------------------------------------------------ dispose */
  function dispose() {
    clearInterval(pollTimer);
    clearTimeout(toastTimer);
    listeners.forEach(([t, type, fn, opts]) => t.removeEventListener(type, fn, opts));
    listeners.length = 0;
  }

  return { update, dispose, showPart };
}
