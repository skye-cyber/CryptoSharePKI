// Handle dark mode switching
document.addEventListener("DOMContentLoaded", () => {
    const themeToggleButton = document.getElementById("theme-toggle");
    const sunIcon = document.getElementById("sun-icon");
    const moonIcon = document.getElementById("moon-icon");
    const rootElement = document.documentElement;

    // Initialize theme based on user's previous preference or system preference
    const userTheme = localStorage.getItem("theme");
    const systemTheme = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    const currentTheme = userTheme || systemTheme;

    // Set the initial theme
    setTheme(currentTheme);

    // Add click event listener to the theme toggle button
    themeToggleButton.addEventListener("click", () => {
        const newTheme = rootElement.classList.contains("dark") ? "light" : "dark";
        setTheme(newTheme);
    });

    // Function to set the theme
    function setTheme(theme) {
        if (theme === "dark") {
            rootElement.classList.add("dark");
            sunIcon.classList.add("hidden");
            moonIcon.classList.remove("hidden");
            //insight_section.classList.add("bg-dark-img");
            //insight_section.classList.remove("bg-light-img");
        } else {
            rootElement.classList.remove("dark");
            sunIcon.classList.remove("hidden");
            moonIcon.classList.add("hidden");
            //insight_section.classList.add("bg-light-img");
            //insight_section.classList.remove("bg-dark-img");
        }
        localStorage.setItem("theme", theme);
    }

    //implement view swithcing
    const toggleButton = document.querySelector('#toggleView');
    const fileContainer = document.querySelector('#fileContainer');
    const fileItems = document.querySelectorAll('.file-item');

    toggleButton.addEventListener('click', function() {
        if (fileContainer.classList.contains('grid')) {
            fileContainer.classList.remove('grid');
            fileContainer.classList.add('block');
            toggleButton.textContent = 'Grid View';
            fileItems.forEach(item => {
                item.classList.add('my-2');
            });
        } else {
            fileContainer.classList.remove('block');
            fileContainer.classList.add('grid');
            toggleButton.textContent = 'List View';
            fileItems.forEach(item => {
                item.classList.remove('my-2');
            });
        }
    });

});

