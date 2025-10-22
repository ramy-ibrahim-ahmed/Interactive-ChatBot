// control.js

const backendUrl = '/api/v1/data';

document.getElementById('extract-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const status = document.getElementById('extract-status');
    const container = document.getElementById('extract-form').parentElement;
    // Remove any existing download button
    const existingBtn = container.querySelector('.download-btn');
    if (existingBtn) existingBtn.remove();
    status.textContent = 'Processing...';
    status.className = 'mt-1 text-xs text-slate-600';
    const formData = new FormData();
    formData.append('pdf_file', document.getElementById('pdf-file').files[0]);
    try {
        const response = await fetch(`${backendUrl}/extract`, { method: 'POST', body: formData });
        if (!response.ok) throw new Error(`Error: ${response.statusText}`);
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const filename = response.headers.get('Content-Disposition')?.split('filename=')[1] || 'output.md';

        // Create download button
        const downloadBtn = document.createElement('button');
        downloadBtn.textContent = 'Download File';
        downloadBtn.className = 'download-btn bg-transparent border-2 border-green-500 hover:bg-green-100 hover:border-green-700 hover:text-green-700 text-green-500 font-bold py-1 px-3 rounded-md transition-all text-sm mt-2';
        downloadBtn.style.filter = 'url(#sketchy)';
        downloadBtn.onclick = () => {
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            a.click();
            URL.revokeObjectURL(url);
            // Optionally remove button after download
            downloadBtn.remove();
        };

        status.textContent = 'Extraction successful!';
        status.className = 'mt-1 text-xs text-green-600';
        container.appendChild(downloadBtn);
    } catch (error) {
        status.textContent = `Error: ${error.message}`;
        status.className = 'mt-1 text-xs text-red-600';
    }
});

document.getElementById('chunk-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const status = document.getElementById('chunk-status');
    const container = document.getElementById('chunk-form').parentElement;
    // Remove any existing download button
    const existingBtn = container.querySelector('.download-btn');
    if (existingBtn) existingBtn.remove();
    status.textContent = 'Processing...';
    status.className = 'mt-1 text-xs text-slate-600';
    const formData = new FormData();
    formData.append('md_file', document.getElementById('md-file').files[0]);
    const separator = document.getElementById('separator').value || '---#---';
    const boundaries = document.getElementById('boundaries').value;
    const numTocPages = document.getElementById('num-toc-pages').value;
    const collectionName = document.getElementById('collection-name-chunk').value;
    try {
        const response = await fetch(`${backendUrl}/chunk?separator=${encodeURIComponent(separator)}&boundaries=${encodeURIComponent(boundaries)}&num_toc_pages=${numTocPages}&collection_name=${encodeURIComponent(collectionName)}`, {
            method: 'POST',
            body: formData
        });
        if (!response.ok) throw new Error(`Error: ${response.statusText}`);
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const filename = response.headers.get('Content-Disposition')?.split('filename=')[1] || 'chunks.json';

        // Create download button
        const downloadBtn = document.createElement('button');
        downloadBtn.textContent = 'Download File';
        downloadBtn.className = 'download-btn bg-transparent border-2 border-green-500 hover:bg-green-100 hover:border-green-700 hover:text-green-700 text-green-500 font-bold py-1 px-3 rounded-md transition-all text-sm mt-2';
        downloadBtn.style.filter = 'url(#sketchy)';
        downloadBtn.onclick = () => {
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            a.click();
            URL.revokeObjectURL(url);
            // Optionally remove button after download
            downloadBtn.remove();
        };

        status.textContent = 'Chunking successful!';
        status.className = 'mt-1 text-xs text-green-600';
        container.appendChild(downloadBtn);
    } catch (error) {
        status.textContent = `Error: ${error.message}`;
        status.className = 'mt-1 text-xs text-red-600';
    }
});

document.getElementById('index-semantic-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const status = document.getElementById('index-semantic-status');
    status.textContent = 'Processing...';
    const formData = new FormData();
    formData.append('json_file', document.getElementById('json-file-semantic').files[0]);
    const collectionName = document.getElementById('collection-name-semantic').value;
    try {
        const response = await fetch(`${backendUrl}/index/semantic?collection_name=${encodeURIComponent(collectionName)}`, {
            method: 'POST',
            body: formData
        });
        if (!response.ok) throw new Error(`Error: ${response.statusText}`);
        const data = await response.json();
        status.textContent = data.message;
        status.className = 'mt-1 text-xs text-green-600';
    } catch (error) {
        status.textContent = `Error: ${error.message}`;
        status.className = 'mt-1 text-xs text-red-600';
    }
});

document.getElementById('index-lexical-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const status = document.getElementById('index-lexical-status');
    status.textContent = 'Processing...';
    const formData = new FormData();
    formData.append('json_file', document.getElementById('json-file-lexical').files[0]);
    const collectionName = document.getElementById('collection-name-lexical').value;
    try {
        const response = await fetch(`${backendUrl}/index/lexical?collection_name=${encodeURIComponent(collectionName)}`, {
            method: 'POST',
            body: formData
        });
        if (!response.ok) throw new Error(`Error: ${response.statusText}`);
        const data = await response.json();
        status.textContent = data.message;
        status.className = 'mt-1 text-xs text-green-600';
    } catch (error) {
        status.textContent = `Error: ${error.message}`;
        status.className = 'mt-1 text-xs text-red-600';
    }
});