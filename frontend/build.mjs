import fs from 'fs';
import path from 'path';

const projectDir = path.dirname(new URL(import.meta.url).pathname).replace(/^\/(\w):/, '$1:');
const distDir = path.join(projectDir, 'dist');

// Ensure dist directory exists
if (!fs.existsSync(distDir)) {
    fs.mkdirSync(distDir, { recursive: true });
}

// Files to copy directly
const filesToCopy = ['index.html', 'dashboard.html', 'pipeline.html', 'styles.css', 'app.js', 'demo-data.js'];

filesToCopy.forEach(file => {
    fs.copyFileSync(
        path.join(projectDir, file),
        path.join(distDir, file)
    );
});

// Generate config.js from template and environment variables
const template = fs.readFileSync(path.join(projectDir, 'config.template.js'), 'utf8');
const apiUrl = process.env.API_BASE_URL || '';
const configContent = template.replace('${API_BASE_URL}', apiUrl);

fs.writeFileSync(path.join(distDir, 'config.js'), configContent);

console.log('Build complete. Output in dist/');
