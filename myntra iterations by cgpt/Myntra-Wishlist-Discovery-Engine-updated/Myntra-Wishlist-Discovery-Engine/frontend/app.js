/**
 * Phase 10 — Dashboard App Logic
 * Handles: data loading, rendering, navigation, theme, chat, filters
 */

const state = {
  isDemo: true, // always start demo-first; upgrade to live if API responds
  apiUrl: window.__APP_CONFIG__?.API_BASE_URL || window.location.origin,
  data: { overview: null, behaviours: null, questions: null, segments: null, opportunities: null, evidence: [] },
  activeIntentFilter: '',
  activeSourceFilter: '',
  chatOpen: false,
  chatHistory: [],
  theme: localStorage.getItem('theme') || 'dark'
};

// ── Bootstrap ─────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
  applyTheme(state.theme);
  setupNavigation();
  setupDrawer();
  setupThemeToggle();
  setupChat();
  setupFilters();
  setupPipelineControls();
  setupSummaryButton();

  // Try live API first, fall back to demo data.
  // The API health route is intentionally namespaced under /api.
  try {
    const probe = await fetch(`${state.apiUrl}/api/health`, { signal: AbortSignal.timeout(2500) });
    if (probe.ok) {
      await fetchAllData();
      state.isDemo = false;
      document.getElementById('demo-banner').classList.add('hidden');
      document.getElementById('status-label').textContent = 'Live';
    } else throw new Error('unhealthy');
  } catch {
    enableDemoMode();
  }

  renderAll();
  feather.replace();
});

function enableDemoMode() {
  state.isDemo = true;
  document.getElementById('demo-banner').classList.remove('hidden');
  document.getElementById('status-label').textContent = 'Demo';
  state.data = {
    overview: DEMO_DATA.overview,
    behaviours: DEMO_DATA.behaviours,
    questions: DEMO_DATA.questions,
    segments: DEMO_DATA.segments,
    opportunities: DEMO_DATA.opportunities,
    evidence: DEMO_DATA.evidence
  };
}

// ── API ───────────────────────────────────────────────────
async function apiGet(path) {
  const res = await fetch(`${state.apiUrl}${path}`);
  if (!res.ok) throw new Error(`${res.status}`);
  return res.json();
}

async function fetchAllData() {
  const [ov, beh, qs, segs, opps, ev] = await Promise.all([
    apiGet('/api/dashboard/overview'),
    apiGet('/api/dashboard/behaviours'),
    apiGet('/api/dashboard/questions'),
    apiGet('/api/segments'),
    apiGet('/api/segments/opportunities'),
    apiGet('/api/evidence?limit=30')
  ]);
  state.data.overview = ov;
  state.data.behaviours = beh;
  state.data.questions = qs;
  state.data.segments = segs.segments;
  state.data.opportunities = opps.opportunities;
  state.data.evidence = ev.items;
}

// ── Render All ────────────────────────────────────────────
function renderAll() {
  renderOverview();
  renderQuestions();
  renderBehaviours();
  renderSegments();
  renderOpportunities();
  renderEvidence();
  feather.replace();
}

function esc(str) {
  if (!str) return '';
  return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// ── OVERVIEW ──────────────────────────────────────────────
function renderOverview() {
  const d = state.data.overview;
  if (!d) return;

  document.getElementById('val-total').textContent = (d.total_annotations || 0).toLocaleString();

  const blocked = d.intent_x_friction?.high_intent_with_friction;
  if (blocked) document.getElementById('val-blocked').textContent = blocked.percent + '%';

  // Top friction
  const frictions = state.data.behaviours?.friction_distribution;
  if (frictions) {
    const top = Object.entries(frictions).sort((a,b) => b[1].of_all_annotations.percent - a[1].of_all_annotations.percent)[0];
    if (top) {
      document.getElementById('val-topfriction').textContent = top[0].replace(/_/g,' ');
      document.getElementById('val-topfriction-count').textContent = `${top[1].count} mentions · ${top[1].of_all_annotations.percent}%`;
    }
  }

  // Funnel
  const total = d.total_annotations || 0;
  const hiPct  = d.intent_x_friction?.high_intent_total?.percent || 0;
  const blkPct = d.intent_x_friction?.high_intent_with_friction?.percent || 0;
  const hiCount = d.intent_x_friction?.high_intent_total?.count || 0;
  const blkCount = d.intent_x_friction?.high_intent_with_friction?.count || 0;

  document.getElementById('funnel-container').innerHTML = `
    <div class="funnel">
      <div class="funnel-step" style="--w:100%">
        <span>Total Annotated Evidence</span>
        <strong>100% &nbsp;(${total.toLocaleString()} items)</strong>
      </div>
      <div class="funnel-step" style="--w:${hiPct}%">
        <span>High Purchase Intent</span>
        <strong>${hiPct}% &nbsp;(${hiCount.toLocaleString()} users)</strong>
      </div>
      <div class="funnel-step blocked" style="--w:${(hiPct * blkPct / 100).toFixed(1)}%">
        <span>Blocked by Friction</span>
        <strong>${blkPct}% of high-intent &nbsp;(${blkCount.toLocaleString()} users)</strong>
      </div>
    </div>`;

  // Source distribution
  const src = d.source_distribution;
  if (src) {
    const rows = Object.entries(src).sort((a,b) => b[1].count - a[1].count).map(([k,v]) => `
      <div class="bar-row">
        <div class="bar-header">
          <span class="bar-label">${k.replace(/_/g,' ')}</span>
          <span class="bar-value">${v.percent}% &nbsp;(${v.count.toLocaleString()})</span>
        </div>
        <div class="bar-track"><div class="bar-fill" style="width:${v.percent}%"></div></div>
      </div>`).join('');
    document.getElementById('source-chart').innerHTML = `<div class="bar-chart">${rows}</div>`;
  }
}

// ── QUESTIONS ─────────────────────────────────────────────
function renderQuestions() {
  const qs = state.data.questions || [];
  const covered = qs.filter(q => q.coverage_status === 'covered').length;
  const questionValue = document.getElementById('val-questions');
  const questionSub = document.getElementById('val-questions-sub');
  if (questionValue) questionValue.textContent = qs.length || 0;
  if (questionSub) questionSub.textContent = `${covered} covered`;
  document.getElementById('questions-container').innerHTML = qs.map(q => {
    const st = q.coverage_status;
    const icon = st === 'covered' ? '✓' : st === 'partial' ? '◑' : '○';
    return `
    <div class="q-card">
      <div class="q-icon ${st}">${icon}</div>
      <div class="q-body">
        <div class="q-text">${esc(q.question)}</div>
        <div class="q-fields">${(q.fields_used || []).map(f => `<span class="q-ftag">${esc(f)}</span>`).join('')}</div>
      </div>
      <div class="q-count"><span>${q.evidence_count || 0}</span><br>items</div>
    </div>`;
  }).join('');
}

// ── BEHAVIOURS ────────────────────────────────────────────
function buildBarChart(dataObj, limit = 7) {
  if (!dataObj) return '<p style="color:var(--text-muted);font-size:12px;">No data</p>';
  return Object.entries(dataObj)
    .sort((a,b) => b[1].percent - a[1].percent)
    .slice(0, limit)
    .map(([k,v]) => `
    <div class="bar-row">
      <div class="bar-header">
        <span class="bar-label">${k.replace(/_/g,' ')}</span>
        <span class="bar-value">${v.percent}% (${v.count})</span>
      </div>
      <div class="bar-track"><div class="bar-fill" style="width:${Math.min(v.percent,100)}%"></div></div>
    </div>`).join('');
}

function renderBehaviours() {
  const b = state.data.behaviours;
  if (!b) return;
  if (b.reason_for_saving)    document.getElementById('chart-reason').innerHTML    = buildBarChart(b.reason_for_saving);
  if (b.wishlist_intent)      document.getElementById('chart-intent').innerHTML    = buildBarChart(b.wishlist_intent);
  if (b.purchase_stage)       document.getElementById('chart-stage').innerHTML     = buildBarChart(b.purchase_stage);
  if (b.behaviour_after_saving) document.getElementById('chart-action').innerHTML  = buildBarChart(b.behaviour_after_saving);
  if (b.off_platform_research)  document.getElementById('chart-research').innerHTML = buildBarChart(b.off_platform_research);
  if (b.workaround_distribution) document.getElementById('chart-workaround').innerHTML = buildBarChart(b.workaround_distribution);
  if (b.friction_distribution) {
    const fd = {};
    for (const [k,v] of Object.entries(b.friction_distribution)) {
      fd[k] = { count: v.count, percent: v.of_all_annotations.percent };
    }
    document.getElementById('chart-friction').innerHTML = buildBarChart(fd, 10);
  }
}

// ── SEGMENTS ──────────────────────────────────────────────
function renderSegments() {
  const segs = state.data.segments || [];
  document.getElementById('segments-container').innerHTML = segs.map(s => `
    <div class="seg-card">
      <div class="seg-name">${esc(s.name.replace(/_/g,' '))}</div>
      <div class="seg-badge-row">
        <div class="seg-pill">${s.count} items</div>
        <div class="seg-pct">${(s.fraction_of_total * 100).toFixed(1)}% of corpus</div>
      </div>
      <div class="seg-desc">${esc(s.description)}</div>
      ${s.top_frictions ? `<div style="margin-top:12px;display:flex;flex-wrap:wrap;gap:4px;">${s.top_frictions.map(f => `<span class="q-ftag">${f.replace(/_/g,' ')}</span>`).join('')}</div>` : ''}
    </div>`).join('');
}

// ── OPPORTUNITIES ─────────────────────────────────────────
function renderOpportunities() {
  const opps = state.data.opportunities || [];
  document.getElementById('opportunities-container').innerHTML = opps.map((o, i) => {
    const score = Math.round(o.overall_score * 100);
    const deg = score * 3.6;
    return `
    <div class="opp-card">
      <div class="opp-rank">#${i+1}</div>
      <div class="opp-body">
        <div class="opp-stmt">${esc(o.statement)}</div>
        <div class="opp-tags">
          <div class="opp-tag"><i data-feather="users" style="width:11px;height:11px;"></i>${esc((o.segment_name||'').replace(/_/g,' '))}</div>
          <div class="opp-tag"><i data-feather="file-text" style="width:11px;height:11px;"></i>${o.evidence_count} evidence items</div>
          <div class="opp-tag"><i data-feather="alert-circle" style="width:11px;height:11px;"></i>${esc(o.dominant_friction_type||'mixed').replace(/_/g,' ')}</div>
        </div>
      </div>
      <div class="opp-score-block">
        <div class="opp-donut" onclick='showOppDetails(${JSON.stringify(o)})' title="Click for 7-factor breakdown">
          <div class="opp-donut-bg" style="background:conic-gradient(var(--primary) ${deg}deg,var(--bg-elevated) ${deg}deg);border-radius:50%;"></div>
          <div class="opp-donut-fg"><span class="opp-score-num">${score}</span></div>
        </div>
        <div class="opp-breakdown-link" onclick='showOppDetails(${JSON.stringify(o)})'>Breakdown</div>
      </div>
    </div>`;
  }).join('');
}

// ── EVIDENCE ──────────────────────────────────────────────
function renderEvidence() {
  const ev = (state.data.evidence || []).filter(e => {
    const iMatch = !state.activeIntentFilter || e.wishlist_intent === state.activeIntentFilter;
    const sMatch = !state.activeSourceFilter || e.source_type === state.activeSourceFilter;
    return iMatch && sMatch;
  });

  document.getElementById('evidence-container').innerHTML = ev.length === 0
    ? '<p style="color:var(--text-muted);padding:20px 0;">No evidence matches the current filters.</p>'
    : ev.map(e => {
        const frictions = (() => { try { return Array.isArray(e.frictions) ? e.frictions : JSON.parse(e.frictions || '[]'); } catch { return []; } })();
        return `
        <div class="ev-card" onclick="showEvidenceDetail('${e.raw_id}')">
          <div class="ev-top">
            <div class="ev-quote">"${esc((e.raw_text || '').substring(0, 200))}${(e.raw_text||'').length > 200 ? '…' : ''}"</div>
            <div class="ev-src">${esc(e.source_type || '').replace(/_/g,' ')}</div>
          </div>
          <div class="ev-bottom">
            ${e.wishlist_intent ? `<span class="ev-tag intent">${esc(e.wishlist_intent.replace(/_/g,' '))}</span>` : ''}
            ${frictions.slice(0,2).map(f => `<span class="ev-tag friction">${esc((f.type||f).replace(/_/g,' '))}</span>`).join('')}
            ${e.purchase_stage ? `<span class="ev-tag stage">${esc(e.purchase_stage.replace(/_/g,' '))}</span>` : ''}
          </div>
        </div>`;
      }).join('');
}

function setupFilters() {
  document.querySelectorAll('#intent-pills .f-pill').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('#intent-pills .f-pill').forEach(b => b.classList.remove('on'));
      btn.classList.add('on');
      state.activeIntentFilter = btn.dataset.intent;
      renderEvidence();
    });
  });

  document.getElementById('filter-source').addEventListener('change', e => {
    state.activeSourceFilter = e.target.value;
    renderEvidence();
  });
}

// ── SUMMARY ───────────────────────────────────────────────
function setupSummaryButton() {
  document.getElementById('btn-gen-summary').addEventListener('click', () => {
    const body = document.getElementById('summary-body');
    body.innerHTML = '<p style="color:var(--text-muted);">Generating...</p>';
    setTimeout(() => {
      const d = state.data;
      const topOpp = (d.opportunities||[])[0];
      const topSeg = (d.segments||[])[0];
      const blocked = d.overview?.intent_x_friction?.high_intent_with_friction;
      body.innerHTML = `
        <h4>Executive Summary · Myntra Wishlist Discovery Engine</h4>
        <p>This pipeline analyzed <span class="hl">${(d.overview?.total_annotations||0).toLocaleString()} user-generated reviews</span> from the configured public sources, annotated across structured behavioral dimensions using Gemini with support-span validation.</p>
        <h4>Core Finding</h4>
        <p>Of users showing high purchase intent, <span class="hl">${blocked?.percent || 0}% are blocked from converting</span> by at least one measurable friction. This is an observational signal, not a causal conclusion.</p>
        <h4>Top Three Friction Types</h4>
        <ul>
          ${(Object.entries(d.behaviours?.friction_distribution || {}).slice(0, 3).map(([name, value]) => `<li><strong>${esc(name.replace(/_/g,' '))}</strong> — ${value.count} mentions (${value.of_all_annotations.percent}% of annotated evidence).</li>`).join('') || '<li>No friction distribution is available yet.</li>')}
        </ul>
        <h4>Highest-Priority Opportunity</h4>
        <p>${topOpp ? esc(topOpp.statement) : 'No ranked opportunity is available yet.'} ${topOpp ? `This opportunity scores <span class="hl">${Math.round(topOpp.overall_score*100)}/100</span> across the 7-factor model and affects the <em>${(topSeg?.name||'current') .replace(/_/g,' ')}</em> segment.` : ''}</p>
        <h4>Research Limitations</h4>
        <p>All evidence is observational. Correlations do not imply causation or feature recommendations. Review corpora skew toward negative experiences. Demographic inference was not performed.</p>`;
    }, 1200);
  });
}

// ── DRAWER ────────────────────────────────────────────────
function setupDrawer() {
  document.getElementById('btn-close-drawer').onclick = () => document.getElementById('drawer').classList.add('hidden');
  document.getElementById('drawer').onclick = e => { if (e.target === document.getElementById('drawer')) document.getElementById('drawer').classList.add('hidden'); };
}

window.showOppDetails = function(opp) {
  document.getElementById('drawer-title').textContent = 'Score Breakdown';
  const labels = { frequency:'Frequency', severity:'Severity', purchase_intent:'Purchase Intent', conversion_relevance:'Conversion Relevance', source_convergence:'Source Convergence', segment_concentration:'Segment Concentration', evidence_confidence:'Evidence Confidence' };
  let html = `
    <p style="font-size:13px;color:var(--text-secondary);margin-bottom:20px;line-height:1.6;">${esc(opp.statement)}</p>
    <div style="font-size:22px;font-weight:800;color:var(--primary);margin-bottom:20px;padding-bottom:16px;border-bottom:1px solid var(--border);">
      Overall Score: ${Math.round(opp.overall_score*100)} <span style="font-size:14px;color:var(--text-muted);font-weight:400;">/ 100</span>
    </div>
    <div class="bar-chart">`;
  for (const [key, val] of Object.entries(opp.component_scores || {})) {
    const exp = opp.explanations?.[key] || '';
    html += `
      <div class="bar-row" style="margin-bottom:16px">
        <div class="bar-header">
          <span class="bar-label" style="font-weight:700;">${labels[key] || key}</span>
          <span class="bar-value" style="color:var(--text-primary);font-weight:700;">${(val*100).toFixed(0)}/100</span>
        </div>
        <div class="bar-track" style="height:8px;margin-bottom:5px;"><div class="bar-fill" style="width:${val*100}%"></div></div>
        <div style="font-size:11.5px;color:var(--text-muted);line-height:1.5;">${esc(exp)}</div>
      </div>`;
  }
  html += `</div>`;
  document.getElementById('drawer-body').innerHTML = html;
  document.getElementById('drawer').classList.remove('hidden');
  feather.replace();
};

window.showEvidenceDetail = function(rawId) {
  document.getElementById('drawer-title').textContent = 'Evidence Detail';
  const ev = state.data.evidence.find(e => e.raw_id === rawId);
  if (!ev) {
    document.getElementById('drawer-body').innerHTML = '<p style="color:var(--danger)">Not found.</p>';
    document.getElementById('drawer').classList.remove('hidden');
    return;
  }
  const frictions = (() => { try { return Array.isArray(ev.frictions) ? ev.frictions : JSON.parse(ev.frictions || '[]'); } catch { return []; } })();
  document.getElementById('drawer-body').innerHTML = `
    <div style="margin-bottom:14px;display:flex;gap:8px;align-items:center;">
      <span class="ev-src" style="font-size:11px;background:var(--bg-elevated);padding:3px 9px;border-radius:6px;color:var(--text-muted);text-transform:uppercase;font-weight:700;">${esc(ev.source_type||'').replace(/_/g,' ')}</span>
      <span style="font-size:11px;color:var(--text-muted);font-family:var(--font-mono);">${ev.raw_id}</span>
    </div>
    <div style="background:var(--bg-elevated);padding:16px;border-radius:10px;font-style:italic;line-height:1.65;margin-bottom:20px;font-size:13px;color:var(--text-secondary);">"${esc(ev.raw_text)}"</div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;font-size:13px;margin-bottom:16px;">
      <div><strong>Intent:</strong><br>${esc((ev.wishlist_intent||'-').replace(/_/g,' '))}</div>
      <div><strong>Stage:</strong><br>${esc((ev.purchase_stage||'-').replace(/_/g,' '))}</div>
      <div><strong>Confidence:</strong><br>${ev.evidence_confidence || '-'}/3</div>
      <div><strong>Workaround:</strong><br>${esc((ev.workaround||'none').replace(/_/g,' '))}</div>
    </div>
    ${frictions.length ? `
    <h4 style="font-size:13px;font-weight:700;margin-bottom:10px;color:var(--primary);">Frictions Detected</h4>
    ${frictions.map(f => `
      <div style="background:var(--bg-elevated);padding:10px 14px;border-radius:8px;margin-bottom:8px;font-size:12.5px;">
        <strong>${esc((f.type||f).replace(/_/g,' '))}</strong>
        ${f.severity ? `<span style="float:right;color:var(--primary);font-weight:700;">severity ${f.severity}/3</span>` : ''}
        ${f.support_span ? `<div style="margin-top:6px;color:var(--text-muted);font-style:italic;">"${esc(f.support_span)}"</div>` : ''}
      </div>`).join('')}` : ''}`;
  document.getElementById('drawer').classList.remove('hidden');
};

// ── NAVIGATION ────────────────────────────────────────────
function setupNavigation() {
  const links = document.querySelectorAll('.nav-links a');
  links.forEach(link => {
    link.addEventListener('click', e => {
      e.preventDefault();
      const id = link.getAttribute('href').substring(1);
      links.forEach(l => l.classList.remove('active'));
      link.classList.add('active');
      document.querySelectorAll('main section').forEach(s => s.classList.remove('active-section'));
      document.getElementById(id)?.classList.add('active-section');
    });
  });
}

// ── THEME ─────────────────────────────────────────────────
function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  state.theme = theme;
  localStorage.setItem('theme', theme);
}

function setupThemeToggle() {
  document.getElementById('theme-toggle').addEventListener('click', () => {
    applyTheme(state.theme === 'dark' ? 'light' : 'dark');
    const icon = document.querySelector('#theme-toggle .icon');
    icon.setAttribute('data-feather', state.theme === 'light' ? 'moon' : 'sun');
    feather.replace();
  });
}

// ── CHAT ──────────────────────────────────────────────────
function setupChat() {
  const fab = document.getElementById('chat-fab');
  const panel = document.getElementById('chat-panel');
  const closeBtn = document.getElementById('chat-close');
  const sendBtn = document.getElementById('chat-send');
  const input = document.getElementById('chat-input');

  fab.addEventListener('click', () => toggleChat());
  closeBtn.addEventListener('click', () => toggleChat(false));

  sendBtn.addEventListener('click', sendChat);
  input.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendChat(); }
  });
  input.addEventListener('input', () => {
    input.style.height = 'auto';
    input.style.height = Math.min(input.scrollHeight, 80) + 'px';
  });

  // Suggestion pills
  document.querySelectorAll('.sugg-pill').forEach(pill => {
    pill.addEventListener('click', () => {
      input.value = pill.dataset.q;
      document.getElementById('chat-suggestions').style.display = 'none';
      sendChat();
    });
  });
}

function toggleChat(forceState) {
  const panel = document.getElementById('chat-panel');
  const fab = document.getElementById('chat-fab');
  state.chatOpen = forceState !== undefined ? forceState : !state.chatOpen;
  panel.classList.toggle('open', state.chatOpen);
  feather.replace();
}

function addChatBubble(role, text) {
  const msgs = document.getElementById('chat-messages');
  const div = document.createElement('div');
  div.className = `chat-bubble ${role}`;
  div.innerHTML = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\*(.*?)\*/g, '<em>$1</em>');
  msgs.appendChild(div);
  msgs.scrollTop = msgs.scrollHeight;
  return div;
}

function addTypingIndicator() {
  const msgs = document.getElementById('chat-messages');
  const div = document.createElement('div');
  div.className = 'chat-typing';
  div.id = 'typing-indicator';
  div.innerHTML = '<div class="typ-dot"></div><div class="typ-dot"></div><div class="typ-dot"></div>';
  msgs.appendChild(div);
  msgs.scrollTop = msgs.scrollHeight;
}

function removeTypingIndicator() {
  document.getElementById('typing-indicator')?.remove();
}

async function sendChat() {
  const input = document.getElementById('chat-input');
  const question = input.value.trim();
  if (!question) return;

  input.value = '';
  input.style.height = 'auto';
  document.getElementById('chat-suggestions').style.display = 'none';
  document.getElementById('chat-send').disabled = true;

  addChatBubble('user', esc(question));
  addTypingIndicator();

  // Short simulated delay for realism
  await new Promise(r => setTimeout(r, 900 + Math.random() * 600));

  let answer;
  if (!state.isDemo) {
    try {
      // Try live chat endpoint
      const res = await fetch(`${state.apiUrl}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, history: state.chatHistory.slice(-6) })
      });
      if (res.ok) {
        const data = await res.json();
        answer = data.answer;
      } else throw new Error('API error');
    } catch {
      answer = getChatResponse(question);
    }
  } else {
    answer = getChatResponse(question);
  }

  removeTypingIndicator();
  state.chatHistory.push({ role: 'user', content: question }, { role: 'assistant', content: answer });
  addChatBubble('bot', answer);
  document.getElementById('chat-send').disabled = false;
  feather.replace();
}

// ── PIPELINE ──────────────────────────────────────────────
function setupPipelineControls() {
  const btn = document.getElementById('btn-trigger');
  btn.addEventListener('click', async () => {
    if (state.isDemo) {
      window.location.href = 'pipeline.html';
      return;
    }
    const scope = document.getElementById('run-scope').value;
    const cap = parseInt(document.getElementById('run-limit').value, 10);
    btn.disabled = true; btn.textContent = 'Starting...';
    try {
      const res = await fetch(`${state.apiUrl}/api/pipeline/runs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dataset_scope: scope, item_cap: cap, sources: ['google_play', 'reddit', 'youtube'] })
      });
      if (!res.ok) throw new Error((await res.json()).detail || 'Failed');
      const data = await res.json();
      document.getElementById('run-status').classList.remove('hidden');
      pollRun(data.run_id, btn);
    } catch (e) {
      alert(`Pipeline Error: ${e.message}`);
      btn.disabled = false; btn.textContent = 'Start Run';
    }
  });
}

function pollRun(runId, btn) {
  const interval = setInterval(async () => {
    try {
      const run = await apiGet(`/api/pipeline/runs/${runId}`);
      const stagesEl = document.getElementById('run-stages');
      if (run.stages) {
        stagesEl.innerHTML = run.stages.map(s => `
          <div class="run-stage-item ${s.status}">
            <span>${esc(s.stage_label)}</span>
            <span style="margin-left:auto;font-size:11px;color:var(--text-muted);">${s.status}</span>
          </div>`).join('');
      }
      if (['completed','failed','completed_with_warnings'].includes(run.status)) {
        clearInterval(interval);
        btn.disabled = false; btn.textContent = 'Start Run';
        if (run.status !== 'failed') { fetchAllData().then(renderAll); }
      }
    } catch { clearInterval(interval); btn.disabled = false; btn.textContent = 'Start Run'; }
  }, 2000);
}
