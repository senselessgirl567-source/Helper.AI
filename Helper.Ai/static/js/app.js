/* ── Helper.ai — app.js ── */

const socket = io();
let currentUser = null;
let currentRoom = null;
let currentDocId = null;
let selectedTool = 'ppt';
let recognition = null;
let micActive = false;

// ── Init ─────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
  const res = await fetch('/api/me');
  if (!res.ok) { window.location.href = '/login'; return; }
  currentUser = await res.json();
  const initials = currentUser.name.split(' ').map(n=>n[0]).join('').toUpperCase().slice(0,2);
  document.getElementById('user-avatar').textContent = initials;
  document.getElementById('user-name-display').textContent = currentUser.name;
  document.getElementById('user-email-display').textContent = currentUser.email;
  loadDocuments();
});

// ── View switching ─────────────────────────────────────────────────
function switchView(view, el) {
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.getElementById('view-' + view).classList.add('active');
  el.classList.add('active');
  const titles = { dashboard:'Dashboard', ppt:'Auto PPT Maker', report:'Report Generator', notes:'Smart Notes', collab:'Live Collaboration', vault:'My Vault', files:'Cloud Files' };
  document.getElementById('page-title').textContent = titles[view] || view;
  if (view === 'files') loadDocuments('all');
  if (view === 'vault') loadDocuments('vault');
  if (window.innerWidth <= 640) document.getElementById('sidebar').classList.remove('open');
}

function toggleSidebar() {
  document.getElementById('sidebar').classList.toggle('open');
}

function handleNewBtn() {
  switchView('ppt', document.querySelector('[data-view="ppt"]'));
}

// ── Tool selector ──────────────────────────────────────────────────
function selectTool(el) {
  document.querySelectorAll('.tool-card').forEach(c => c.classList.remove('selected'));
  el.classList.add('selected');
  selectedTool = el.dataset.tool;
}

// ── Generate (dashboard) ───────────────────────────────────────────
async function generateContent() {
  const topic = document.getElementById('prompt-input').value.trim();
  const isPrivate = document.getElementById('make-private').checked;
  const status = document.getElementById('gen-status');
  if (!topic) { showStatus(status, 'Please enter a topic.', 'error'); return; }
  showStatus(status, `Generating ${selectedTool === 'ppt' ? 'presentation' : selectedTool === 'report' ? 'report' : 'notes'}…`, 'loading');
  try {
    const endpoint = `/api/generate/${selectedTool}`;
    const body = selectedTool === 'notes' ? { text: topic, private: isPrivate } : { topic, private: isPrivate };
    const res = await fetch(endpoint, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body) });
    const data = await res.json();
    if (data.error) { showStatus(status, data.error, 'error'); return; }
    showStatus(status, 'Generated successfully!', 'success');
    currentDocId = data.doc_id;
    openResultModal(selectedTool, data.data);
    loadDocuments();
  } catch(e) { showStatus(status, 'Network error. Try again.', 'error'); }
}

// ── PPT page ───────────────────────────────────────────────────────
async function generatePPT() {
  const topic = document.getElementById('ppt-topic').value.trim();
  const isPrivate = document.getElementById('ppt-private').checked;
  const status = document.getElementById('ppt-status');
  const result = document.getElementById('ppt-result');
  if (!topic) { showStatus(status, 'Please enter a topic.', 'error'); return; }
  showStatus(status, 'Generating your presentation…', 'loading');
  result.innerHTML = '';
  try {
    const res = await fetch('/api/generate/ppt', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ topic, private: isPrivate }) });
    const data = await res.json();
    if (data.error) { showStatus(status, data.error, 'error'); return; }
    showStatus(status, `✓ ${data.data.slides?.length || 0} slides created!`, 'success');
    currentDocId = data.doc_id;
    result.innerHTML = renderPPT(data.data);
  } catch(e) { showStatus(status, 'Network error.', 'error'); }
}

// ── Report page ───────────────────────────────────────────────────────
async function generateReport() {
  const topic = document.getElementById('report-topic').value.trim();
  const isPrivate = document.getElementById('report-private').checked;
  const status = document.getElementById('report-status');
  const result = document.getElementById('report-result');
  if (!topic) { showStatus(status, 'Please enter a topic.', 'error'); return; }
  showStatus(status, 'Generating structured report…', 'loading');
  result.innerHTML = '';
  try {
    const res = await fetch('/api/generate/report', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ topic, private: isPrivate }) });
    const data = await res.json();
    if (data.error) { showStatus(status, data.error, 'error'); return; }
    showStatus(status, '✓ Report ready!', 'success');
    currentDocId = data.doc_id;
    result.innerHTML = renderReport(data.data);
  } catch(e) { showStatus(status, 'Network error.', 'error'); }
}

// ── Notes page ─────────────────────────────────────────────────────
async function generateNotes() {
  const text = document.getElementById('notes-input').value.trim();
  const isPrivate = document.getElementById('notes-private').checked;
  const status = document.getElementById('notes-status');
  const result = document.getElementById('notes-result');
  if (!text) { showStatus(status, 'Please enter some text.', 'error'); return; }
  showStatus(status, 'Creating smart notes…', 'loading');
  result.innerHTML = '';
  try {
    const res = await fetch('/api/generate/notes', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ text, private: isPrivate }) });
    const data = await res.json();
    if (data.error) { showStatus(status, data.error, 'error'); return; }
    showStatus(status, '✓ Notes ready!', 'success');
    currentDocId = data.doc_id;
    result.innerHTML = renderNotes(data.data);
  } catch(e) { showStatus(status, 'Network error.', 'error'); }
}

// ── Renderers ──────────────────────────────────────────────────────
function renderPPT(data) {
  const slides = data.slides || [];
  return `<div class="result-section">
    <p style="font-size:12px;color:var(--text-hint);margin-bottom:12px;">${slides.length} slides · "${data.title || ''}"</p>
    ${slides.map(s => `
    <div class="slide-card">
      <div class="slide-num">Slide ${s.slide_number} · ${s.type}</div>
      <div class="slide-heading">${esc(s.heading)}</div>
      ${s.body ? `<div class="slide-body">${esc(s.body)}</div>` : ''}
      ${s.bullet_points?.length ? `<ul class="slide-bullets">${s.bullet_points.map(b=>`<li>${esc(b)}</li>`).join('')}</ul>` : ''}
      ${s.speaker_notes ? `<div class="slide-notes">🎤 ${esc(s.speaker_notes)}</div>` : ''}
    </div>`).join('')}
  </div>`;
}

function renderReport(data) {
  return `<div class="result-section">
    <h2 style="font-size:18px;font-weight:700;margin-bottom:6px;">${esc(data.title || '')}</h2>
    ${data.abstract ? `<p style="font-size:13px;color:var(--text-sec);margin-bottom:14px;line-height:1.6;font-style:italic;">${esc(data.abstract)}</p>` : ''}
    ${data.keywords?.length ? `<p style="font-size:11px;color:var(--text-hint);margin-bottom:16px;">Keywords: ${data.keywords.join(', ')}</p>` : ''}
    ${(data.sections||[]).map(s => `
    <div class="report-section">
      <div class="report-heading">${esc(s.heading)}</div>
      <div class="report-content">${esc(s.content)}</div>
    </div>`).join('')}
  </div>`;
}

function renderNotes(data) {
  return `<div class="result-section">
    <h2 style="font-size:17px;font-weight:700;margin-bottom:8px;">${esc(data.title||'')}</h2>
    ${data.summary ? `<p style="font-size:13px;color:var(--text-sec);margin-bottom:14px;line-height:1.6;">${esc(data.summary)}</p>` : ''}
    ${data.key_points?.length ? `
    <div class="panel-label" style="margin-bottom:6px;">Key points</div>
    <ul class="notes-key-points">${data.key_points.map(k=>`<li>${esc(k)}</li>`).join('')}</ul>` : ''}
    ${(data.sections||[]).map(s => `
    <div class="report-section">
      <div class="report-heading">${esc(s.heading)}</div>
      <div class="report-content">${esc(s.content)}</div>
      ${s.important_terms?.length ? `<div style="margin-top:8px;">${s.important_terms.map(t=>`<span style="font-size:11px;background:var(--purple-light);color:var(--purple);padding:2px 8px;border-radius:20px;margin:2px;display:inline-block;"><b>${esc(t.term)}</b>: ${esc(t.definition)}</span>`).join('')}</div>` : ''}
    </div>`).join('')}
    ${data.flashcards?.length ? `
    <div class="panel-label" style="margin:14px 0 8px;">Flashcards</div>
    ${data.flashcards.map(f=>`<div class="flashcard"><div class="flashcard-q">Q: ${esc(f.question)}</div><div class="flashcard-a">A: ${esc(f.answer)}</div></div>`).join('')}` : ''}
    ${data.exam_tips?.length ? `
    <div class="panel-label" style="margin:14px 0 6px;">Exam tips</div>
    <ul class="notes-key-points">${data.exam_tips.map(t=>`<li>${esc(t)}</li>`).join('')}</ul>` : ''}
  </div>`;
}

// ── Modal ──────────────────────────────────────────────────────────
function openResultModal(type, data) {
  const modal = document.getElementById('result-modal');
  document.getElementById('modal-title').textContent = type === 'ppt' ? 'Presentation' : type === 'report' ? 'Report' : 'Smart Notes';
  const body = document.getElementById('modal-body');
  if (type === 'ppt') body.innerHTML = renderPPT(data);
  else if (type === 'report') body.innerHTML = renderReport(data);
  else body.innerHTML = renderNotes(data);
  modal.classList.remove('hidden');
}

function closeModal() { document.getElementById('result-modal').classList.add('hidden'); }

// ── Load documents ─────────────────────────────────────────────────
async function loadDocuments(mode) {
  const res = await fetch('/api/documents');
  if (!res.ok) return;
  const docs = await res.json();

  const recentEl = document.getElementById('recent-docs');
  const allEl = document.getElementById('all-docs');
  const vaultEl = document.getElementById('vault-docs');

  const colors = { ppt:['#FAECE7','#993C1D','PPT'], report:['#E6F1FB','#185FA5','REP'], notes:['#E1F5EE','#0F6E56','NOTE'] };

  const renderItem = d => {
    const [bg,fg,label] = colors[d.doc_type] || ['#F1EFE8','#5F5E5A','DOC'];
    return `<div class="doc-item" onclick="openDoc(${d.id})">
      <div class="doc-badge" style="background:${bg};color:${fg};">${label}</div>
      <div>
        <div class="doc-name">${esc(d.title)}</div>
        <div class="doc-meta">${d.created_at}</div>
      </div>
      ${d.is_private ? '<div class="doc-lock">🔒</div>' : ''}
    </div>`;
  };

  const recent = docs.slice(0,5);
  if (recentEl) recentEl.innerHTML = recent.length ? recent.map(renderItem).join('') : '<div class="empty-state">No documents yet.</div>';
  if (allEl) allEl.innerHTML = docs.length ? docs.map(renderItem).join('') : '<div class="empty-state">No documents yet.</div>';
  if (vaultEl) {
    const private_ = docs.filter(d => d.is_private);
    vaultEl.innerHTML = private_.length ? private_.map(renderItem).join('') : '<div class="empty-state">No private documents.</div>';
  }
}

async function openDoc(id) {
  const res = await fetch(`/api/documents/${id}`);
  if (!res.ok) return;
  const doc = await res.json();
  currentDocId = doc.id;
  openResultModal(doc.doc_type, doc.content);
}

// ── Share ──────────────────────────────────────────────────────────
async function shareCurrentDoc() {
  if (!currentDocId) return alert('Generate a document first.');
  const res = await fetch(`/api/documents/${currentDocId}/share`, { method:'POST' });
  const data = await res.json();
  const url = window.location.origin + data.share_url;
  const box = document.getElementById('share-url-box');
  const inp = document.getElementById('share-url-display');
  if (box && inp) { box.classList.remove('hidden'); inp.value = url; }
  else { prompt('Share this link:', url); }
}

function copyShareUrl() {
  const inp = document.getElementById('share-url-display');
  navigator.clipboard.writeText(inp.value).then(() => alert('Copied!'));
}

// ── Real-time Collaboration ───────────────────────────────────────
function joinRoom() {
  const roomId = document.getElementById('room-id-input').value.trim();
  if (!roomId) return;
  socket.emit('join_room', { room: roomId });
  currentRoom = roomId;
  const status = document.getElementById('room-status');
  status.style.display = 'block';
  status.textContent = `Joined room: ${roomId}`;
  status.style.background = '#EAF3DE'; status.style.color = '#3B6D11';
  document.getElementById('collab-live-badge').style.display = 'inline';
}

function broadcastNote() {
  if (!currentRoom) return;
  const content = document.getElementById('collab-editor').value;
  socket.emit('note_update', { room: currentRoom, content });
}

socket.on('note_changed', data => {
  const editor = document.getElementById('collab-editor');
  if (editor) editor.value = data.content;
});

socket.on('user_joined', data => {
  addMember(data.user);
});

socket.on('user_left', data => {
  const membersEl = document.getElementById('members-list');
  const collabEl = document.getElementById('collab-users');
  [membersEl, collabEl].forEach(el => {
    if (el) el.querySelectorAll('[data-user]').forEach(m => { if (m.dataset.user === data.user) m.remove(); });
  });
});

function addMember(name) {
  const html = `<div class="member-item" data-user="${esc(name)}"><div class="online-dot"></div>${esc(name)}</div>`;
  const membersEl = document.getElementById('members-list');
  const collabEl = document.getElementById('collab-users');
  if (membersEl) { if (membersEl.querySelector('.empty-state')) membersEl.innerHTML = ''; membersEl.insertAdjacentHTML('beforeend', html); }
  if (collabEl) { if (collabEl.querySelector('.empty-state')) collabEl.innerHTML = ''; collabEl.insertAdjacentHTML('beforeend', html); }
}

// ── Voice / Speech Recognition ─────────────────────────────────────
function initSpeech(targetId, btnId) {
  if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
    alert('Speech recognition not supported in this browser. Try Chrome.');
    return null;
  }
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  const r = new SR();
  r.continuous = true;
  r.interimResults = true;
  r.lang = 'en-US';
  r.onresult = e => {
    let transcript = '';
    for (let i = e.resultIndex; i < e.results.length; i++) transcript += e.results[i][0].transcript;
    const el = document.getElementById(targetId);
    if (el) el.value = transcript;
  };
  r.onerror = () => stopMic(btnId);
  return r;
}

function toggleMic() {
  const btn = document.getElementById('mic-btn');
  if (!micActive) {
    recognition = initSpeech('prompt-input', 'mic-btn');
    if (!recognition) return;
    recognition.start();
    micActive = true;
    btn.classList.add('active');
    btn.title = 'Stop listening';
  } else {
    stopMic('mic-btn');
  }
}

function toggleMicNotes() {
  if (!micActive) {
    recognition = initSpeech('notes-input', null);
    if (!recognition) return;
    recognition.start();
    micActive = true;
  } else {
    if (recognition) recognition.stop();
    micActive = false;
  }
}

function stopMic(btnId) {
  if (recognition) { recognition.stop(); recognition = null; }
  micActive = false;
  if (btnId) { const btn = document.getElementById(btnId); if (btn) { btn.classList.remove('active'); btn.title = 'Voice input'; } }
}

// ── Logout ───────────────────────────────────────────────────────
async function logout() {
  await fetch('/api/logout', { method: 'POST' });
  window.location.href = '/login';
}

// ── Helpers ──────────────────────────────────────────────────────
function esc(str) {
  if (!str) return '';
  return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function showStatus(el, msg, type) {
  el.textContent = msg;
  el.className = `gen-status ${type}`;
  el.style.display = 'block';
}
