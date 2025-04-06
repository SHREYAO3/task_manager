// Theme management
document.addEventListener('DOMContentLoaded', function() {
    // Look for both types of theme toggle buttons
    const darkModeToggle = document.getElementById('darkModeToggle');
    const themeToggle = document.getElementById('themeToggle');
    const body = document.body;


    // Function to update theme
    function updateTheme(isDark) {
        if (isDark) {
            body.classList.add('dark-theme');
            body.classList.add('dark-mode'); // For compatibility with both class names
        } else {
            body.classList.remove('dark-theme');
            body.classList.remove('dark-mode');
        }


        // Update icons in both nav and sidebar
        const toggleButtons = [darkModeToggle, themeToggle].filter(Boolean);
        toggleButtons.forEach(button => {
            if (button) {
                const icon = button.querySelector('i');
                if (icon) {
                    if (isDark) {
                        icon.classList.remove('fa-moon');
                        icon.classList.add('fa-sun');
                    } else {
                        icon.classList.remove('fa-sun');
                        icon.classList.add('fa-moon');
                    }
                }
            }
        });
    }


    // Check for saved theme preference
    const isDark = localStorage.getItem('theme') === 'dark';
    updateTheme(isDark);


    // Listen for theme changes from any toggle button
    const toggleButtons = [darkModeToggle, themeToggle].filter(Boolean);
    toggleButtons.forEach(button => {
        if (button) {
            button.addEventListener('click', () => {
                const isDark = !body.classList.contains('dark-theme');
                localStorage.setItem('theme', isDark ? 'dark' : 'light');
                updateTheme(isDark);
            });
        }
    });


    // Listen for storage changes (sync across tabs/windows)
    window.addEventListener('storage', (e) => {
        if (e.key === 'theme') {
            updateTheme(e.newValue === 'dark');
        }
    });
});