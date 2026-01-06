
document.addEventListener('DOMContentLoaded', function() {
// 1. Funcionalidad de Búsqueda
const searchInput = document.getElementById('metadataSearch');
const table = document.getElementById('metadataTable');

if (searchInput && table) {
    searchInput.addEventListener('keyup', function() {
        const filter = searchInput.value.toLowerCase();
        const rows = table.getElementsByTagName('tr');

        for (let i = 1; i < rows.length; i++) { // Empezar en 1 para saltar el header
            const keyCol = rows[i].getElementsByTagName('td')[0];
            const valCol = rows[i].getElementsByTagName('td')[1];
            
            if (keyCol && valCol) {
                const keyText = keyCol.textContent || keyCol.innerText;
                const valText = valCol.textContent || valCol.innerText;

                if (keyText.toLowerCase().indexOf(filter) > -1 || valText.toLowerCase().indexOf(filter) > -1) {
                    rows[i].style.display = "";
                } else {
                    rows[i].style.display = "none";
                }
            }
        }
    });
}

// 2. Funcionalidad de Copiar al Portapapeles
const copyBtns = document.querySelectorAll('.copy-btn');
copyBtns.forEach(btn => {
    btn.addEventListener('click', function() {
        const textToCopy = this.getAttribute('data-value');
        
        navigator.clipboard.writeText(textToCopy).then(() => {
            // Feedback visual temporal
            const originalIcon = this.innerHTML;
            this.innerHTML = '<i class="bi bi-check2 text-success"></i>';
            this.classList.remove('text-secondary');
            
            setTimeout(() => {
                this.innerHTML = originalIcon;
                this.classList.add('text-secondary');
            }, 1500);
        }).catch(err => {
            console.error('Error al copiar: ', err);
        });
    });
});
});