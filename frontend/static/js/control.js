// control.js

const backendUrl = '/api/v1/data';

// --- NEW ASYNCHRONOUS PDF EXTRACTION LOGIC ---

/**
 * Polls the backend to check the status of a task.
 * @param {string} taskId - The ID of the task to check.
 * @param {HTMLElement} statusEl - The element to display status messages.
 * @param {HTMLElement} containerEl - The container to append the download button to.
 */
const pollTaskStatus = async (taskId, statusEl, containerEl) => {
    try {
        const response = await fetch(`${backendUrl}/status/${taskId}`);
        if (!response.ok) {
            throw new Error(`Status check failed: ${response.statusText}`);
        }
        const data = await response.json();

        if (data.status === 'processing') {
            // If still processing, wait 3 seconds and poll again
            statusEl.textContent = 'Processing... This may take several minutes. Please wait.';
            setTimeout(() => pollTaskStatus(taskId, statusEl, containerEl), 3000);
        } else if (data.status === 'completed') {
            // If completed, fetch the final result
            statusEl.textContent = 'Processing complete! Fetching your file...';
            await fetchTaskResult(taskId, statusEl, containerEl);
        } else if (data.status === 'failed') {
            // If failed, show an error message
            throw new Error(data.error || 'The task failed for an unknown reason.');
        }
    } catch (error) {
        statusEl.textContent = `Error: ${error.message}`;
        statusEl.className = 'mt-1 text-xs text-red-600';
    }
};

/**
 * Fetches the final result of a completed task and creates a download button.
 * @param {string} taskId - The ID of the completed task.
 * @param {HTMLElement} statusEl - The element to display status messages.
 * @param {HTMLElement} containerEl - The container to append the download button to.
 */
const fetchTaskResult = async (taskId, statusEl, containerEl) => {
    try {
        const response = await fetch(`${backendUrl}/result/${taskId}`);
        if (!response.ok) {
            throw new Error(`Failed to download file: ${response.statusText}`);
        }

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
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            downloadBtn.remove();
        };

        statusEl.textContent = 'Extraction successful!';
        statusEl.className = 'mt-1 text-xs text-green-600';
        containerEl.appendChild(downloadBtn);
    } catch (error) {
        statusEl.textContent = `Error: ${error.message}`;
        statusEl.className = 'mt-1 text-xs text-red-600';
    }
};

document.getElementById('extract-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const status = document.getElementById('extract-status');
    const container = document.getElementById('extract-form').parentElement;

    // Remove any existing download button
    const existingBtn = container.querySelector('.download-btn');
    if (existingBtn) existingBtn.remove();

    status.textContent = 'Uploading file...';
    status.className = 'mt-1 text-xs text-slate-600';

    const formData = new FormData();
    const pdfFile = document.getElementById('pdf-file').files[0];
    if (!pdfFile) {
        status.textContent = 'Error: Please select a PDF file.';
        status.className = 'mt-1 text-xs text-red-600';
        return;
    }
    formData.append('pdf_file', pdfFile);

    try {
        // 1. Start the task
        const response = await fetch(`${backendUrl}/extract`, {
            method: 'POST',
            body: formData
        });
        if (!response.ok) {
            throw new Error(`Upload failed: ${response.statusText}`);
        }
        const data = await response.json();

        // 2. Start polling for the status using the received task_id
        pollTaskStatus(data.task_id, status, container);

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