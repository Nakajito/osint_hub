// 1. Función para copiar al portapapeles
function copyHash() {
    const hashInput = document.getElementById('hashResult');
    hashInput.select();
    hashInput.setSelectionRange(0, 99999); 
    navigator.clipboard.writeText(hashInput.value).then(() => {
        const btn = document.querySelector('.btn-outline-primary');
        const originalHtml = btn.innerHTML;
        btn.innerHTML = '<i class="bi bi-check"></i> Copiado';
        btn.classList.replace('btn-outline-primary', 'btn-success');
        setTimeout(() => {
            btn.innerHTML = originalHtml;
            btn.classList.replace('btn-success', 'btn-outline-primary');
        }, 2000);
    });
}

document.addEventListener('DOMContentLoaded', function() {
    const MAX_SIZE = 10 * 1024 * 1024; // 10 MB

    // ==========================================
    // 1. LÓGICA: GENERAR HASH (Archivo O Texto)
    // ==========================================
    const genBtn = document.querySelector('button[name="generate"]');
    if (genBtn) {
        const form = genBtn.closest('form');
        const fileInput = form.querySelector('input[type="file"]');
        const textInput = form.querySelector('textarea') || form.querySelector('input[type="text"]:not([hidden])');
        const originalPlaceholder = textInput ? textInput.placeholder : '';

        function updateGenForm() {
            const hasFile = fileInput && fileInput.files.length > 0;
            const hasText = textInput && textInput.value.trim().length > 0;
            let isFileTooBig = false;

            // Validación de tamaño
            if (hasFile) {
                if (fileInput.files[0].size > MAX_SIZE) {
                    isFileTooBig = true;
                    showError(fileInput, `El archivo supera el límite de 10 MB.`);
                } else {
                    clearError(fileInput);
                }
            } else {
                clearError(fileInput);
            }

            // Exclusión Mutua
            if (hasFile) {
                if (textInput) {
                    textInput.disabled = true;
                    textInput.value = '';
                    textInput.placeholder = "Modo Archivo activo (Texto deshabilitado)";
                }
            } else if (hasText) {
                if (fileInput) {
                    fileInput.disabled = true;
                    fileInput.value = '';
                }
            } else {
                if (textInput) {
                    textInput.disabled = false;
                    textInput.placeholder = originalPlaceholder;
                }
                if (fileInput) fileInput.disabled = false;
            }

            // Botón
            if ((hasFile && !isFileTooBig) || hasText) {
                genBtn.disabled = false;
            } else {
                genBtn.disabled = true;
            }
        }

        if (fileInput) {
            fileInput.addEventListener('change', updateGenForm);
            fileInput.addEventListener('click', () => { if(fileInput.value) updateGenForm(); });
        }
        if (textInput) {
            ['input', 'paste', 'change', 'keyup'].forEach(evt => textInput.addEventListener(evt, updateGenForm));
        }
        updateGenForm();
    }

    // ==========================================
    // 2. LÓGICA: VERIFICAR INTEGRIDAD
    //    ( (Archivo O Texto) Y Hash )
    // ==========================================
    const verifyForm = document.querySelector('form[action*="verify"]');
    
    if (verifyForm) {
        const vBtn = verifyForm.querySelector('button[type="submit"]');
        const vFile = verifyForm.querySelector('input[type="file"]');
        
        // INTENTA IDENTIFICAR LOS CAMPOS POR TIPO O NOMBRE
        // vTextContent: El campo donde pegan el texto a analizar (textarea o input 'text_content')
        // vHashTarget: El campo donde pegan el hash para comparar (input 'hash' o 'target_hash')
        
        // ESTRATEGIA: Buscamos textarea para contenido. Si no hay, asumimos input[text].
        // AJUSTA ESTOS SELECTORES SI TUS CAMPOS SE LLAMAN DIFERENTE EN DJANGO
        const vTextContent = verifyForm.querySelector('textarea') || verifyForm.querySelector('input[name="text"]'); 
        
        // El hash suele ser un input type="text". Buscamos uno que NO sea el de contenido.
        let vHashTarget = verifyForm.querySelector('input[name="hash"]');
        if (!vHashTarget) {
            // Fallback: buscar cualquier input text que no sea el vTextContent
            const allTexts = verifyForm.querySelectorAll('input[type="text"]');
            allTexts.forEach(input => {
                if (input !== vTextContent) vHashTarget = input;
            });
        }

        const vTextOriginalPlaceholder = vTextContent ? vTextContent.placeholder : '';

        function updateVerifyForm() {
            const hasFile = vFile && vFile.files.length > 0;
            const hasText = vTextContent && vTextContent.value.trim().length > 0;
            const hasHash = vHashTarget && vHashTarget.value.trim().length > 0;
            let isFileTooBig = false;

            // 1. Validar Tamaño Archivo
            if (hasFile) {
                if (vFile.files[0].size > MAX_SIZE) {
                    isFileTooBig = true;
                    showError(vFile, `El archivo supera el límite de 10 MB.`);
                } else {
                    clearError(vFile);
                }
            } else {
                clearError(vFile);
            }

            // 2. Exclusión Mutua (Archivo vs Texto de Contenido)
            // EL HASH (vHashTarget) SIEMPRE SE MANTIENE ACTIVO
            if (hasFile) {
                if (vTextContent) {
                    vTextContent.disabled = true;
                    vTextContent.value = '';
                    vTextContent.placeholder = "Verificando Archivo (Texto deshabilitado)";
                }
            } else if (hasText) {
                if (vFile) {
                    vFile.disabled = true;
                    vFile.value = '';
                }
            } else {
                // Reset
                if (vTextContent) {
                    vTextContent.disabled = false;
                    vTextContent.placeholder = vTextOriginalPlaceholder;
                }
                if (vFile) vFile.disabled = false;
            }

            // 3. Estado del Botón
            // Habilitar SI: ( (Tiene Archivo Válido) O (Tiene Texto) ) Y (Tiene Hash)
            const sourceValid = (hasFile && !isFileTooBig) || hasText;
            
            if (sourceValid && hasHash) {
                vBtn.disabled = false;
            } else {
                vBtn.disabled = true;
            }
        }

        // Listeners
        if (vFile) {
            vFile.addEventListener('change', updateVerifyForm);
            vFile.addEventListener('click', () => { if(vFile.value) updateVerifyForm(); });
        }
        if (vTextContent) {
            ['input', 'paste', 'change', 'keyup'].forEach(evt => vTextContent.addEventListener(evt, updateVerifyForm));
        }
        if (vHashTarget) {
            ['input', 'paste', 'change', 'keyup'].forEach(evt => vHashTarget.addEventListener(evt, updateVerifyForm));
        }

        // Init
        updateVerifyForm();
    }

    // ==========================================
    // UTILIDADES
    // ==========================================
    function showError(input, msg) {
        input.classList.add('is-invalid');
        let errDiv = input.parentElement.querySelector('.size-error');
        if (!errDiv) {
            errDiv = document.createElement('div');
            errDiv.className = 'invalid-feedback size-error';
            errDiv.style.display = 'block';
            input.parentElement.appendChild(errDiv);
        }
        errDiv.innerText = msg;
    }

    function clearError(input) {
        if (!input) return;
        input.classList.remove('is-invalid');
        const errDiv = input.parentElement.querySelector('.size-error');
        if (errDiv) errDiv.remove();
    }
});

// Copiar al portapapeles
function copyHash() {
    const hashInput = document.getElementById('hashResult');
    if (!hashInput) return;
    hashInput.select();
    hashInput.setSelectionRange(0, 99999);
    navigator.clipboard.writeText(hashInput.value).then(() => {
        const btn = document.querySelector('.btn-outline-primary');
        if(btn) {
            const originalHtml = btn.innerHTML;
            btn.innerHTML = '<i class="bi bi-check"></i> Copiado';
            btn.classList.replace('btn-outline-primary', 'btn-success');
            setTimeout(() => {
                btn.innerHTML = originalHtml;
                btn.classList.replace('btn-success', 'btn-outline-primary');
            }, 2000);
        }
    });
}