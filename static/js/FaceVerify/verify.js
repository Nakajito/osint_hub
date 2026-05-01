document.addEventListener('DOMContentLoaded', () => {
  console.log('[FaceVerify] JS v3 loaded');
  const form = document.getElementById('face-verify-form');
  const image1Input = document.getElementById('image1');
  const image2Input = document.getElementById('image2');
  const preview1 = document.getElementById('preview1');
  const preview2 = document.getElementById('preview2');
  const canvas1 = document.getElementById('canvas1');
  const canvas2 = document.getElementById('canvas2');
  const status1 = document.getElementById('face-status1');
  const status2 = document.getElementById('face-status2');
  const fileName1 = document.getElementById('file-name-1');
  const fileName2 = document.getElementById('file-name-2');
  const dzEmpty1 = document.getElementById('dz-empty-1');
  const dzEmpty2 = document.getElementById('dz-empty-2');
  const dzPreview1 = document.getElementById('dz-preview-1');
  const dzPreview2 = document.getElementById('dz-preview-2');
  const dropZone1 = document.getElementById('drop-zone-1');
  const dropZone2 = document.getElementById('drop-zone-2');
  const submitBtn = document.getElementById('submit-btn');
  const loader = document.getElementById('search-loader');
  const resultSection = document.getElementById('result-section');
  const errorSection = document.getElementById('error-section');
  const resetBtn = document.getElementById('reset-btn');

  // ===== Face detection model (progressive enhancement) =====
  const MODEL_URL = 'https://cdn.jsdelivr.net/npm/@vladmandic/face-api@1.7.13/model';
  let modelReady = false;

  try {
    faceapi.nets.tinyFaceDetector.loadFromUri(MODEL_URL)
      .then(() => { modelReady = true; })
      .catch((e) => console.warn('Face model load failed:', e));
  } catch (e) {
    console.warn('faceapi not available:', e);
  }

  // ===== Drag & drop =====
  function setupDragDrop(dropZone, inputEl, imgEl, canvasEl, statusEl, fileNameEl, emptyEl, previewEl) {
    dropZone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropZone.classList.add('drag-over');
    });
    dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
    dropZone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropZone.classList.remove('drag-over');
      const file = e.dataTransfer.files[0];
      if (file && file.type.startsWith('image/')) {
        const dt = new DataTransfer();
        dt.items.add(file);
        inputEl.files = dt.files;
        loadPreview(inputEl, imgEl, canvasEl, statusEl, fileNameEl, emptyEl, previewEl);
      }
    });
    dropZone.addEventListener('click', (e) => {
      if (!e.target.closest('label') && !e.target.closest('.dz-preview') && !e.target.closest('.dz-clear')) {
        inputEl.click();
      }
    });
  }

  setupDragDrop(dropZone1, image1Input, preview1, canvas1, status1, fileName1, dzEmpty1, dzPreview1);
  setupDragDrop(dropZone2, image2Input, preview2, canvas2, status2, fileName2, dzEmpty2, dzPreview2);

  // ===== Load preview (img always works) then detect =====
  function loadPreview(inputEl, imgEl, canvasEl, statusEl, fileNameEl, emptyEl, previewEl) {
    if (!inputEl.files[0]) return;

    const file = inputEl.files[0];
    const url = URL.createObjectURL(file);

    imgEl.onerror = () => URL.revokeObjectURL(url);

    imgEl.onload = () => {
      URL.revokeObjectURL(url);

      // Show preview immediately — img handles scaling natively
      fileNameEl.textContent = file.name.toUpperCase();
      emptyEl.classList.add('d-none');
      previewEl.classList.remove('d-none');

      // Reset canvas overlay
      canvasEl.width = 0;
      canvasEl.height = 0;
      statusEl.classList.add('d-none');

      // Face detection is optional — runs only if model loaded
      if (modelReady) {
        runDetection(imgEl, canvasEl, statusEl);
      }
    };

    imgEl.src = url;
  }

  // ===== Face detection on img element + draw overlay =====
  async function runDetection(imgEl, canvasEl, statusEl) {
    statusEl.textContent = 'Scanning...';
    statusEl.className = 'badge bg-secondary';
    statusEl.classList.remove('d-none');

    try {
      const detections = await faceapi.detectAllFaces(
        imgEl,
        new faceapi.TinyFaceDetectorOptions({ inputSize: 416, scoreThreshold: 0.45 })
      );

      if (detections.length === 0) {
        statusEl.textContent = 'Sin rostro detectado';
        statusEl.className = 'badge bg-warning text-dark';
        return;
      }

      // Scale detection coords (natural img space → displayed img space)
      const dispW = imgEl.offsetWidth;
      const dispH = imgEl.offsetHeight;
      const scaleX = dispW / imgEl.naturalWidth;
      const scaleY = dispH / imgEl.naturalHeight;

      // Canvas overlay covers the same area as the displayed img
      // (centered in dz-canvas-wrap by flexbox)
      const wrap = imgEl.parentElement;
      const offsetX = (wrap.offsetWidth - dispW) / 2;
      const offsetY = (wrap.offsetHeight - dispH) / 2;

      canvasEl.width = wrap.offsetWidth;
      canvasEl.height = wrap.offsetHeight;
      canvasEl.style.top = '0';
      canvasEl.style.left = '0';
      canvasEl.style.width = wrap.offsetWidth + 'px';
      canvasEl.style.height = wrap.offsetHeight + 'px';

      const ctx = canvasEl.getContext('2d');
      const lw = Math.max(2, Math.round(dispW / 120));
      const dotR = Math.max(3, Math.round(dispW / 90));
      ctx.strokeStyle = '#20c997';
      ctx.lineWidth = lw;

      detections.forEach((det) => {
        const { x, y, width, height } = det.box;
        const rx = x * scaleX + offsetX;
        const ry = y * scaleY + offsetY;
        const rw = width * scaleX;
        const rh = height * scaleY;
        ctx.strokeRect(rx, ry, rw, rh);
        ctx.fillStyle = '#20c997';
        [[rx, ry], [rx + rw, ry], [rx, ry + rh], [rx + rw, ry + rh]].forEach(([cx, cy]) => {
          ctx.beginPath();
          ctx.arc(cx, cy, dotR, 0, Math.PI * 2);
          ctx.fill();
        });
      });

      statusEl.textContent = detections.length === 1 ? '1 rostro detectado' : `${detections.length} rostros detectados`;
      statusEl.className = 'badge bg-success';
    } catch (e) {
      statusEl.textContent = 'Error de detección';
      statusEl.className = 'badge bg-danger';
    }
  }

  image1Input.addEventListener('change', () => loadPreview(image1Input, preview1, canvas1, status1, fileName1, dzEmpty1, dzPreview1));
  image2Input.addEventListener('change', () => loadPreview(image2Input, preview2, canvas2, status2, fileName2, dzEmpty2, dzPreview2));

  // ===== Clear slot =====
  function clearSlot(inputEl, imgEl, canvasEl, statusEl, fileNameEl, emptyEl, previewEl) {
    inputEl.value = '';
    imgEl.src = '';
    canvasEl.width = 0;
    canvasEl.height = 0;
    statusEl.classList.add('d-none');
    fileNameEl.textContent = '';
    previewEl.classList.add('d-none');
    emptyEl.classList.remove('d-none');
  }

  document.getElementById('clear1').addEventListener('click', (e) => {
    e.stopPropagation();
    clearSlot(image1Input, preview1, canvas1, status1, fileName1, dzEmpty1, dzPreview1);
  });
  document.getElementById('clear2').addEventListener('click', (e) => {
    e.stopPropagation();
    clearSlot(image2Input, preview2, canvas2, status2, fileName2, dzEmpty2, dzPreview2);
  });

  // ===== Form submit =====
  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    if (!image1Input.files[0] || !image2Input.files[0]) {
      showError('Selecciona ambas imágenes antes de comparar.');
      return;
    }

    resultSection.classList.add('d-none');
    errorSection.classList.add('d-none');
    loader.classList.remove('d-none');
    submitBtn.disabled = true;

    const formData = new FormData(form);
    const csrf = getCookie('csrftoken');

    try {
      const resp = await fetch('', {
        method: 'POST',
        headers: { 'X-CSRFToken': csrf },
        body: formData,
      });

      if (!resp.ok) {
        const data = await resp.json();
        throw new Error(extractFirstError(data.errors || {}) || 'Error al enviar el formulario.');
      }

      const { task_id } = await resp.json();
      pollStatus(task_id);
    } catch (err) {
      hideLoader();
      showError(err.message);
    }
  });

  // ===== Polling =====
  function pollStatus(taskId) {
    let polls = 0;
    const MAX_POLLS = 120;
    const interval = setInterval(async () => {
      polls++;
      if (polls > MAX_POLLS) {
        clearInterval(interval);
        hideLoader();
        showError('Tiempo de espera agotado.');
        return;
      }
      try {
        const resp = await fetch(`/face/status/${taskId}/`);
        const data = await resp.json();
        if (data.state === 'SUCCESS') {
          clearInterval(interval);
          hideLoader();
          showResult(data.result);
        } else if (data.state === 'FAILURE') {
          clearInterval(interval);
          hideLoader();
          showError(data.error || 'Error desconocido en el servidor.');
        }
      } catch (err) {
        clearInterval(interval);
        hideLoader();
        showError('Error de red al verificar el estado.');
      }
    }, 1500);
  }

  // ===== Show result =====
  function showResult(result) {
    if (result.ok === false) {
      showError(result.error || 'No se pudo completar la verificación.');
      return;
    }

    const verified = result.verified;
    const confidence = parseFloat(result.confidence) || 0;
    const gaugeFill = document.getElementById('gauge-fill');
    const gaugeVal = document.getElementById('gauge-value');

    gaugeFill.style.stroke = verified ? '#FF6500' : '#dc3545';
    gaugeFill.style.strokeDashoffset = 251 - (251 * confidence / 100);

    let current = 0;
    const target = Math.round(confidence);
    const step = Math.max(1, Math.ceil(target / 40));
    const counter = setInterval(() => {
      current = Math.min(current + step, target);
      gaugeVal.textContent = current + '%';
      if (current >= target) clearInterval(counter);
    }, 25);

    const badge = document.getElementById('result-badge');
    if (verified) {
      badge.style.cssText = 'background:linear-gradient(135deg,#1E3E62,#0B192C);color:#fff;font-size:.68rem;letter-spacing:.08em;padding:.3rem .8rem;border-radius:.2rem;';
      badge.innerHTML = '<i class="bi bi-patch-check-fill me-1"></i>Match Confirmed';
    } else {
      badge.style.cssText = 'background:linear-gradient(135deg,#dc3545,#a71d2a);color:#fff;font-size:.68rem;letter-spacing:.08em;padding:.3rem .8rem;border-radius:.2rem;';
      badge.innerHTML = '<i class="bi bi-x-circle-fill me-1"></i>No Match';
    }

    const confEl = document.getElementById('confidence-level-val');
    if (confidence >= 80) { confEl.textContent = 'HIGH'; confEl.style.color = '#28a745'; }
    else if (confidence >= 60) { confEl.textContent = 'MEDIUM'; confEl.style.color = '#ffc107'; }
    else { confEl.textContent = 'LOW'; confEl.style.color = '#dc3545'; }

    document.getElementById('r-distance').textContent = result.distance;
    document.getElementById('r-threshold').textContent = result.threshold;
    document.getElementById('r-confidence').textContent = result.confidence;
    document.getElementById('r-model').textContent = result.model;
    document.getElementById('r-detector').textContent = result.detector_backend;

    resultSection.classList.remove('d-none');
    resultSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  // ===== Reset =====
  resetBtn.addEventListener('click', () => {
    resultSection.classList.add('d-none');
    errorSection.classList.add('d-none');
    form.reset();
    clearSlot(image1Input, preview1, canvas1, status1, fileName1, dzEmpty1, dzPreview1);
    clearSlot(image2Input, preview2, canvas2, status2, fileName2, dzEmpty2, dzPreview2);
    document.getElementById('gauge-fill').style.strokeDashoffset = '251';
    document.getElementById('gauge-value').textContent = '0%';
  });

  // ===== Helpers =====
  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return '';
  }

  function extractFirstError(errors) {
    for (const field in errors) {
      const msgs = errors[field];
      if (Array.isArray(msgs) && msgs.length > 0) return msgs[0];
      if (typeof msgs === 'string') return msgs;
    }
    return '';
  }

  function hideLoader() {
    loader.classList.add('d-none');
    submitBtn.disabled = false;
  }

  function showError(msg) {
    document.getElementById('error-message').textContent = msg;
    errorSection.classList.remove('d-none');
    errorSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
});
