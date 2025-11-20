const API_BASE = 'http://127.0.0.1:5000';

// POST JSON
async function apiPost(path, body){
  try {
    const res = await fetch(API_BASE + path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body || {})
    });
    // some endpoints may return text — try parse safely
    return await res.json();
  } catch (e) {
    console.warn('apiPost error', e);
    return null;
  }
}


// GET JSON
async function apiGet(path){
  try {
    const res = await fetch(API_BASE + path);
    return await res.json();
  } catch (e) {
    console.warn('apiGet error', e);
    return null;
  }
}

window.apiPost = apiPost;
window.apiGet = apiGet;