function getApi() {
  // pywebview exposes window.pywebview.api.
  // (method names: api_preview, api_rename_all, api_undo_last)
  return window.pywebview && window.pywebview.api ? window.pywebview.api : null;
}

function callApi(method, params) {
  const api = getApi();
  if (!api || typeof api[method] !== 'function') {
    return Promise.reject(new Error('Backend API is not available.')); 
  }

  return api[method](...params);
}

