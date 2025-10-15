const API_URL = (localStorage.getItem('apiUrl') || 'http://127.0.0.1:8000');
const form = document.getElementById('uploadForm');
const fileInput = document.getElementById('fileInput');
const output = document.getElementById('output');
const statusEl = document.getElementById('status');

function setStatus(msg) { statusEl.textContent = msg; }

async function extractFHIR(file) {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${API_URL}/extract-fhir`, { method: 'POST', body: formData });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`HTTP ${res.status}: ${err}`);
  }
  return await res.json();
}

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const file = fileInput.files[0];
  if (!file) return;
  try {
    form.querySelector('button').disabled = true;
    setStatus('Uploading and extracting...');
    const data = await extractFHIR(file);
    setStatus('Done');
    output.textContent = JSON.stringify(data, null, 2);
  } catch (err) {
    setStatus('Error');
    output.textContent = String(err);
  } finally {
    form.querySelector('button').disabled = false;
  }
});
