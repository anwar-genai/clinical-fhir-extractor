let API_URL = (localStorage.getItem('apiUrl') || 'http://127.0.0.1:8000');
const form = document.getElementById('uploadForm');
const fileInput = document.getElementById('fileInput');
const output = document.getElementById('output');
const statusEl = document.getElementById('status');
const fileName = document.getElementById('fileName');
const copyBtn = document.getElementById('copyBtn');
const downloadBtn = document.getElementById('downloadBtn');
const apiUrlInput = document.getElementById('apiUrl');
const saveApiBtn = document.getElementById('saveApi');
const dropZone = document.getElementById('dropZone');
const browseBtn = document.getElementById('browseBtn');

// Initialize API URL input
apiUrlInput.value = API_URL;
saveApiBtn.addEventListener('click', () => {
  API_URL = apiUrlInput.value.trim() || 'http://127.0.0.1:8000';
  localStorage.setItem('apiUrl', API_URL);
  setStatus(`Saved API URL: ${API_URL}`);
});

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

// Drag and drop handlers
['dragenter','dragover'].forEach(evt => dropZone.addEventListener(evt, (e) => {
  e.preventDefault();
  e.stopPropagation();
  dropZone.classList.add('dragover');
}));
['dragleave','drop'].forEach(evt => dropZone.addEventListener(evt, (e) => {
  e.preventDefault();
  e.stopPropagation();
  dropZone.classList.remove('dragover');
}));
dropZone.addEventListener('drop', (e) => {
  const dt = e.dataTransfer;
  const files = dt?.files;
  if (files && files.length > 0) {
    fileInput.files = files;
    fileName.textContent = files[0].name;
  }
});

browseBtn.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', () => {
  const f = fileInput.files[0];
  fileName.textContent = f ? f.name : 'No file selected';
});

// Copy & Download
copyBtn.addEventListener('click', async () => {
  try {
    await navigator.clipboard.writeText(output.textContent || '');
    setStatus('Copied to clipboard');
  } catch {
    setStatus('Copy failed');
  }
});

downloadBtn.addEventListener('click', () => {
  const blob = new Blob([output.textContent || ''], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'fhir_output.json';
  a.click();
  URL.revokeObjectURL(url);
});
