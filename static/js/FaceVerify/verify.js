document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('face-verify-form');
  const image1Input = document.getElementById('image1');
  const image2Input = document.getElementById('image2');
  const preview1 = document.getElementById('preview1');
  const preview2 = document.getElementById('preview2');
  const submitBtn = document.getElementById('submit-btn');
  const loader = document.getElementById('search-loader');
  const resultSection = document.getElementById('result-section');
  const errorSection = document.getElementById('error-section');
  const resetBtn = document.getElementById('reset-btn');

  let preview1URL = null;
  let preview2URL = null;

  function handleImageChange(inputEl, previewEl, urlRef) {
    return function () {
      if (inputEl.files[0]) {
        if (urlRef === 'preview1' && preview1URL) {
          URL.revokeObjectURL(preview1URL);
        } else if (urlRef === 'preview2' && preview2URL) {
          URL.revokeObjectURL(preview2URL);
        }

        const url = URL.createObjectURL(inputEl.files[0]);
        if (urlRef === 'preview1') {
          preview1URL = url;
        } else if (urlRef === 'preview2') {
          preview2URL = url;
        }

        previewEl.src = url;
        previewEl.style.display = 'block';
      } else {
        previewEl.style.display = 'none';
      }
    };
  }

  image1Input.addEventListener('change', handleImageChange(image1Input, preview1, 'preview1'));
  image2Input.addEventListener('change', handleImageChange(image2Input, preview2, 'preview2'));

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    if (!image1Input.files[0] || !image2Input.files[0]) {
      showError('Selecciona ambas imágenes antes de comparar.');
      return;
    }

    resultSection.style.display = 'none';
    errorSection.style.display = 'none';
    loader.style.display = 'block';
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
        const firstError = extractFirstError(data.errors || {});
        throw new Error(firstError || 'Error al enviar el formulario.');
      }

      const { task_id } = await resp.json();
      pollStatus(task_id);
    } catch (err) {
      hideLoader();
      showError(err.message);
    }
  });

  function pollStatus(taskId) {
    const interval = setInterval(async () => {
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

  function showResult(result) {
    if (result.ok === false) {
      showError(result.error || 'No se pudo completar la verificación.');
      return;
    }

    const verified = result.verified;
    const verdict = document.getElementById('result-verdict');
    verdict.className = 'alert ' + (verified ? 'alert-success' : 'alert-danger');
    verdict.innerHTML = verified
      ? '<i class="bi bi-check-circle-fill me-2"></i><strong>Misma persona</strong> — los rostros coinciden.'
      : '<i class="bi bi-x-circle-fill me-2"></i><strong>Personas distintas</strong> — los rostros no coinciden.';

    document.getElementById('r-distance').textContent = result.distance;
    document.getElementById('r-threshold').textContent = result.threshold;
    document.getElementById('r-confidence').textContent = result.confidence;
    document.getElementById('r-model').textContent = result.model;
    document.getElementById('r-detector').textContent = result.detector_backend;

    resultSection.style.display = 'block';
  }

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
    loader.style.display = 'none';
    submitBtn.disabled = false;
  }

  function showError(msg) {
    document.getElementById('error-message').textContent = msg;
    errorSection.style.display = 'block';
  }

  resetBtn.addEventListener('click', () => {
    resultSection.style.display = 'none';
    errorSection.style.display = 'none';
    form.reset();
    preview1.style.display = 'none';
    preview2.style.display = 'none';
  });
});
