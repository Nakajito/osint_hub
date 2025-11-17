document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('emailSearchForm');
    const emailInput = document.getElementById('email');
    
    // Validación adicional en el frontend
    form.addEventListener('submit', function(e) {
        const email = emailInput.value.trim();
        
        if (!email) {
            e.preventDefault();
            alert('Por favor, ingresa un correo electrónico');
            emailInput.focus();
            return false;
        }
        
        // Validación básica de formato de email
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            e.preventDefault();
            alert('Por favor, ingresa un correo electrónico válido');
            emailInput.focus();
            return false;
        }
        
        // Mostrar indicador de carga
        const submitBtn = form.querySelector('button[type="submit"]');
        submitBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Buscando...';
        submitBtn.disabled = true;
    });
});