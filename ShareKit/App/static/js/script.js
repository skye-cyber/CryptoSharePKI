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


    const openModalButton = document.getElementById('openUploadModal');
    const closeModalButton = document.getElementById('closeModal');
    const uploadModal = document.getElementById('uploadModal');
    const modalContent = document.getElementById('modalContent');
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const uploadForm = document.getElementById('uploadForm');

    openModalButton.addEventListener('click', () => {
        uploadModal.classList.remove('hidden');
        setTimeout(() => {
            modalContent.classList.remove('scale-95');
            modalContent.classList.add('scale-100');
        }, 10);
    });

    closeModalButton.addEventListener('click', () => {
        modalContent.classList.remove('scale-100');
        modalContent.classList.add('scale-95');
        setTimeout(() => {
            uploadModal.classList.add('hidden');
        }, 300);
    });

    dropZone.addEventListener('click', () => {
        fileInput.click();
    });

    fileInput.addEventListener('change', (event) => {
        const file = event.target.files[0];
        if (file) {
            uploadForm.file.files = event.target.files;
        }
    });

    dropZone.addEventListener('dragover', (event) => {
        event.preventDefault();
        dropZone.classList.add('border-blue-600', 'dark:border-cyan-600');
        dropZone.classList.remove('border-blue-400', 'dark:border-cyan-400');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('border-blue-600', 'dark:border-cyan-600');
        dropZone.classList.add('border-blue-400', 'dark:border-cyan-400');
    });

    dropZone.addEventListener('drop', (event) => {
        event.preventDefault();
        dropZone.classList.remove('border-blue-600', 'dark:border-cyan-600');
        dropZone.classList.add('border-blue-400', 'dark:border-cyan-400');
        const files = event.dataTransfer.files;
        if (files.length > 0) {
            uploadForm.file.files = files;
        }
});

const menu_bt = document.getElementById('menu')
menu_bt.addEventListener('click', () =>{
     HandleMenu();
})

document.getElementById('closeMenuModal').addEventListener('click', () =>{
    HandleMenu();
})

function HandleMenu() {
    const menu_modal = document.getElementById('menu_modal')
    menu_modal.classList.toggle('-translate-x-full');
    menu_modal.classList.toggle('-translate-x-1')
}

const search_bar = document.getElementById('search_bar');
function setSearchContent(){
    search_bar.value = document.URL
}
setSearchContent();
/*
 search_bar.addEventListener('keydown', function(event){
    if (event.key === "Enter" && !event.shiftKey){
        console.log("keydown")
        const response = fetch(search_bar.value, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
        });
    }
})
*/
const items = document.querySelectorAll('#shared-item-text');

items.forEach(item => {
    const maxLength = 6;
    let text = item.textContent.trim(); // Ensure proper text extraction

    const parts = text.split(".");
    let formattedText;

    if (parts.length < 2) {
        formattedText = text; // No extension found, keep as is
    } else {
        const extension = parts.pop(); // Extract the file extension
        let name = parts.join("."); // Join the remaining parts as the name

        if (name.length > maxLength) {
            name = name.slice(0, maxLength) + "..."; // Truncate and add ellipsis
        }

        formattedText = `${name}.${extension}`; // Reconstruct the file name
    }

    item.textContent = formattedText; // Update the DOM element
});

// Global variable to store the selected device
var selectedDevice = "";

// When the page loads, attach click listeners to device elements
    // Assume each device is rendered with the class 'device-item'
    const deviceItems = document.querySelectorAll('.device-item');
    deviceItems.forEach(function(item) {
        item.addEventListener('click', function() {
            // Get the device IP from a data attribute
            selectedDevice = this.getAttribute('data-device');
            console.log("Selected device:", selectedDevice);
            // Optionally update download links immediately after selection
            updateDownloadLinks();
            updateViewLinks();
        });
    });

});

updateDownloadLinks()
// Function to update all download links with the selected device
function updateDownloadLinks() {
    const downloadLinks = document.getElementById('access-link-download');
    downloadLinks.forEach(function(link) {
        const filename = link.getAttribute('data-filename')
        console.log(filename);
        // Construct the URL for the download route using the selected device
        // For example: /download/192.168.1.103/filename.ext
        link.href = "/download/" + selectedDevice + "/" + filename;
    });
}


// Function to update all download links with the selected device
function updateViewLinks() {
    const downloadLinks = document.getElementById('access-link-view');
    downloadLinks.forEach(function(link) {
        const dir = link.getAttribute('data-dir')
        console.log(dir);
        // Construct the URL for the download route using the selected device
        // For example: /download/192.168.1.103/filename.ext
        link.href = "/view/" + selectedDevice + "/" + dir;
    });
}
