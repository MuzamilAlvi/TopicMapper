const el = (id) => document.getElementById(id);

function toast({ title, message, type = 'info', duration = 3200 } = {}) {
  const host = el('toastHost');
  if (!host) return;

  const toastEl = document.createElement('div');
  toastEl.className = 'toast toast-pop';

  const icon = type === 'success' ? '✓' : type === 'error' ? '!' : type === 'warning' ? '⚠' : '✦';
  toastEl.innerHTML = `
    <div class="ticon">${icon}</div>
    <div class="tmeta">
      <div class="ttitle">${title || 'Notification'}</div>
      <div class="tmsg">${message || ''}</div>
    </div>
  `;

  host.appendChild(toastEl);
  window.setTimeout(() => {
    toastEl.remove();
  }, duration);
}

function setStatus(pillText, text) {
  el('statusPill').textContent = pillText;
  el('statusText').textContent = text;
}

function setProgress(percent) {
  const p = Math.max(0, Math.min(100, Number(percent) || 0));
  const bar = el('progressBar');
  const detail = el('progressDetail');
  bar.style.width = p + '%';
  detail.textContent = p + '%';
}

function statusBadge(status) {
  const map = {
    matched: { cls: 'matched', label: 'Matched' },
    unmatched: { cls: 'unmatched', label: 'Unmatched' },
    duplicate: { cls: 'duplicate', label: 'Duplicate target' },
    error: { cls: 'error', label: 'Error' },
  };
  const m = map[status] || { cls: '', label: status };
  return `
    <span class="badge ${m.cls}"><span class="dot"></span>${m.label}</span>
  `;
}

