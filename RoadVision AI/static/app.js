const state = {
  selectedImage: null,
  confidence: 5,
  detections: []
};

const apiBase = 'http://127.0.0.1:8000';

function setConfidence(val) {
  state.confidence = Number(val);
  document.getElementById('confidenceValue').textContent = `${state.confidence}%`;
  document.getElementById('confidenceSlider').value = state.confidence;
}

function handleFileSelect(file) {
  if (!file) return;
  state.selectedImage = file;
  document.getElementById('fileName').textContent = file.name;
  document.getElementById('fileMeta').textContent = `${(file.size / 1024).toFixed(1)} KB`;
}

function renderDetections(items) {
  const tableBody = document.getElementById('detectionsTableBody');
  tableBody.innerHTML = '';

  if (!items || !items.length) {
    tableBody.innerHTML = `<tr><td colspan="4">No detections</td></tr>`;
    return;
  }

  items.forEach((item, index) => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${index + 1}</td>
      <td>${item.class_name || 'Unknown'}</td>
      <td>${(item.confidence * 100).toFixed(1)}%</td>
      <td>${item.bbox_xyxy ? item.bbox_xyxy.join(', ') : 'n/a'}</td>
    `;
    tableBody.appendChild(row);
  });
}

async function analyzeImage() {
  if (!state.selectedImage) {
    alert('Please choose an image first.');
    return;
  }

  const formData = new FormData();
  formData.append('file', state.selectedImage);
  formData.append('confidence', String(state.confidence));

  try {
    const response = await fetch(`${apiBase}/predict`, {
      method: 'POST',
      body: formData
    });

    const data = await response.json();
    if (!data.success) {
      throw new Error(data.detail || 'Prediction failed');
    }

    state.detections = data.detections || [];
    renderDetections(state.detections);
    document.getElementById('resultSummary').textContent = `Detected ${state.detections.length} objects`;
  } catch (error) {
    alert(error.message || 'Failed to analyze image');
  }
}

document.getElementById('confidenceSlider').addEventListener('input', (event) => {
  setConfidence(event.target.value);
});

document.getElementById('imageInput').addEventListener('change', (event) => {
  handleFileSelect(event.target.files[0]);
});

document.getElementById('analyzeBtn').addEventListener('click', analyzeImage);

setConfidence(5);
