// ── DOM refs ──────────────────────────────────────────────────────────────────
const form     = document.getElementById('main-form');
const input    = document.getElementById('domain-input');
const btn      = document.getElementById('run-btn');
const btnText  = btn.querySelector('.btn-text');
const btnLoad  = btn.querySelector('.btn-loader');
const errorMsg = document.getElementById('error-msg');
const results  = document.getElementById('results');

// ── submit ────────────────────────────────────────────────────────────────────
form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const domain = input.value.trim();

    // client-side validation
    if (!domain) {
        showError('Enter a domain first — e.g. openai.com');
        input.focus();
        return;
    }
    if (domain.includes(' ') || !domain.includes('.')) {
        showError('That doesn\'t look like a domain. Try something like openai.com');
        input.focus();
        return;
    }

    setLoading(true);
    clearError();
    resetResults();

    try {
        const resp = await fetch('/api/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ domain }),
        });
        const data = await resp.json();

        if (!resp.ok) {
            showError(data.error || 'Something went wrong on the server');
            return;
        }

        await renderStaged(data);
    } catch {
        showError('Could not reach the server — make sure app.py is running');
    } finally {
        setLoading(false);
    }
});

// ── staged reveal — makes the pipeline feel alive ─────────────────────────────
async function renderStaged(data) {
    results.style.display = 'block';
    results.scrollIntoView({ behavior: 'smooth', block: 'start' });

    // Stage 1 — companies
    setStepPending(1, 'Searching Ocean.io...');
    await sleep(400);
    renderCompanies(data.companies || []);
    show('section-companies');
    setStepDone(1, `${(data.companies || []).length} found`);

    // Stage 2 — people (same API call, staggered reveal)
    await sleep(500);
    setStepPending(2, 'Querying Prospeo...');
    await sleep(600);
    renderContacts(data.contacts || []);
    show('section-contacts');
    setStepDone(2, `${(data.contacts || []).length} contacts`);

    // Stage 3 — emails (already in contacts data, just light up)
    await sleep(500);
    setStepPending(3, 'Resolving via Eazyreach...');
    await sleep(500);
    setStepDone(3, 'emails resolved');

    // Stage 4 — outreach
    await sleep(500);
    setStepPending(4, 'Generating copy...');
    await sleep(700);
    renderOutreach(data.contacts || []);
    show('section-outreach');
    setStepDone(4, `${(data.contacts || []).length} drafts ready`);

    // final toast
    await sleep(200);
    toast(`Pipeline complete — ${(data.contacts || []).length} outreach emails ready`, 'success');
}

// ── step indicator helpers ────────────────────────────────────────────────────
function setStepPending(n, label) {
    const si = document.getElementById(`si-${n}`);
    const ss = document.getElementById(`ss-${n}`);
    if (si) si.classList.add('pending');
    if (ss) ss.textContent = label;
}

function setStepDone(n, label) {
    const si = document.getElementById(`si-${n}`);
    const ss = document.getElementById(`ss-${n}`);
    if (si) {
        si.classList.remove('pending');
        si.classList.add('active');
    }
    if (ss) ss.textContent = label;
}

// ── renderers ─────────────────────────────────────────────────────────────────
function renderCompanies(companies) {
    document.getElementById('co-count').textContent = `${companies.length} companies`;

    const grid = document.getElementById('companies-grid');
    grid.innerHTML = companies.map((c, i) => `
        <div class="company-card" style="animation-delay:${i * 60}ms">
            <div class="company-name">${esc(c.name)}</div>
            <div class="company-domain">${esc(c.domain)}</div>
            <div class="company-meta">
                <span class="company-industry">${esc(c.industry || '')}</span>
                ${c.match_score ? `<span class="match-score">${c.match_score}%</span>` : ''}
            </div>
            ${c.employee_count ? `<div class="company-size">${esc(c.employee_count)} employees</div>` : ''}
        </div>
    `).join('');
}

function renderContacts(contacts) {
    document.getElementById('ct-count').textContent = `${contacts.length} contacts`;

    document.getElementById('contacts-table').innerHTML = contacts.map((c, i) => {
        const conf = c.confidence || 0;
        const confColor = conf >= 85 ? 'var(--green)' : conf >= 70 ? 'var(--yellow)' : 'var(--red)';
        const statusClass = c.email_status === 'from_prospeo' ? 'valid'
            : conf >= 75 ? 'valid' : 'unverified';
        const statusLabel = c.email_status === 'from_prospeo' ? 'verified'
            : conf >= 75 ? 'likely valid' : 'pattern';

        return `
        <tr style="animation-delay:${i * 40}ms">
            <td class="td-name">${esc(c.full_name || `${c.first_name} ${c.last_name}`)}</td>
            <td>${esc(c.title || '—')}</td>
            <td><span class="td-company">${esc(c.company || '—')}</span></td>
            <td class="td-email">${esc(c.email || '—')}</td>
            <td>
                <span class="status-badge ${statusClass}">${statusLabel}</span>
                <span class="conf-num" style="color:${confColor}">${conf}%</span>
            </td>
        </tr>`;
    }).join('');
}

function renderOutreach(contacts) {
    document.getElementById('ou-count').textContent = `${contacts.length} drafts`;

    document.getElementById('outreach-grid').innerHTML = contacts.map((c, i) => {
        const sourceLabel = c.copy_source === 'ai' ? '✨ AI' : '📝 Template';
        const sourceCls   = c.copy_source === 'ai' ? 'src-ai' : 'src-tmpl';

        return `
        <div class="outreach-card" style="animation-delay:${i * 80}ms">
            <div class="outreach-header">
                <div class="outreach-meta">
                    <span class="outreach-name">${esc(c.full_name || '')}</span>
                    <span class="outreach-sep">·</span>
                    <span class="outreach-email">${esc(c.email || '')}</span>
                    <span class="outreach-sep">·</span>
                    <span class="outreach-company">${esc(c.company || '')}</span>
                </div>
                <span class="outreach-source ${sourceCls}">${sourceLabel}</span>
            </div>
            <div class="outreach-subject">${esc(c.subject || '')}</div>
            <div class="outreach-body">${esc(c.body || '')}</div>
        </div>`;
    }).join('');
}

// ── toast notifications ────────────────────────────────────────────────────────
function toast(msg, type = 'info', duration = 3500) {
    const container = document.getElementById('toast-container');
    const el = document.createElement('div');
    el.className = `toast toast-${type}`;
    el.textContent = msg;
    container.appendChild(el);

    requestAnimationFrame(() => el.classList.add('toast-visible'));

    setTimeout(() => {
        el.classList.remove('toast-visible');
        setTimeout(() => el.remove(), 300);
    }, duration);
}

// ── utilities ─────────────────────────────────────────────────────────────────
function sleep(ms) {
    return new Promise(r => setTimeout(r, ms));
}

function show(id) {
    const el = document.getElementById(id);
    if (el) el.style.display = 'block';
}

function setLoading(on) {
    btn.disabled = on;
    btnText.style.display = on ? 'none' : 'inline';
    btnLoad.style.display  = on ? 'flex'  : 'none';
    if (on) input.disabled = true;
    else    input.disabled = false;
}

function showError(msg) {
    errorMsg.textContent = msg;
    errorMsg.style.display = 'block';
    errorMsg.classList.add('shake');
    setTimeout(() => errorMsg.classList.remove('shake'), 400);
    toast(msg, 'error');
}

function clearError() {
    errorMsg.style.display = 'none';
    errorMsg.textContent = '';
}

function resetResults() {
    ['si-1','si-2','si-3','si-4'].forEach(id => {
        const el = document.getElementById(id);
        if (el) { el.classList.remove('active', 'pending'); }
    });
    ['ss-1','ss-2','ss-3','ss-4'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.textContent = '';
    });
    ['section-companies','section-contacts','section-outreach'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.style.display = 'none';
    });
    results.style.display = 'none';
}

// XSS-safe escape
function esc(str) {
    if (!str) return '';
    const d = document.createElement('div');
    d.textContent = String(str);
    return d.innerHTML;
}

// allow pressing Enter in input
input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') form.dispatchEvent(new Event('submit'));
});
