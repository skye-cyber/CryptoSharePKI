// generate-icons.js
const fs = require('fs');
const path = require('path');
const { library, icon } = require('@fortawesome/fontawesome-svg-core');
const { faFileVideo, faFileAudio, faFile, faFileImage, faFolder } = require('@fortawesome/free-solid-svg-icons');

// Add the specific icons to the library
library.add(faFileVideo, faFileAudio, faFile, faFileImage, faFolder);

// Function to generate SVG icons
function generateSVGs() {
    const outputDir = path.join(__dirname, 'static', 'icons');

    // Create the output directory if it doesn't exist
    fs.mkdirSync(outputDir, { recursive: true });

    // Define the icons to be generated
    const icons = {
        'file-video': faFileVideo,
        'file-audio': faFileAudio,
        'file': faFile,
        'file-image': faFileImage,
        'folder': faFolder
    };

    // Generate SVG files for each icon
    for (const [name, iconData] of Object.entries(icons)) {
        // Create SVG content using FontAwesome's icon API
        const svgContent = icon(iconData).html[0]; // Get the SVG HTML string

        // Construct the file path for the SVG file
        const svgFileName = path.join(outputDir, `${name}.svg`);

        // Write the SVG content to the file
        fs.writeFileSync(svgFileName, svgContent);
    }

    console.log('SVG icons generated successfully in:', outputDir);
}

// Generate the SVG icons
generateSVGs();
