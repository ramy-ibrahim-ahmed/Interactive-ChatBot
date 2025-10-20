// DOM Elements (no changes here)
const chatContainer = document.getElementById('chat-container');
const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const personaStatus = document.getElementById('persona-status');
const eyes = document.getElementById('eyes');
const mouth = document.getElementById('mouth');
const sendButton = document.getElementById('send-button');
const micButton = document.getElementById('mic-button');
const providerButton = document.getElementById('provider-button');
const providerMenu = document.getElementById('provider-menu');

// Add this at the top of the script, after the DOM elements
let sessionId = localStorage.getItem('chat_session_id');
if (!sessionId) {
    sessionId = crypto.randomUUID();
    localStorage.setItem('chat_session_id', sessionId);
}

// Custom provider selection logic
let selectedProvider = 'gemini'; // Default
providerButton.addEventListener('click', () => {
    providerMenu.classList.toggle('hidden');
});
providerMenu.addEventListener('click', (e) => {
    if (e.target.tagName === 'LI') {
        selectedProvider = e.target.dataset.value;
        providerButton.textContent = e.target.textContent;
        providerMenu.classList.add('hidden');
    }
});

// Handle Enter to send and Shift+Enter for new line
chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault(); // Prevent default new line
        chatForm.dispatchEvent(new Event('submit')); // Trigger form submit
    }
    // If Shift+Enter, do nothing—allow default new line
});

// Chat state & other variables (no changes here)
let isLoading = false;
let isRecording = false;
let mediaRecorder;
let audioChunks = [];
let lastUserMessage;
let isAudioInput = false;
const backendUrl = '/api/v1/chat';
const ttsUrl = '/api/v1/chat/tts';

// Helper functions and persona states
function isRTL(text) {
    const rtlChars = /[\u0590-\u05FF\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]/;
    return rtlChars.test(text);
}
let blinkInterval;
const personaStates = {
    idle: {
        mouth: '<path d="M 80 125 Q 100 140 120 125" stroke="#34d399" stroke-width="4" fill="none" stroke-linecap="round" />',
        eyesOpen: '<circle id="left-eye" cx="80" cy="80" r="8" fill="#34d399" /><circle id="right-eye" cx="120" cy="80" r="8" fill="#34d399" />',
        eyesClosed: '<path d="M 70 80 H 90" stroke="#34d399" stroke-width="4" fill="none" stroke-linecap="round" /><path d="M 110 80 H 130" stroke="#34d399" stroke-width="4" fill="none" stroke-linecap="round" />',
        status: 'متصل',
        statusColor: 'text-emerald-400'
    },
    thinking: {
        mouth: '<path d="M 80 130 H 120" stroke="#f59e0b" stroke-width="4" fill="none" stroke-linecap="round" />',
        eyes: '<circle id="left-eye" cx="80" cy="75" r="8" fill="#f59e0b" /><circle id="right-eye" cx="120" cy="75" r="8" fill="#f59e0b" />',
        // --- ENHANCEMENT 3: Updated fallback thinking status ---
        status: 'جاري المعالجة...',
        statusColor: 'text-amber-400'
    },
    talking: {
        mouth: [
            '<path d="M 80 125 Q 100 130 120 125" stroke="#60a5fa" stroke-width="4" fill="none" stroke-linecap="round" />',
            '<path d="M 80 125 Q 100 135 120 125" stroke="#60a5fa" stroke-width="4" fill="none" stroke-linecap="round" />',
            '<path d="M 80 125 Q 100 140 120 125" stroke="#60a5fa" stroke-width="4" fill="none" stroke-linecap="round" />'
        ],
        eyes: '<circle id="left-eye" cx="80" cy="80" r="9" fill="#60a5fa" /><circle id="right-eye" cx="120" cy="80" r="9" fill="#60a5fa" />',
        status: 'يرد...',
        statusColor: 'text-blue-400'
    },
    error: {
        mouth: '<path d="M 80 135 Q 100 120 120 135" stroke="#f43f5e" stroke-width="4" fill="none" stroke-linecap="round" />',
        eyes: '<path d="M 72 72 L 88 88 M 88 72 L 72 88" stroke="#f43f5e" stroke-width="4" fill="none" stroke-linecap="round" /><path d="M 112 72 L 128 88 M 128 72 L 112 88" stroke="#f43f5e" stroke-width="4" fill="none" stroke-linecap="round" />',
        status: 'خطأ',
        statusColor: 'text-red-500'
    }
};
let talkInterval;
function setPersonaState(state) {
    clearInterval(blinkInterval);
    clearInterval(talkInterval);
    const s = personaStates[state];

    personaStatus.textContent = s.status;
    personaStatus.className = `font-medium ${s.statusColor}`;

    switch (state) {
        case 'idle':
            mouth.innerHTML = s.mouth;
            eyes.innerHTML = s.eyesOpen;
            blinkInterval = setInterval(() => {
                eyes.innerHTML = s.eyesClosed;
                setTimeout(() => {
                    if (personaStatus.textContent === 'متصل') {
                        eyes.innerHTML = s.eyesOpen;
                    }
                }, 200);
            }, 4000);
            break;
        case 'thinking':
            mouth.innerHTML = s.mouth;
            eyes.innerHTML = s.eyes;
            break;
        case 'talking':
            eyes.innerHTML = s.eyes;
            let mouthIndex = 0;
            talkInterval = setInterval(() => {
                mouth.innerHTML = s.mouth[mouthIndex];
                mouthIndex = (mouthIndex + 1) % s.mouth.length;
            }, 150);
            break;
        case 'error':
            mouth.innerHTML = s.mouth;
            eyes.innerHTML = s.eyes;
            break;
    }
}

function addAudioPlayer(messageElement, audioUrl) {
    const audioContainer = document.createElement('div');
    audioContainer.classList.add('mt-2', 'flex', 'flex-wrap', 'items-center', 'gap-2', 'justify-end', 'dir-rtl'); // RTL for Arabic labels

    const audio = document.createElement('audio');
    audio.src = audioUrl;
    audio.preload = 'metadata'; // Load metadata for duration

    // Play/Pause Button
    const playPauseButton = document.createElement('button');
    playPauseButton.classList.add('flex', 'items-center', 'gap-1', 'text-blue-500', 'bg-transparent', 'border-2', 'border-blue-500', 'hover:bg-blue-100', 'hover:border-blue-600', 'hover:text-blue-600', 'px-3', 'py-1', 'rounded-lg', 'transition-colors', 'font-medium', 'text-sm');
    playPauseButton.style.filter = 'url(#sketchy)';

    const playIcon = `
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polygon points="5 3 19 12 5 21 5 3"></polygon>
    </svg>
    تشغيل
`;
    const pauseIcon = `
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <rect x="6" y="4" width="4" height="16"></rect>
        <rect x="14" y="4" width="4" height="16"></rect>
    </svg>
    إيقاف
`;
    playPauseButton.innerHTML = playIcon;

    playPauseButton.onclick = () => {
        if (audio.paused) {
            audio.play().catch(e => console.error('Playback error:', e));
        } else {
            audio.pause();
        }
    };

    // Progress Bar
    const progressContainer = document.createElement('div');
    progressContainer.classList.add('flex', 'items-center', 'gap-2', 'w-48', 'md:w-64');

    const progress = document.createElement('input');
    progress.type = 'range';
    progress.min = 0;
    progress.max = 100;
    progress.value = 0;
    progress.classList.add('flex-1', 'h-2', 'bg-slate-200', 'rounded-lg', 'cursor-pointer', 'accent-blue-500');
    progress.style.filter = 'url(#sketchy)';

    const timeDisplay = document.createElement('span');
    timeDisplay.classList.add('text-xs', 'text-slate-600', 'font-medium');
    timeDisplay.textContent = '0:00 / 0:00';

    // Update progress and time
    audio.ontimeupdate = () => {
        const percent = (audio.currentTime / audio.duration) * 100;
        progress.value = percent || 0;
        const current = formatTime(audio.currentTime);
        const duration = formatTime(audio.duration);
        timeDisplay.textContent = `${current} / ${duration}`;
    };

    progress.oninput = () => {
        const time = (progress.value / 100) * audio.duration;
        audio.currentTime = time;
    };

    progressContainer.appendChild(progress);
    progressContainer.appendChild(timeDisplay);

    // Volume Slider
    const volumeContainer = document.createElement('div');
    volumeContainer.classList.add('flex', 'items-center', 'gap-1');

    const volumeIcon = document.createElement('svg');
    volumeIcon.innerHTML = `
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="blue-500" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
        <path d="M15.54 8.46a5 5 0 0 1 0 7.07"></path>
    </svg>
`;

    const volume = document.createElement('input');
    volume.type = 'range';
    volume.min = 0;
    volume.max = 100;
    volume.value = 100;
    volume.classList.add('w-20', 'h-2', 'bg-slate-200', 'rounded-lg', 'cursor-pointer', 'accent-blue-500');
    volume.style.filter = 'url(#sketchy)';

    volume.oninput = () => {
        audio.volume = volume.value / 100;
    };

    volumeContainer.appendChild(volumeIcon);
    volumeContainer.appendChild(volume);

    // Playback Speed Dropdown
    const speedContainer = document.createElement('div');
    speedContainer.classList.add('flex', 'items-center', 'gap-1');

    const speedLabel = document.createElement('span');
    speedLabel.textContent = 'سرعة:';
    speedLabel.classList.add('text-xs', 'text-blue-500', 'font-medium');

    const speedSelect = document.createElement('select');
    speedSelect.classList.add('bg-transparent', 'border-2', 'border-blue-500', 'text-blue-500', 'px-2', 'py-1', 'rounded-lg', 'text-sm', 'font-medium', 'hover:bg-blue-100', 'hover:border-blue-600', 'hover:text-blue-600', 'transition-colors');
    speedSelect.style.filter = 'url(#sketchy)';

    const speeds = [0.5, 0.75, 1, 1.25, 1.5, 1.75, 2];
    speeds.forEach(rate => {
        const option = document.createElement('option');
        option.value = rate;
        option.textContent = `${rate}x`;
        if (rate === 1) option.selected = true;
        speedSelect.appendChild(option);
    });

    speedSelect.onchange = () => {
        audio.playbackRate = parseFloat(speedSelect.value);
    };

    speedContainer.appendChild(speedLabel);
    speedContainer.appendChild(speedSelect);

    // Audio event handlers (unchanged from your code)
    audio.onplay = () => {
        setPersonaState('talking');
        playPauseButton.innerHTML = pauseIcon;
    };
    audio.onpause = () => {
        setPersonaState('idle');
        playPauseButton.innerHTML = playIcon;
    };
    audio.onended = () => {
        setPersonaState('idle');
        playPauseButton.innerHTML = playIcon;
        progress.value = 0;
    };
    audio.onerror = () => {
        setPersonaState('idle');
        playPauseButton.innerHTML = playIcon;
    };
    audio.onloadedmetadata = () => {
        timeDisplay.textContent = `0:00 / ${formatTime(audio.duration)}`;
    };

    // Helper to format time (e.g., 0:00)
    function formatTime(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
    }

    // Append all to container
    audioContainer.appendChild(playPauseButton);
    audioContainer.appendChild(progressContainer);
    audioContainer.appendChild(volumeContainer);
    audioContainer.appendChild(speedContainer);

    messageElement.appendChild(audioContainer);
}

function addGenerateTTSButton(messageElement) {
    const generateButton = document.createElement('button');
    generateButton.classList.add('mt-2', 'flex', 'items-center', 'gap-1', 'text-blue-500', 'bg-transparent', 'border-2', 'border-blue-500', 'hover:bg-blue-100', 'hover:border-blue-600', 'hover:text-blue-600', 'px-3', 'py-1', 'rounded-lg', 'transition-colors', 'font-medium', 'text-sm');
    generateButton.style.filter = 'url(#sketchy)';
    generateButton.innerHTML = `
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
        <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path>
    </svg>
    استمع إلى الرد
`;
    generateButton.onclick = async () => {
        const text = messageElement.dataset.originalText;
        if (!text) return;
        try {
            generateButton.disabled = true;
            generateButton.innerHTML = `<span class="animate-pulse">جاري التوليد...</span>`;
            const formData = new FormData();
            formData.append('text', text);
            const res = await fetch(ttsUrl, { method: 'POST', body: formData });
            if (!res.ok) throw new Error('TTS failed');
            const data = await res.json();
            addAudioPlayer(messageElement, data.audio_path);
            generateButton.remove();
        } catch (e) {
            console.error('TTS error:', e);
            alert('فشل في توليد الصوت.');
            generateButton.disabled = false;
            generateButton.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
                <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path>
            </svg>
            استمع إلى الرد
        `;
        }
    };
    messageElement.appendChild(generateButton);
}

function addTTSControl(messageElement) {
    if (messageElement.dataset.audioPath) {
        addAudioPlayer(messageElement, messageElement.dataset.audioPath);
    } else {
        addGenerateTTSButton(messageElement);
    }
}

function addMessageToChat(sender, message, returnElement = false) {
    const messageWrapper = document.createElement('div');
    messageWrapper.classList.add('mb-4', 'w-full', 'animate__animated', 'animate__fadeIn');
    messageWrapper.classList.add('flex', sender === 'user' ? 'justify-end' : 'justify-start');

    const messageElement = document.createElement('div');
    messageElement.classList.add('px-4', 'py-3', 'break-words', 'rounded-lg', 'shadow-md');

    if (sender === 'bot') {
        messageElement.dataset.originalText = message;
        if (message === '...') {
            messageElement.innerHTML = '<span class="blinking-cursor"></span>';
        } else {
            messageElement.innerHTML = marked.parse(message);
        }
        messageElement.classList.add('bg-slate-200', 'text-slate-800');

        // --- 1. ADD THESE TWO LINES ---
        // This forces the bot's text to always be Right-to-Left.
        messageElement.dir = 'rtl';
        messageElement.classList.add('text-right');

        // New: Make bot messages full width for better markdown support
        messageElement.classList.add('w-full');
    } else { // This block is for the 'user'
        messageElement.textContent = message;
        messageElement.classList.add('chat-bubble-user');
        messageElement.classList.add('max-w-xs', 'lg:max-w-md'); // Keep limited width for user bubbles

        // We keep the smart detection for the user's messages
        if (isRTL(messageElement.textContent.trim())) {
            messageElement.dir = 'rtl';
            messageElement.classList.add('text-right');
        } else {
            messageElement.dir = 'ltr';
            messageElement.classList.add('text-left');
        }
    }

    messageWrapper.appendChild(messageElement);
    chatContainer.appendChild(messageWrapper);
    chatContainer.scrollTop = chatContainer.scrollHeight;

    if (returnElement) {
        return messageElement;
    }

    if (sender === 'user') {
        lastUserMessage = messageElement;
    }
    return messageElement;
}
function updateLastUserMessage(text) {
    if (lastUserMessage) {
        lastUserMessage.textContent = text;
        if (isRTL(text)) {
            lastUserMessage.dir = 'rtl';
            lastUserMessage.classList.remove('text-left');
            lastUserMessage.classList.add('text-right');
        } else {
            lastUserMessage.dir = 'ltr';
            lastUserMessage.classList.remove('text-right');
            lastUserMessage.classList.add('text-left');
        }
    }
};

// --- ENHANCEMENT 3: Rewritten to update persona status directly ---
let partialResponse = '';
function handleStreamEvent(data, botMessageElement) {
    const event = data.event;

    if (event === 'transcribed') {
        // Update the user message with the transcribed text immediately
        if (isAudioInput && data.data.user_message) {
            updateLastUserMessage(data.data.user_message);
        }
        return;  // Exit early, as this is just for transcription display
    }

    if (event === 'start_node') {
        setPersonaState('thinking'); // Sets the thinking face, color, and fallback text
        const node = data.node;
        let statusText;

        switch (node) {
            case '__classify__': statusText = '...فهم الطلب🤔'; break;
            case '__queries__': statusText = '...تحسين الاستفسار✍️'; break;
            case '__semantic__': statusText = '...تحديد النظام🥱'; break;
            case '__search__': statusText = '...تحليل وتدقيق😙'; break;
            case '__chat__': statusText = '...يكتب😁'; break;
            default: statusText = '...جاري المعالجة'; break;
        }

        // Directly update the persona status text, overriding the default from setPersonaState
        personaStatus.textContent = statusText;

    } else if (event === 'stream_chunk') {
        partialResponse += data.data.chunk;
        botMessageElement.innerHTML = marked.parse(partialResponse);
        chatContainer.scrollTop = chatContainer.scrollHeight;  // Scroll during streaming

    } else if (event === 'final_answer') {
        const finalData = data.data;
        // Note: We no longer need to update user_message here for audio, as it's handled in 'transcribed'
        botMessageElement.dataset.originalText = partialResponse || finalData.answer || "عذرا يرجى اعادة المحاولة!";
        botMessageElement.dataset.audioPath = finalData.audio_path || '';
        botMessageElement.innerHTML = marked.parse(botMessageElement.dataset.originalText);
        addTTSControl(botMessageElement);
        setPersonaState('idle');
        partialResponse = '';  // Reset for next message

    } else if (event === 'error') {
        botMessageElement.innerHTML = marked.parse(`حدث خطأ: ${data.message}`);
        setPersonaState('error');
        setTimeout(() => setPersonaState('idle'), 4000);
        partialResponse = '';
    }
}
// Modify the callChatbotAPI function to include session_id in formData
async function callChatbotAPI(prompt = null, audioBlob = null) {
    isLoading = true;
    setPersonaState('thinking');
    sendButton.disabled = true;
    chatInput.disabled = true;
    micButton.disabled = true;
    partialResponse = '';  // Reset here

    const botMessageElement = addMessageToChat('bot', '...', true);

    try {
        const formData = new FormData();
        formData.append('session_id', sessionId);  // Add session_id here
        formData.append('provider', selectedProvider);  // Add selected provider
        if (audioBlob) {
            formData.append('audio', audioBlob, 'recording.webm');
        } else if (prompt) {
            formData.append('query', prompt);
        }

        const response = await fetch(backendUrl, { method: 'POST', body: formData });

        if (!response.ok) throw new Error(`API error: ${response.status} ${response.statusText}`);

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const parts = buffer.split('\n\n');
            buffer = parts.pop(); // Last part might be incomplete

            for (const part of parts) {
                if (part.startsWith('data: ')) {
                    const jsonString = part.substring(6);
                    if (jsonString) {
                        try {
                            const data = JSON.parse(jsonString);
                            handleStreamEvent(data, botMessageElement);
                        } catch (e) {
                            console.error('Error parsing streaming JSON:', e, `Received: "${jsonString}"`);
                        }
                    }
                }
            }
        }
    } catch (error) {
        console.error("Chatbot API Error:", error);
        botMessageElement.innerHTML = marked.parse('عذراً، حدثت مشكلة. يرجى المحاولة مرة أخرى.');
        setPersonaState('error');
        setTimeout(() => setPersonaState('idle'), 4000);
    } finally {
        isLoading = false;
        sendButton.disabled = false;
        chatInput.disabled = false;
        micButton.disabled = false;
        isAudioInput = false;
        chatInput.focus();
    }
}
// Text input submit
chatForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const userInput = chatInput.value.trim();
    if (userInput && !isLoading) {
        addMessageToChat('user', userInput);
        chatInput.value = '';
        callChatbotAPI(userInput);
    }
});

// Audio input
micButton.addEventListener('click', async () => {
    if (isLoading) return;

    if (!isRecording) {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];
            mediaRecorder.ondataavailable = (e) => audioChunks.push(e.data);
            mediaRecorder.onstop = () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                addMessageToChat('user', 'رسالة صوتية...');
                isAudioInput = true;
                callChatbotAPI(null, audioBlob);
            };
            mediaRecorder.start();
            isRecording = true;
            micButton.classList.remove('border-green-500', 'text-green-500', 'hover:bg-green-100', 'hover:border-green-700', 'hover:text-green-700');
            micButton.classList.add('border-red-500', 'text-red-500', 'hover:bg-red-100', 'hover:border-red-700', 'hover:text-red-700', 'recording-pulse');
        } catch (error) {
            console.error('Microphone access error:', error);
            alert('يرجى السماح بالوصول إلى الميكروفون.');
        }
    } else {
        mediaRecorder.stop();
        isRecording = false;
        micButton.classList.remove('border-red-500', 'text-red-500', 'hover:bg-red-100', 'hover:border-red-700', 'hover:text-red-700', 'recording-pulse');
        micButton.classList.add('border-green-500', 'text-green-500', 'hover:bg-green-100', 'hover:border-green-700', 'hover:text-green-700');
    }
});
