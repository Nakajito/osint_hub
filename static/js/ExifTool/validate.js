document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('file');
    const submitBtn = document.getElementById('submitBtn');
    const errorDiv = document.getElementById('fileError');
    const MAX_SIZE = 10 * 1024 * 1024; // 10 MB en bytes

    fileInput.addEventListener('change', function() {
        // Reiniciar estados visuales
        fileInput.classList.remove('is-invalid');
        errorDiv.style.display = 'none';
        submitBtn.disabled = false;

        if (this.files && this.files[0]) {
            const fileSize = this.files[0].size;

            if (fileSize > MAX_SIZE) {
                // El archivo es muy grande
                const sizeInMB = (fileSize / (1024 * 1024)).toFixed(2);
                
                fileInput.classList.add('is-invalid'); // Pone el borde rojo estilo Bootstrap
                errorDiv.textContent = `⚠️ El archivo pesa ${sizeInMB} MB. El límite permitido es 10 MB.`;
                errorDiv.style.display = 'block';
                
                // Desactivar botón de envío
                submitBtn.disabled = true;
                
                // Opcional: Limpiar el input para obligar a re-seleccionar
                this.value = ''; 
            }
        }
    });
});