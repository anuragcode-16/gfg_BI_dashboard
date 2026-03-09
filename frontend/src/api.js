// src/api.js
const API_BASE = 'https://gfg-bi-dashboard-1.onrender.com/api';

export async function sendQuery({ query, conversationHistory, previousSql, dbPath, schemaOverride }) {
  const res = await fetch(`${API_BASE}/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query,
      conversation_history: conversationHistory || null,
      previous_sql: previousSql || null,
      db_path: dbPath || null,
      schema_override: schemaOverride || null,
    }),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function uploadCSV(file) {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${API_BASE}/upload`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) throw new Error(`Upload error: ${res.status}`);
  return res.json();
}

export async function resetDataset() {
  const res = await fetch(`${API_BASE}/reset`, { method: 'POST' });
  if (!res.ok) throw new Error(`Reset error: ${res.status}`);
  return res.json();
}

export async function getUploadStatus() {
  const res = await fetch(`${API_BASE}/upload/status`);
  if (!res.ok) throw new Error(`Status error: ${res.status}`);
  return res.json();
}

export async function getSchema() {
  const res = await fetch(`${API_BASE}/schema`);
  if (!res.ok) throw new Error(`Schema error: ${res.status}`);
  return res.json();
}

export async function healthCheck() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    return res.ok;
  } catch {
    return false;
  }
}
