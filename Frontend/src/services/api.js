const BASE_URL = '/api/v1';

/**
 * Validate a pair of GeoTIFF files.
 */
export async function validateImages(preFile, postFile) {
  const formData = new FormData();
  formData.append('pre_flood', preFile);
  formData.append('post_flood', postFile);

  const res = await fetch(`${BASE_URL}/flood/validate`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Validation failed (${res.status}): ${text}`);
  }
  return res.json();
}

/**
 * Run the complete flood analysis pipeline in one request.
 */
export async function runFullPipeline(preFile, postFile, options = {}) {
  const formData = new FormData();
  formData.append('pre_flood', preFile);
  formData.append('post_flood', postFile);
  formData.append('method', options.method || 'auto');
  formData.append('simplify_tolerance', String(options.simplifyTolerance ?? '0.0001'));
  formData.append('buffer_m', String(options.bufferM ?? '100.0'));

  const res = await fetch(`${BASE_URL}/flood/pipeline`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Pipeline failed (${res.status}): ${text}`);
  }
  return res.json();
}

/**
 * Run dual-GeoTIFF Image Study flood change detection and centroid analysis.
 */
export async function runImageStudy(preFile, postFile) {
  const formData = new FormData();
  formData.append('pre_flood', preFile);
  formData.append('post_flood', postFile);
  formData.append('method', 'auto');

  const res = await fetch(`${BASE_URL}/flood/image-study`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: res.statusText }));
    const detail = typeof errorData.detail === 'string' ? errorData.detail : JSON.stringify(errorData.detail);
    throw new Error(detail || 'Image Study analysis failed.');
  }
  return res.json();
}

/**
 * Send a natural-language question to the AI assistant.
 */
export async function sendChatQuery(question, sessionId = null, context = null) {
  const res = await fetch(`${BASE_URL}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, session_id: sessionId, context }),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Chat request failed (${res.status}): ${text}`);
  }
  return res.json();
}

/**
 * Get cached session results by session_id.
 */
export async function getSession(sessionId) {
  const res = await fetch(`${BASE_URL}/flood/session/${sessionId}`);
  if (!res.ok) throw new Error(`Session not found: ${sessionId}`);
  return res.json();
}

/**
 * Fetch a real demo GeoTIFF file from the backend and return as File object.
 */
export async function getDemoFile(filename) {
  const res = await fetch(`${BASE_URL}/flood/demo-file/${filename}`);
  if (!res.ok) {
    // Fallback to /flood/sample/
    const res2 = await fetch(`${BASE_URL}/flood/sample/${filename}`);
    if (!res2.ok) {
      throw new Error(`Failed to load demo file ${filename} (${res.status})`);
    }
    const blob = await res2.blob();
    return new File([blob], filename, { type: 'image/tiff' });
  }
  const blob = await res.blob();
  return new File([blob], filename, { type: 'image/tiff' });
}

/**
 * Load a real demo pair (Kerala or Nepal) as File objects for pipeline analysis.
 */
export async function loadDemoPair(demoId) {
  if (demoId === 'kerala') {
    const [pre, post] = await Promise.all([
      getDemoFile('kerala_before_flood.tif'),
      getDemoFile('kerala_after_flood.tif'),
    ]);
    return { pre, post, name: 'Kerala Flood', id: 'kerala' };
  } else if (demoId === 'nepal') {
    const [pre, post] = await Promise.all([
      getDemoFile('nepal_before_flood.tif'),
      getDemoFile('nepal_after_flood.tif'),
    ]);
    return { pre, post, name: 'Nepal 2026 Flood', id: 'nepal' };
  }
  return null;
}

/**
 * Check backend health.
 */
export async function checkHealth() {
  const res = await fetch('/health');
  if (!res.ok) throw new Error('Backend health check failed');
  return res.json();
}

