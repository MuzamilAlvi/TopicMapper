/**
 * Filename Format Builder (frontend)
 * - Presets
 * - Token-based formatting
 * - Live preview rendering (if preview DOM exists)
 *
 * Tokens:
 *   {number}       => extracted topic number (possibly zero-padded)
 *   {title}        => official title (sanitized)
 *   {originalName} => original filename without extension
 *   {extension}    => original file extension
 */

(function () {
  // Hard guard: avoid runtime crashes if this file is loaded unexpectedly.
  try {
    const PRESETS = [
      { label: '{number} - {title} (Recommended)', pattern: '{number} - {title}', id: 'recommended' },
      { label: '{title}', pattern: '{title}', id: 'titleOnly' },
      { label: '{title} [{number}]', pattern: '{title} [{number}]', id: 'titleBracket' },
      { label: '{number}_{title}', pattern: '{number}_{title}', id: 'underscore' },
      { label: 'Lesson {number} - {title}', pattern: 'Lesson {number} - {title}', id: 'lesson' },
      { label: '{number}. {title}', pattern: '{number}. {title}', id: 'dot' },
      // Hidden means sequence number is removed completely from final filename
      { label: 'Hidden (title only)', pattern: '{title}', id: 'hidden' }
    ];

    function el(id) {
      return document.getElementById(id);
    }

    function escapeHtml(str) {
      return String(str ?? '')
        .replaceAll('&', '&amp;')
        .replaceAll('<', '<')
        .replaceAll('>', '>')
        .replaceAll('"', '"')
        .replaceAll("'", '&#039;');
    }

    function sanitizeFilenameBody(body) {
      // Windows invalid characters: < > : " / \ | ? *
      return String(body ?? '').replace(/[<>:"/\\|?*]/g, '-').trim();
    }

    function applyTokens(pattern, tokens) {
      let out = String(pattern ?? '');
      out = out.replaceAll('{number}', tokens.number);
      out = out.replaceAll('{title}', tokens.title);
      out = out.replaceAll('{originalName}', tokens.originalName);
      out = out.replaceAll('{extension}', tokens.extension);
      out = out.replace(/\s{2,}/g, ' ').trim();
      return out;
    }

    function getUiStateForRenaming() {
      // The UI may not exist yet; provide defaults for safe operation.
      const keepSeqOn = el('keepSeq')?.checked ?? true;
      const zeroPadOn = el('zeroPad')?.checked ?? false;
      const numPos = el('numPos')?.value ?? 'prefix'; // prefix | suffix | hidden
      const patternText = el('patternInput')?.value ?? '{number} - {title}';

      return {
        keepSequenceNumber: !!keepSeqOn,
        zeroPadNumbers: !!zeroPadOn,
        numberPosition: numPos,
        namingPattern: patternText
      };
    }

    function getPreviewTokensFromExample() {
      // Example per requirement:
      // Number: 019
      // Title: WHILE Loop in Python
      return {
        numberRaw: '19',
        numberDisplay: '019',
        title: 'WHILE Loop in Python',
        originalName: 'AIP301_Topic019_DigiSkills 3.0',
        extension: '.mp4'
      };
    }

    function renderLivePreview() {
      // Optional DOM (not mandatory)
      const container = el('previewExamples');
      if (!container) return;

      const tokens = getPreviewTokensFromExample();
      const ui = getUiStateForRenaming();

      const finalTokens = {
        number: ui.zeroPadNumbers ? tokens.numberDisplay : String(parseInt(tokens.numberRaw, 10) || 0),
        title: tokens.title,
        originalName: tokens.originalName,
        extension: tokens.extension
      };

      // Hidden behavior: if keepSequenceNumber is Off, force {title} only semantics.
      let pattern = ui.namingPattern;
      if (!ui.keepSequenceNumber || ui.numberPosition === 'hidden') {
        pattern = '{title}';
      }

      const exampleRows = [];
      exampleRows.push(applyTokens(pattern, finalTokens));
      exampleRows.push(applyTokens('{title}', finalTokens));
      exampleRows.push(applyTokens('{title} [{number}]', finalTokens));
      exampleRows.push(applyTokens('Lesson {number} - {title}', finalTokens));

      container.innerHTML = exampleRows
        .map((s) => {
          const safe = sanitizeFilenameBody(s);
          return `<div class="preview-line">${escapeHtml(safe)}</div>`;
        })
        .join('');
    }

    function setPreset(presetId) {
      const preset = PRESETS.find((p) => p.id === presetId);
      if (!preset) return;

      if (el('patternInput')) {
        el('patternInput').value = preset.pattern;
      }

      if (presetId === 'hidden' && el('keepSeq')) {
        el('keepSeq').checked = false;
      }

      renderLivePreview();
    }

    function buildPresetsUI() {
      const select = el('presetSelect');
      if (!select) return;

      select.innerHTML = PRESETS
        .map((p) => `<option value="${p.id}">${escapeHtml(p.label)}</option>`)
        .join('');

      select.addEventListener('change', () => setPreset(select.value));

      if (!select.value) setPreset('recommended');
      else setPreset(select.value);
    }

    // Public API for app.js/ui.js
    window.formatBuilder = {
      PRESETS,
      getUiStateForRenaming,
      renderLivePreview,
      setPreset,
      buildPresetsUI
    };

    document.addEventListener('DOMContentLoaded', () => {
      try {
        buildPresetsUI();
        renderLivePreview();

        // Live updates (if controls exist)
        ['keepSeq', 'zeroPad', 'numPos', 'patternInput'].forEach((id) => {
          const node = el(id);
          if (!node) return;
          node.addEventListener('input', renderLivePreview);
          node.addEventListener('change', renderLivePreview);
        });
      } catch (_e) {
        // ignore UI missing
      }
    });
  } catch (_err) {
    // Never throw on load.
  }
})();

