function getApi() {
  // pywebview exposes window.pywebview.api.
  // (method names: api_preview, api_rename_all, api_undo_last)
  return window.pywebview && window.pywebview.api ? window.pywebview.api : null;
}


