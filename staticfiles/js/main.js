// ========================================
// OSINT Hub - JavaScript Principal
// ========================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('OSINT Hub JS cargado correctamente');
    
    // ========================================
    // CAMBIO DE TEMA CLARO/OSCURO
    // ========================================
    const themeToggle = document.getElementById('theme-toggle');
    
    if (!themeToggle) {
        console.error('No se encontró el botón de tema');
        return;
    }
    
    const htmlElement = document.documentElement;
    const iconDark = themeToggle.querySelector('.theme-icon-dark');
    const iconLight = themeToggle.querySelector('.theme-icon-light');
    
    if (!iconDark || !iconLight) {
        console.error('No se encontraron los iconos de tema');
        return;
    }
    
    console.log('Botón de tema encontrado');
    
    // Obtener tema guardado o usar tema del sistema
    const getPreferredTheme = () => {
        const storedTheme = localStorage.getItem('theme');
        if (storedTheme) {
            return storedTheme;
        }
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    };
    
    // Aplicar tema
    const setTheme = (theme) => {
        console.log('Cambiando tema a:', theme);
        htmlElement.setAttribute('data-bs-theme', theme);
        document.body.setAttribute('data-bs-theme', theme);
        localStorage.setItem('theme', theme);
        
        // Cambiar icono
        if (theme === 'dark') {
            iconDark.classList.add('d-none');
            iconLight.classList.remove('d-none');
        } else {
            iconLight.classList.add('d-none');
            iconDark.classList.remove('d-none');
        }
        
        console.log('Tema aplicado:', theme);
    };
    
    // Inicializar tema
    setTheme(getPreferredTheme());
    
    // Toggle al hacer clic
    themeToggle.addEventListener('click', function(e) {
        e.preventDefault();
        console.log('Click en botón de tema detectado');
        
        const currentTheme = htmlElement.getAttribute('data-bs-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        
        console.log('Tema actual:', currentTheme, '-> Nuevo tema:', newTheme);
        
        // Agregar animación de rotación
        this.classList.add('rotating');
        setTimeout(() => {
            this.classList.remove('rotating');
        }, 500);
        
        setTheme(newTheme);
    });
    
    console.log('Event listener agregado al botón de tema');
    
    // Detectar cambios en preferencia del sistema
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
        if (!localStorage.getItem('theme')) {
            setTheme(e.matches ? 'dark' : 'light');
        }
    });
    
    // ========================================
    // AUTO-DISMISS ALERTS
    // ========================================
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000); // 5 segundos
    });
    
    // ========================================
    // SMOOTH SCROLL
    // ========================================
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // ========================================
    // ANIMACIÓN DE ENTRADA DE TARJETAS
    // ========================================
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    document.querySelectorAll('.card').forEach(card => {
        observer.observe(card);
    });
});