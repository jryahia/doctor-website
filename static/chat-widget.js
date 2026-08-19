/**
 * Doctor Website — Enhanced AI Chat Widget
 * Self-contained, zero-dependency IIFE.
 * POSTs to /api/chat with {doctor_id, message, session_id}
 * GETs /api/doctors for doctor list
 *
 * Features:
 *  - Auto-opens after 3s with greeting
 *  - 600px wide (desktop), full-width mobile
 *  - Glassmorphism dark theme with green accents
 *  - Doctor name from /api/doctors, dropdown switcher
 *  - Minimize to floating bar with unread badge
 *  - sessionStorage persistence for messages, session, doctor, state
 */
(function () {
  'use strict';

  if (document.querySelector('[data-cw-installed]')) return;

  /* ── Constants ──────────────────────────────────────────── */
  var STORAGE_KEY_MSGS  = 'cw_messages';
  var STORAGE_KEY_SID   = 'chat_session_id';
  var STORAGE_KEY_DID   = 'chat_doctor_id';
  var STORAGE_KEY_OPEN  = 'cw_is_open';
  var MAX_STORED_MSGS   = 50;
  var MINIMIZED_CLS     = 'cw-minimized';
  var OPEN_CLS          = 'cw-open';
  var ANIM_DELAY_MS     = 3000;

  /* ── Resolve the doctor the visitor picked on the page ───── */
  function resolvePageDoctorId() {
    try {
      var params = new URLSearchParams(window.location.search);
      var fromUrl = parseInt(params.get('doctor'), 10);
      if (fromUrl) return fromUrl;
    } catch (_) {}
    // The main page stores the active doctor under 'doctor_id'
    var fromPage = parseInt(sessionStorage.getItem('doctor_id'), 10);
    if (fromPage) return fromPage;
    var fromChat = parseInt(sessionStorage.getItem(STORAGE_KEY_DID), 10);
    if (fromChat) return fromChat;
    return 1;
  }

  /* ── State ───────────────────────────────────────────────── */
  var state = {
    isOpen: false,
    isLoading: false,
    doctorId: resolvePageDoctorId(),
    sessionId: sessionStorage.getItem(STORAGE_KEY_SID) || '',
    doctors: [],
    unreadCount: 0,
  };

  /* ── Helpers ─────────────────────────────────────────────── */
  function getEl(id) { return document.getElementById(id); }

  function scrollToBottom() {
    var el = getEl('cw-messages');
    if (el) { el.scrollTop = el.scrollHeight; }
  }

  function saveMessages(msgs) {
    try {
      sessionStorage.setItem(STORAGE_KEY_MSGS, JSON.stringify(msgs.slice(-MAX_STORED_MSGS)));
    } catch (_) {}
  }

  function loadMessages() {
    try {
      var raw = sessionStorage.getItem(STORAGE_KEY_MSGS);
      return raw ? JSON.parse(raw) : [];
    } catch (_) { return []; }
  }

  function saveOpenState(open) {
    try { sessionStorage.setItem(STORAGE_KEY_OPEN, open ? '1' : '0'); } catch (_) {}
  }

  function now() {
    var d = new Date();
    return String(d.getHours()).padStart(2,'0') + ':' + String(d.getMinutes()).padStart(2,'0');
  }

  function escapeHtml(str) {
    var div = document.createElement('div');
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
  }

  function currentDoctor() {
    return state.doctors.find(function (d) { return d.id === state.doctorId; }) || null;
  }

  function doctorDisplayName(doc) {
    if (!doc) return 'Assistente Medico';
    return doc.name;
  }

  /* ── Inject styles ─────────────────────────────────────── */
  var SHEET = document.createElement('style');
  SHEET.textContent = [
    '/* ── Enhanced Chat Widget ─────────────────────────────── */',
    '',
    '/* ── Bubble (minimized bar) ─────────────────────────── */',
    '#cw-bar {',
    '  position: fixed; bottom: 24px; right: 24px; z-index: 9999;',
    '  display: flex; align-items: center; gap: 10px;',
    '  background: rgba(12,18,12,0.95);',
    '  backdrop-filter: blur(24px); -webkit-backdrop-filter: blur(24px);',
    '  border: 1px solid rgba(45,125,70,0.2);',
    '  border-radius: 999px; padding: 10px 20px 10px 18px;',
    '  box-shadow: 0 8px 40px rgba(0,0,0,0.5);',
    '  cursor: pointer;',
    '  transition: transform 0.3s ease, box-shadow 0.3s ease;',
    '  user-select: none;',
    '}',
    '#cw-bar:hover { transform: scale(1.03); }',
    '#cw-bar-icon {',
    '  width: 32px; height: 32px; border-radius: 50%;',
    '  background: linear-gradient(135deg, #2d7d46 0%, #4caf50 100%);',
    '  display: flex; align-items: center; justify-content: center;',
    '  flex-shrink: 0;',
    '}',
    '#cw-bar-icon svg { width: 16px; height: 16px; fill: #fff; display: block; }',
    '#cw-bar-label {',
    '  font: 500 14px/1 Inter, system-ui, sans-serif;',
    '  color: #e0e0e0; white-space: nowrap;',
    '}',
    '#cw-bar-badge {',
    '  position: absolute; top: -6px; right: -6px;',
    '  min-width: 20px; height: 20px; border-radius: 10px;',
    '  background: #e8782a; color: #fff;',
    '  font: 700 11px/20px Inter, sans-serif; text-align: center;',
    '  padding: 0 5px; display: none;',
    '}',
    '#cw-bar-badge.cw-visible { display: block; }',
    '',
    '/* ── Panel ────────────────────────────────────────────── */',
    '#cw-panel {',
    '  position: fixed; bottom: 24px; right: 24px; z-index: 10000;',
    '  width: 600px; height: 80vh; max-height: 820px;',
    '  background: rgba(12,18,12,0.95);',
    '  backdrop-filter: blur(24px); -webkit-backdrop-filter: blur(24px);',
    '  border: 1px solid rgba(45,125,70,0.2);',
    '  border-radius: 16px;',
    '  box-shadow: 0 8px 40px rgba(0,0,0,0.5);',
    '  display: flex; flex-direction: column;',
    '  opacity: 0;',
    '  transform: translateY(16px) scale(0.96);',
    '  transition: opacity 0.3s ease, transform 0.3s ease;',
    '  pointer-events: none;',
    '  overflow: hidden;',
    '}',
    '#cw-panel.cw-open {',
    '  opacity: 1;',
    '  transform: translateY(0) scale(1);',
    '  pointer-events: auto;',
    '}',
    '',
    '/* ── Header ───────────────────────────────────────────── */',
    '#cw-header {',
    '  flex-shrink: 0;',
    '  background: rgba(12,18,12,0.98);',
    '  border-bottom: 3px solid #2d7d46;',
    '}',
    '#cw-header-top {',
    '  display: flex; align-items: center; gap: 10px;',
    '  padding: 14px 16px 8px;',
    '}',
    '#cw-avatar {',
    '  width: 40px; height: 40px; border-radius: 50%;',
    '  background: linear-gradient(135deg, #2d7d46 0%, #e8782a 100%);',
    '  display: flex; align-items: center; justify-content: center;',
    '  color: #fff; font: 700 16px/1 Inter, sans-serif; flex-shrink: 0;',
    '}',
    '#cw-header-info { flex: 1; min-width: 0; }',
    '#cw-header-name {',
    '  font: 600 14px/1.3 Inter, system-ui, sans-serif;',
    '  color: #e8e8e8;',
    '}',
    '#cw-header-status {',
    '  font: 400 11px/1.3 Inter, sans-serif;',
    '  color: #4caf50; display: flex; align-items: center; gap: 4px;',
    '  margin-top: 1px;',
    '}',
    '#cw-header-status::before {',
    '  content: ""; width: 7px; height: 7px; border-radius: 50%;',
    '  background: #4caf50; display: inline-block;',
    '  animation: cw-pulse-dot 2s ease-in-out infinite;',
    '}',
    '@keyframes cw-pulse-dot {',
    '  0%, 100% { opacity: 1; }',
    '  50% { opacity: 0.4; }',
    '}',
    '#cw-header-actions { display: flex; gap: 4px; align-items: center; }',
    '#cw-question-counter {',
    '  font: 600 11px/1 Inter, sans-serif; color: #E8803A;',
    '  padding: 3px 8px; border-radius: 10px;',
    '  background: rgba(232,128,58,0.12);',
    '  border: 1px solid rgba(232,128,58,0.2);',
    '  white-space: nowrap;',
    '}',
    '#cw-doctor-select {',
    '  background: rgba(45,125,70,0.12);',
    '  color: #c0c0c0; border: 1px solid rgba(45,125,70,0.2);',
    '  border-radius: 8px; padding: 4px 22px 4px 8px;',
    '  font: 400 11px/1.4 Inter, sans-serif;',
    '  cursor: pointer; outline: none; appearance: none;',
    '  -webkit-appearance: none;',
    '  background-image: url("data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 width=%2710%27 height=%276%27%3E%3Cpath d=%27M0 0l5 6 5-6z%27 fill=%27%23888%27/%3E%3C/svg%3E");',
    '  background-repeat: no-repeat;',
    '  background-position: right 6px center;',
    '  max-width: 110px;',
    '}',
    '#cw-doctor-select:hover { border-color: rgba(45,125,70,0.4); }',
    '#cw-doctor-select option { background: #1a2a1a; color: #e0e0e0; }',
    '.cw-hdr-btn {',
    '  width: 28px; height: 28px; border-radius: 50%; border: none;',
    '  background: rgba(255,255,255,0.06); cursor: pointer; display: flex;',
    '  align-items: center; justify-content: center; flex-shrink: 0;',
    '  transition: background 0.2s; color: #888; font-size: 16px; line-height: 1;',
    '}',
    '.cw-hdr-btn:hover { background: rgba(255,255,255,0.12); color: #ccc; }',
    '',
    '/* ── Messages area ───────────────────────────────────── */',
    '#cw-messages {',
    '  flex: 1; overflow-y: auto; padding: 12px 14px 4px;',
    '  display: flex; flex-direction: column; gap: 8px;',
    '  scroll-behavior: smooth; min-height: 0;',
    '}',
    '#cw-messages::-webkit-scrollbar { width: 4px; }',
    '#cw-messages::-webkit-scrollbar-track { background: transparent; }',
    '#cw-messages::-webkit-scrollbar-thumb { background: rgba(45,125,70,0.3); border-radius: 2px; }',
    '#cw-messages::-webkit-scrollbar-thumb:hover { background: rgba(45,125,70,0.5); }',
    '',
    '.cw-msg {',
    '  max-width: 82%; padding: 10px 14px; border-radius: 12px;',
    '  font: 400 13.5px/1.5 Inter, system-ui, sans-serif;',
    '  word-wrap: break-word; white-space: pre-wrap;',
    '  animation: cw-msgIn 0.25s ease; position: relative;',
    '}',
    '.cw-msg-user {',
    '  align-self: flex-end;',
    '  background: linear-gradient(135deg, #2d7d46 0%, #3a9d5a 100%);',
    '  color: #fff;',
    '  border-bottom-right-radius: 4px;',
    '}',
    '.cw-msg-bot {',
    '  align-self: flex-start;',
    '  background: rgba(255,255,255,0.06);',
    '  backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);',
    '  border: 1px solid rgba(255,255,255,0.07);',
    '  color: #ddd;',
    '  border-bottom-left-radius: 4px;',
    '}',
    '.cw-msg-time {',
    '  font-size: 10px; color: rgba(255,255,255,0.35);',
    '  text-align: right; margin-top: 4px;',
    '}',
    '.cw-msg-user .cw-msg-time { color: rgba(255,255,255,0.5); }',
    '.cw-msg-bot .cw-msg-time { color: rgba(255,255,255,0.3); }',
    '',
    '@keyframes cw-msgIn {',
    '  from { opacity: 0; transform: translateY(8px); }',
    '  to { opacity: 1; transform: translateY(0); }',
    '}',
    '',
    '/* ── System message ──────────────────────────────────── */',
    '.cw-msg-system {',
    '  align-self: center; text-align: center;',
    '  font: 400 11px/1.4 Inter, sans-serif; color: rgba(255,255,255,0.3);',
    '  padding: 4px 12px; max-width: 90%;',
    '}',
    '',
    '/* ── Typing indicator ─────────────────────────────────── */',
    '#cw-typing {',
    '  align-self: flex-start; display: flex; gap: 5px;',
    '  padding: 14px 18px;',
    '  background: rgba(255,255,255,0.06);',
    '  backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);',
    '  border: 1px solid rgba(255,255,255,0.07);',
    '  border-radius: 12px;',
    '  border-bottom-left-radius: 4px;',
    '  animation: cw-msgIn 0.2s ease;',
    '}',
    '#cw-typing span {',
    '  width: 7px; height: 7px; border-radius: 50%;',
    '  background: #4caf50; display: block;',
    '  animation: cw-bounce 1.4s ease-in-out infinite both;',
    '}',
    '#cw-typing span:nth-child(1) { animation-delay: 0s; }',
    '#cw-typing span:nth-child(2) { animation-delay: 0.16s; }',
    '#cw-typing span:nth-child(3) { animation-delay: 0.32s; }',
    '',
    '@keyframes cw-bounce {',
    '  0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }',
    '  40% { transform: scale(1); opacity: 1; }',
    '}',
    '',
    '/* ── Quick-reply chips ────────────────────────────────── */',
    '#cw-suggestions {',
    '  display: flex; flex-wrap: wrap; gap: 6px;',
    '  padding: 8px 14px 4px; flex-shrink: 0;',
    '}',
    '.cw-chip {',
    '  padding: 5px 14px; border-radius: 999px;',
    '  border: 1px solid rgba(45,125,70,0.25);',
    '  background: rgba(45,125,70,0.08);',
    '  font: 500 11.5px/1.4 Inter, sans-serif;',
    '  color: #4caf50; cursor: pointer;',
    '  transition: all 0.2s; white-space: nowrap;',
    '  user-select: none;',
    '}',
    '.cw-chip:hover { background: #2d7d46; color: #fff; border-color: #2d7d46; }',
    '',
    '/* ── Input area ───────────────────────────────────────── */',
    '#cw-input-area {',
    '  display: flex; align-items: flex-end; gap: 8px;',
    '  padding: 6px 14px 14px; flex-shrink: 0;',
    '  position: relative;',
    '}',
    '#cw-input-wrap { flex: 1; position: relative; }',
    '#cw-input {',
    '  width: 100%;',
    '  border: 1.5px solid rgba(255,255,255,0.08);',
    '  border-radius: 12px; padding: 9px 14px;',
    '  font: 400 13.5px/1.4 Inter, system-ui, sans-serif;',
    '  outline: none; resize: none; max-height: 90px;',
    '  background: rgba(255,255,255,0.06);',
    '  color: #ddd; transition: border-color 0.2s;',
    '}',
    '#cw-input:focus { border-color: rgba(45,125,70,0.5); }',
    '#cw-input::placeholder { color: rgba(255,255,255,0.25); }',
    '#cw-char-counter {',
    '  position: absolute; bottom: 2px; right: 8px;',
    '  font: 400 10px/1 Inter, sans-serif;',
    '  color: rgba(255,255,255,0.2); pointer-events: none;',
    '}',
    '#cw-send {',
    '  width: 40px; height: 40px; border-radius: 50%; border: none; flex-shrink: 0;',
    '  background: linear-gradient(135deg, #2d7d46 0%, #4caf50 100%);',
    '  cursor: pointer; display: flex; align-items: center; justify-content: center;',
    '  transition: transform 0.15s, box-shadow 0.15s;',
    '  box-shadow: 0 2px 8px rgba(45,125,70,0.25);',
    '}',
    '#cw-send:hover { transform: scale(1.05); box-shadow: 0 3px 12px rgba(45,125,70,0.35); }',
    '#cw-send:active { transform: scale(0.95); }',
    '#cw-send svg { width: 18px; height: 18px; fill: #fff; display: block; }',
    '#cw-send:disabled { opacity: 0.4; cursor: not-allowed; transform: none; box-shadow: none; }',
    '',
    '/* ── Responsive ───────────────────────────────────────── */',
    '@media (max-width: 640px) {',
    '  #cw-panel {',
    '    right: 0; bottom: 0; left: 0;',
    '    width: 100%; height: 80vh; max-height: 80vh;',
    '    border-radius: 16px 16px 0 0;',
    '    transform: translateY(20px) scale(0.97);',
    '  }',
    '  #cw-panel.cw-open { transform: translateY(0) scale(1); }',
    '  #cw-bar { bottom: 16px; right: 16px; }',
    '}',
  ].join('\n');
  document.head.appendChild(SHEET);

  /* ── DOM creation ───────────────────────────────────────── */
  function createBar() {
    var bar = document.createElement('div');
    bar.id = 'cw-bar';
    bar.setAttribute('data-cw-installed', '');
    bar.innerHTML =
      '<div id="cw-bar-icon">' +
        '<svg viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H5.17L4 17.17V4h16v12z"/></svg>' +
      '</div>' +
      '<span id="cw-bar-label">Chat con Assistente</span>' +
      '<span id="cw-bar-badge">0</span>';
    bar.addEventListener('click', function () {
      openPanel();
    });
    return bar;
  }

  function createPanel() {
    var p = document.createElement('div');
    p.id = 'cw-panel';

    /* ── Header ── */
    var hdr = document.createElement('div');
    hdr.id = 'cw-header';
    var hdrTop = document.createElement('div');
    hdrTop.id = 'cw-header-top';
    hdrTop.innerHTML = [
      '<div id="cw-avatar"><svg xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M11 2v2" /> <path d="M5 2v2" /> <path d="M5 3H4a2 2 0 0 0-2 2v4a6 6 0 0 0 12 0V5a2 2 0 0 0-2-2h-1" /> <path d="M8 15a6 6 0 0 0 12 0v-3" /> <circle cx="20" cy="10" r="2" /></svg></div>',
      '<div id="cw-header-info">',
      '  <div id="cw-header-name">Caricamento...</div>',
      '  <div id="cw-header-status">Online</div>',
      '</div>',
      '<div id="cw-question-counter" title="Domande rimanenti">6/6</div>',
      '<div id="cw-header-actions">',
      '  <select id="cw-doctor-select"></select>',
      '  <button class="cw-hdr-btn" id="cw-minimize-btn" aria-label="Minimizza">&#8212;</button>',
      '  <button class="cw-hdr-btn" id="cw-close-btn" aria-label="Chiudi">&times;</button>',
      '</div>',
    ].join('');
    hdr.appendChild(hdrTop);
    p.appendChild(hdr);

    /* ── Messages ── */
    var msgs = document.createElement('div');
    msgs.id = 'cw-messages';
    p.appendChild(msgs);

    /* ── Suggestions ── */
    var suggs = document.createElement('div');
    suggs.id = 'cw-suggestions';
    ['Orari?', 'Indirizzo?', 'Prenotazione?', 'Servizi?', 'Costi?'].forEach(function (text) {
      var chip = document.createElement('span');
      chip.className = 'cw-chip';
      chip.textContent = text;
      chip.addEventListener('click', function () { sendMessage(text); });
      suggs.appendChild(chip);
    });
    p.appendChild(suggs);

    /* ── Input area ── */
    var inpArea = document.createElement('div');
    inpArea.id = 'cw-input-area';
    inpArea.innerHTML = [
      '<div id="cw-input-wrap">',
      '  <textarea id="cw-input" rows="1" placeholder="Scrivi un messaggio..." maxlength="500"></textarea>',
      '  <span id="cw-char-counter">0/500</span>',
      '</div>',
      '<button id="cw-send" aria-label="Invia">',
      '  <svg viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>',
      '</button>',
    ].join('');
    p.appendChild(inpArea);

    /* ── Events ── */
    var minimizeBtn = hdrTop.querySelector('#cw-minimize-btn');
    var closeBtn = hdrTop.querySelector('#cw-close-btn');
    var doctorSelect = hdrTop.querySelector('#cw-doctor-select');
    var input = inpArea.querySelector('#cw-input');
    var sendBtn = inpArea.querySelector('#cw-send');
    var charCounter = inpArea.querySelector('#cw-char-counter');

    minimizeBtn.addEventListener('click', function (e) {
      e.stopPropagation();
      minimizePanel();
    });
    closeBtn.addEventListener('click', function (e) {
      e.stopPropagation();
      closePanel();
    });
    sendBtn.addEventListener('click', function () { sendMessage(input.value); });
    input.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage(input.value);
      }
    });
    input.addEventListener('input', function () {
      autoResizeInput(input);
      charCounter.textContent = input.value.length + '/500';
    });
    doctorSelect.addEventListener('change', function () {
      var newId = parseInt(doctorSelect.value, 10);
      if (newId !== state.doctorId) {
        switchDoctor(newId);
      }
    });

    return p;
  }

  /* ── Inject DOM ─────────────────────────────────────────── */
  var bar = createBar();
  var panel = createPanel();
  document.body.appendChild(panel);
  document.body.appendChild(bar);

  /* ── Panel controls ─────────────────────────────────────── */
  function openPanel() {
    if (state.isOpen) return;
    state.isOpen = true;
    state.unreadCount = 0;
    updateBadge();
    panel.classList.add(OPEN_CLS);
    bar.style.display = 'none';
    saveOpenState(true);
    focusInput();
  }

  function closePanel() {
    if (!state.isOpen) return;
    state.isOpen = false;
    panel.classList.remove(OPEN_CLS);
    bar.style.display = '';
    saveOpenState(false);
  }

  function minimizePanel() {
    state.isOpen = false;
    panel.classList.remove(OPEN_CLS);
    bar.style.display = '';
    saveOpenState(false);
    updateBarLabel();
  }

  function togglePanel() {
    if (state.isOpen) { minimizePanel(); } else { openPanel(); }
  }

  function focusInput() {
    var inp = getEl('cw-input');
    if (inp) setTimeout(function () { inp.focus(); }, 350);
  }

  function autoResizeInput(el) {
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 90) + 'px';
  }

  function updateBadge() {
    var badge = getEl('cw-bar-badge');
    if (!badge) return;
    if (state.unreadCount > 0) {
      badge.textContent = state.unreadCount > 99 ? '99+' : String(state.unreadCount);
      badge.classList.add('cw-visible');
    } else {
      badge.classList.remove('cw-visible');
    }
  }

  function updateBarLabel() {
    var lbl = getEl('cw-bar-label');
    var doc = currentDoctor();
    if (lbl) {
      lbl.textContent = 'Chat con ' + (doc ? doc.name.split(',')[0].trim() : 'Assistente');
    }
  }

  /* ── Doctor management ──────────────────────────────────── */
  function loadDoctors() {
    var xhr = new XMLHttpRequest();
    xhr.open('GET', '/api/doctors', true);
    xhr.onload = function () {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          var data = JSON.parse(xhr.responseText);
          state.doctors = data.doctors || [];
        } catch (_) { state.doctors = []; }
      }
      populateDoctorSelect();
      applyDoctor();
    };
    xhr.onerror = function () {
      // Fallback: use hardcoded common names
      state.doctors = [
        { id: 1, name: 'Dr. Mario Rossi', title: 'Medico Chirurgo' },
        { id: 2, name: 'Dr.ssa Laura Bianchi', title: 'Dermatologa' },
        { id: 3, name: 'Dr. Giovanni Verdi', title: 'Ortopedico' },
      ];
      populateDoctorSelect();
      applyDoctor();
    };
    xhr.send();
  }

  function populateDoctorSelect() {
    var sel = getEl('cw-doctor-select');
    if (!sel) return;
    sel.innerHTML = '';
    state.doctors.forEach(function (doc) {
      var opt = document.createElement('option');
      opt.value = String(doc.id);
      opt.textContent = doc.name.split(',')[0].trim();
      sel.appendChild(opt);
    });
    sel.value = String(state.doctorId);
  }

  function applyDoctor() {
    var doc = currentDoctor();
    var nameEl = getEl('cw-header-name');
    if (nameEl) {
      nameEl.textContent = doc ? doc.name : 'Assistente Medico';
    }
    updateBarLabel();
    // If no messages yet, add welcome
    var msgsEl = getEl('cw-messages');
    if (msgsEl && msgsEl.children.length === 0) {
      addWelcomeMessage(doc);
    }
  }

  function switchDoctor(newId) {
    state.doctorId = newId;
    sessionStorage.setItem(STORAGE_KEY_DID, String(newId));
    applyDoctor();
    var doc = currentDoctor();
    var name = doc ? doc.name : 'Medico';
    addSystemMessage('Sei ora in contatto con ' + name);
    // Update select
    var sel = getEl('cw-doctor-select');
    if (sel) sel.value = String(newId);
  }

  /* ── Messages ───────────────────────────────────────────── */
  function addMessage(text, role, ts) {
    var msgs = getEl('cw-messages');
    if (!msgs) return;
    var div = document.createElement('div');
    div.className = 'cw-msg ' + (role === 'user' ? 'cw-msg-user' : 'cw-msg-bot');
    div.textContent = text;
    var timeEl = document.createElement('div');
    timeEl.className = 'cw-msg-time';
    timeEl.textContent = ts || now();
    div.appendChild(timeEl);
    msgs.appendChild(div);
    scrollToBottom();
    return div;
  }

  function addSystemMessage(text) {
    var msgs = getEl('cw-messages');
    if (!msgs) return;
    var div = document.createElement('div');
    div.className = 'cw-msg-system';
    div.textContent = text;
    msgs.appendChild(div);
    scrollToBottom();
  }

  function addWelcomeMessage(doc) {
    var name = doc ? doc.name : 'Assistente Medico';
    var firstName = name.split(',')[0].trim();
    var welcome = 'Ciao! Sono ' + firstName + '. Come posso aiutarti oggi? Puoi chiedermi informazioni su orari, indirizzo, prenotazioni, servizi o costi.';
    addMessage(welcome, 'bot');
  }

  function showTyping() {
    var msgs = getEl('cw-messages');
    if (!msgs) return;
    var div = document.createElement('div');
    div.id = 'cw-typing';
    div.innerHTML = '<span></span><span></span><span></span>';
    msgs.appendChild(div);
    scrollToBottom();
  }

  function hideTyping() {
    var el = getEl('cw-typing');
    if (el) el.remove();
  }

  function persistMessages() {
    var msgsEl = getEl('cw-messages');
    if (!msgsEl) return;
    var items = [];
    var children = msgsEl.children;
    for (var i = 0; i < children.length; i++) {
      var c = children[i];
      if (c.classList.contains('cw-msg')) {
        items.push({
          text: c.childNodes[0] ? c.childNodes[0].textContent : c.textContent,
          role: c.classList.contains('cw-msg-user') ? 'user' : 'bot',
          time: c.querySelector('.cw-msg-time') ? c.querySelector('.cw-msg-time').textContent : '',
        });
      } else if (c.classList.contains('cw-msg-system')) {
        items.push({
          text: c.textContent,
          role: 'system',
          time: '',
        });
      }
    }
    saveMessages(items);
  }

  function restoreMessages() {
    var msgs = loadMessages();
    if (msgs.length === 0) return;
    var msgsEl = getEl('cw-messages');
    if (!msgsEl) return;
    msgs.forEach(function (item) {
      if (item.role === 'system') {
        addSystemMessage(item.text);
      } else {
        addMessage(item.text, item.role, item.time);
      }
    });
  }

  /* ── Question counter ──────────────────────────────────── */
  function updateQuestionCounter(remaining) {
    var el = document.getElementById('cw-question-counter');
    if (!el) return;
    if (remaining === undefined || remaining === null) return;
    el.textContent = remaining + '/6';
    if (remaining <= 1) {
      el.style.color = '#ef4444';
      el.style.background = 'rgba(239,68,68,0.12)';
      el.style.borderColor = 'rgba(239,68,68,0.2)';
    } else {
      el.style.color = '#E8803A';
      el.style.background = 'rgba(232,128,58,0.12)';
      el.style.borderColor = 'rgba(232,128,58,0.2)';
    }
  }

  /* ── Chat API ───────────────────────────────────────────── */
  function sendMessage(text) {
    text = (text || '').trim();
    if (!text || state.isLoading) return;

    addMessage(text, 'user');
    persistMessages();

    var input = getEl('cw-input');
    if (input) {
      input.value = '';
      input.style.height = 'auto';
      var cc = getEl('cw-char-counter');
      if (cc) cc.textContent = '0/500';
    }

    state.isLoading = true;
    var sendBtn = getEl('cw-send');
    if (sendBtn) sendBtn.disabled = true;

    showTyping();

    var payload = JSON.stringify({
      doctor_id: state.doctorId,
      message: text,
      session_id: state.sessionId || undefined,
    });

    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/api/chat', true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.onload = function () {
      hideTyping();
      state.isLoading = false;
      var sBtn = getEl('cw-send');
      if (sBtn) sBtn.disabled = false;

      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          var data = JSON.parse(xhr.responseText);
          if (data.answer) {
            addMessage(data.answer, 'bot');
            // Update remaining questions counter
            updateQuestionCounter(data.remaining_questions);
          }
          if (data.session_id) {
            state.sessionId = data.session_id;
            sessionStorage.setItem(STORAGE_KEY_SID, state.sessionId);
          }
        } catch (e) {
          addMessage('Mi dispiace, si è verificato un errore. Riprova più tardi.', 'bot');
        }
      } else {
        addMessage('Mi dispiace, si è verificato un errore. Riprova più tardi.', 'bot');
      }
      persistMessages();
    };
    xhr.onerror = function () {
      hideTyping();
      state.isLoading = false;
      var sBtn = getEl('cw-send');
      if (sBtn) sBtn.disabled = false;
      addMessage('Mi dispiace, si è verificato un errore. Riprova più tardi.', 'bot');
      persistMessages();
    };
    xhr.send(payload);
  }

  /* ── Init ───────────────────────────────────────────────── */
  function init() {
    // Restore open state
    var wasOpen = sessionStorage.getItem(STORAGE_KEY_OPEN) === '1';

    // Restore messages first if any
    var savedMsgs = loadMessages();
    if (savedMsgs.length > 0) {
      restoreMessages();
    }

    // Load doctors and setup
    loadDoctors();

    // If no saved messages and was open, add welcome after loading doctors
    // (doctors callback handles welcome if messages area empty)

    // If was open, show panel; otherwise show bar
    if (wasOpen) {
      openPanel();
    } else {
      bar.style.display = '';
    }

    // Auto-open after 3 seconds with greeting
    setTimeout(function () {
      // Only auto-open if there are no or few messages (first visit)
      var msgs = getEl('cw-messages');
      var msgCount = msgs ? msgs.children.length : 0;
      if (!state.isOpen && msgCount <= 1) {
        openPanel();
      }
    }, ANIM_DELAY_MS);
  }

  /* ── Start ──────────────────────────────────────────────── */
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
