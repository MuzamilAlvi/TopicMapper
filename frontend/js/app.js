let selectedFolderPath = null;
let selectedTopicsText = null;
let lastPreview = null;
let currentRows = [];

function readFileText(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () => reject(reader.error);
    reader.onload = () => resolve(String(reader.result || ''));
    reader.readAsText(file);
  });
}

function updateButtonStates() {
  const hasInputs = !!selectedFolderPath && !!selectedTopicsText;
  el('btnPreview').disabled = !hasInputs;
  el('btnRename').disabled = !hasInputs;
}

function renderTable(plans) {
  const tbody = el('rows');
  tbody.innerHTML = '';
  currentRows = plans;

  const rowsFrag = document.createDocumentFragment();

  for (const p of plans) {
    const tr = document.createElement('tr');
    const badgeHtml = statusBadge(p.status);
    tr.innerHTML = `
      <td>${p.original_filename || ''}</td>
      <td>${p.topic_number || '-'}</td>
      <td>${p.official_title ? p.official_title : '-'}</td>
      <td>${p.new_filename ? p.new_filename : '-'}</td>
      <td>${badgeHtml}</td>
    `;
    rowsFrag.appendChild(tr);
  }

  tbody.appendChild(rowsFrag);

  const rowSummary = el('rowSummary');
  const counts = lastPreview?.report?.counts;
  if (counts) {
    rowSummary.textContent = `Matched: ${counts.matched} • Unmatched: ${counts.unmatched} • Duplicates: ${counts.duplicates} • Errors: ${counts.errors}`;
  } else {
    rowSummary.textContent = '—';
  }
}

function applySearchFilter() {
  const q = (el('searchInput').value || '').toLowerCase().trim();
  const f = el('filterSelect').value || 'all';

  const filtered = currentRows.filter(p => {
    const blob = `${p.original_filename || ''} ${p.official_title || ''} ${p.new_filename || ''}`.toLowerCase();
    const matchQ = !q || blob.includes(q);
    const matchF = f === 'all' ? true : p.status === f;
    return matchQ && matchF;
  });

  renderTable(filtered);
}

async function doPreview() {
  if (!selectedFolderPath || !selectedTopicsText) return;

  setStatus('Working…', 'Generating preview');
  setProgress(8);

  try {
    const api = window.pywebview?.api;
    if (!api) throw new Error('Backend API not available');

    setProgress(25);
    const res = await api.api_preview(selectedFolderPath, selectedTopicsText);

    lastPreview = res;
    renderTable(res.plans);

    const counts = res.report?.counts;
    setStatus('Preview ready', counts ? `Matched ${counts.matched} files.` : '');
    setProgress(100);
    toast({ type: 'success', title: 'Preview ready', message: 'Review changes before renaming.' });
  } catch (e) {
    setStatus('Error', 'Could not generate preview');
    setProgress(0);
    toast({ type: 'error', title: 'Preview failed', message: String(e?.message || e) });
  }
}

async function doRenameAll() {
  if (!selectedFolderPath || !selectedTopicsText) return;

  setStatus('Renaming…', 'Applying safe rename rules');
  setProgress(10);

  try {
    const api = window.pywebview?.api;
    if (!api) throw new Error('Backend API not available');

    setProgress(35);
    const res = await api.api_rename_all(selectedFolderPath, selectedTopicsText);
    lastPreview = { ...(lastPreview || {}), plans: lastPreview?.plans, report: res };

    // The backend returns a report, but plans statuses are from preview.
    // Re-run preview to refresh table statuses.
    setProgress(60);
    await doPreview();

    const counts = res?.counts || res?.counts || res?.counts;
    const c = res?.counts;
    setStatus('Completed', c ? `Done: ${c.matched} renamed, ${c.unmatched} skipped, ${c.duplicates} duplicates.` : '');
    setProgress(100);
    toast({ type: 'success', title: 'Rename completed', message: 'A detailed report was generated.' });
    el('undoBtn').disabled = false;
  } catch (e) {
    setStatus('Error', 'Rename failed');
    setProgress(0);
    toast({ type: 'error', title: 'Rename failed', message: String(e?.message || e) });
  }
}

async function doUndo() {
  try {
    const api = window.pywebview?.api;
    if (!api) throw new Error('Backend API not available');

    setStatus('Undoing…', 'Reverting last rename');
    setProgress(25);
    const res = await api.api_undo_last();
    setProgress(100);

    if (res?.ok) {
      setStatus('Undo complete', `Reverted ${res.reverted} files.`);
      toast({ type: 'success', title: 'Undo complete', message: `Reverted ${res.reverted} files.` });
      el('undoBtn').disabled = true;
      await doPreview();
    } else {
      setStatus('Undo not available', res?.message || 'Nothing to undo');
      toast({ type: 'warning', title: 'Undo', message: res?.message || 'Nothing to undo' });
    }
  } catch (e) {
    setStatus('Error', 'Undo failed');
    setProgress(0);
    toast({ type: 'error', title: 'Undo failed', message: String(e?.message || e) });
  }
}

function setFolderInputFromFileList(files) {
  // webkitdirectory folder selection gives multiple files, but we need folder path.
  // In pywebview (Chromium), we can sometimes access file.webkitRelativePath.
  if (!files || !files.length) return;
  const any = files[0];
  const rel = any.webkitRelativePath || any.name || '';
  const firstPart = rel.split('/')[0];
  // We can't reliably get absolute folder path in pure web. We'll prompt user to select folder again.
  // Instead: use file input directory; pywebview can sometimes provide full path in file.name (not reliable).
  // Fallback: require drag/drop to work via custom drop handler.
  selectedFolderPath = null;
}

function wireEvents() {
  const folderInput = el('folderInput');
  const topicsInput = el('topicsInput');

  el('browseFolder').addEventListener('click', () => {
    folderInput.click();
  });

  el('browseTopics').addEventListener('click', () => {
    topicsInput.click();
  });

  folderInput.addEventListener('change', async (ev) => {
    const files = ev.target.files;
    if (!files || !files.length) return;

    // Best effort: infer absolute path if available
    // In pywebview, file inputs may contain full paths in `.path` (Chromium) in some environments.
    const f0 = files[0];
    const maybePath = f0.path || f0.webkitRelativePath || '';

    // If `.path` exists (full path), strip filename to get folder.
    if (typeof f0.path === 'string' && f0.path.includes('\\')) {
      selectedFolderPath = f0.path.replace(/\\[^\\]+$/, '');
    } else {
      // Cannot reliably determine folder path in browser context
      selectedFolderPath = null;
      toast({ type: 'warning', title: 'Folder path unavailable', message: 'Drag & drop a folder into the app for reliable folder selection.' });
    }

    el('folderValue').textContent = selectedFolderPath || 'Not selected';
    updateButtonStates();
  });

  topicsInput.addEventListener('change', async (ev) => {
    const file = ev.target.files && ev.target.files[0];
    if (!file) return;
    selectedTopicsText = await readFileText(file);
    el('topicsValue').textContent = file.name;
    updateButtonStates();
  });

  el('btnPreview').addEventListener('click', doPreview);
  el('btnRename').addEventListener('click', doRenameAll);
  el('undoBtn').addEventListener('click', doUndo);

  el('searchInput').addEventListener('input', applySearchFilter);
  el('filterSelect').addEventListener('change', applySearchFilter);

  el('themeToggle').addEventListener('click', () => {
    const cur = document.documentElement.getAttribute('data-theme') || 'dark';
    const next = cur === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    toast({ type: 'info', title: 'Theme', message: `Switched to ${next} mode` });
  });

  // Keyboard shortcuts
  window.addEventListener('keydown', (e) => {
    const isMac = navigator.platform.toLowerCase().includes('mac');
    const mod = isMac ? e.metaKey : e.ctrlKey;

    if (mod && e.key.toLowerCase() === 'p') {
      e.preventDefault();
      el('btnPreview').click();
    }
    if (mod && e.key.toLowerCase() === 'r') {
      e.preventDefault();
      el('btnRename').click();
    }
    if (mod && e.key.toLowerCase() === 'z') {
      e.preventDefault();
      el('undoBtn').click();
    }
  });

  // Drag & drop (pywebview can provide .path for dropped items)
  const dropFolder = el('dropzoneFolder');
  const dropTopics = el('dropzoneTopics');

  function prevent(e){ e.preventDefault(); e.stopPropagation(); }

  ;[dropFolder, dropTopics].forEach(zone => {
    zone.addEventListener('dragover', (e) => {
      prevent(e);
      zone.style.borderColor = 'rgba(109,94,252,.65)';
    });
    zone.addEventListener('dragleave', (e) => {
      prevent(e);
      zone.style.borderColor = 'rgba(255,255,255,.24)';
    });
    zone.addEventListener('drop', (e) => {
      prevent(e);
      zone.style.borderColor = 'rgba(255,255,255,.24)';

      const dt = e.dataTransfer;
      const files = dt.files;

      if (zone === dropFolder) {
        // Dropped item may include .path for folder in pywebview.
        const item0 = dt.items && dt.items[0];
        // Best effort: use first file's .path, then strip filename.
        if (files && files.length) {
          const f0 = files[0];
          const p = f0.path || '';
          if (p.includes('\\')) {
            selectedFolderPath = p.replace(/\\[^\\]+$/, '');
            el('folderValue').textContent = selectedFolderPath;
            updateButtonStates();
            toast({ type: 'success', title: 'Folder selected', message: selectedFolderPath });
          } else {
            toast({ type: 'warning', title: 'Drop failed', message: 'Could not detect folder path from drop.' });
          }
        } else {
          toast({ type: 'warning', title: 'Drop failed', message: 'No files detected in folder drop.' });
        }
      }

      if (zone === dropTopics) {
        const file = files && files[0];
        if (!file) return;
        if (!file.name.toLowerCase().endsWith('.txt')) {
          toast({ type: 'warning', title: 'Invalid file', message: 'Please drop a .txt topics file.' });
          return;
        }
        readFileText(file).then((txt) => {
          selectedTopicsText = txt;
          el('topicsValue').textContent = file.name;
          updateButtonStates();
          toast({ type: 'success', title: 'Topics imported', message: file.name });
        });
      }
    });
  });
}

document.addEventListener('DOMContentLoaded', () => {
  document.documentElement.setAttribute('data-theme', 'dark');
  wireEvents();
  updateButtonStates();
  setStatus('Idle', 'Select inputs to begin.');
  setProgress(0);
});

