// DOM Elements
const tabBtns = document.querySelectorAll('.tab-btn');
const tabContents = document.querySelectorAll('.tab-content');
const dropArea = document.getElementById('drop-area');
const fileInput = document.getElementById('file-input');
const webcamVideo = document.getElementById('webcam-video');
const webcamCanvas = document.getElementById('webcam-canvas');
const captureBtn = document.getElementById('capture-btn');
const previewContainer = document.getElementById('preview-container');
const imagePreview = document.getElementById('image-preview');
const analyzeBtn = document.getElementById('analyze-btn');
const loader = document.getElementById('loader');
const resultsSection = document.getElementById('results-section');
const annotatedImage = document.getElementById('annotated-image');
const detectedTags = document.getElementById('detected-tags');
const detectedCardsGrid = document.getElementById('detected-cards-grid');
const objectsCountBadge = document.getElementById('objects-count-badge');
const lessonContent = document.getElementById('lesson-content');
const quizContainer = document.getElementById('quiz-container');
const quizQuestion = document.getElementById('quiz-question');
const quizOptions = document.getElementById('quiz-options');
const quizFeedback = document.getElementById('quiz-feedback');

// Modal Elements
const practiceModal = document.getElementById('practice-modal');
const closeModal = document.querySelector('.close-modal');
const targetWordSpan = document.getElementById('target-word');
const recordBtn = document.getElementById('record-btn');
const recordStatus = document.getElementById('record-status');
const evaluationResult = document.getElementById('evaluation-result');
const evalScore = document.getElementById('eval-score');
const evalFeedback = document.getElementById('eval-feedback');
const evalTip = document.getElementById('eval-tip');

let currentFile = null;
let mediaStream = null;
let mediaRecorder = null;
let audioChunks = [];

// --- 1. Tabs & Navigation ---
tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        const tabId = btn.dataset.tab;
        
        tabBtns.forEach(b => b.classList.remove('active'));
        tabContents.forEach(c => c.classList.remove('active'));
        
        btn.classList.add('active');
        document.getElementById(`${tabId}-tab`).classList.add('active');
        
        if (tabId === 'webcam') {
            startWebcam();
        } else {
            stopWebcam();
        }
    });
});

// --- 2. File Upload & Preview ---
dropArea.addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFile(e.target.files[0]);
    }
});

dropArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropArea.style.borderColor = 'var(--primary)';
});

dropArea.addEventListener('dragleave', () => {
    dropArea.style.borderColor = 'var(--border)';
});

dropArea.addEventListener('drop', (e) => {
    e.preventDefault();
    dropArea.style.borderColor = 'var(--border)';
    if (e.dataTransfer.files.length > 0) {
        handleFile(e.dataTransfer.files[0]);
    }
});

function handleFile(file) {
    currentFile = file;
    const reader = new FileReader();
    reader.onload = (e) => {
        imagePreview.src = e.target.result;
        previewContainer.classList.remove('hidden');
    };
    reader.readAsDataURL(file);
}

// --- 3. Webcam Handling ---
async function startWebcam() {
    try {
        mediaStream = await navigator.mediaDevices.getUserMedia({ video: true });
        webcamVideo.srcObject = mediaStream;
    } catch (err) {
        alert('Could not access webcam: ' + err.message);
    }
}

function stopWebcam() {
    if (mediaStream) {
        mediaStream.getTracks().forEach(track => track.stop());
        mediaStream = null;
    }
}

captureBtn.addEventListener('click', () => {
    const context = webcamCanvas.getContext('2d');
    webcamCanvas.width = webcamVideo.videoWidth;
    webcamCanvas.height = webcamVideo.videoHeight;
    context.drawImage(webcamVideo, 0, 0);
    
    webcamCanvas.toBlob((blob) => {
        currentFile = new File([blob], "capture.jpg", { type: "image/jpeg" });
        imagePreview.src = URL.createObjectURL(blob);
        previewContainer.classList.remove('hidden');
    }, 'image/jpeg');
});

// --- 4. API Analysis ---
analyzeBtn.addEventListener('click', async () => {
    if (!currentFile) return;

    loader.classList.remove('hidden');
    resultsSection.classList.add('hidden');
    
    const formData = new FormData();
    formData.append('file', currentFile);

    try {
        const response = await fetch('/api/v1/analyze', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        if (data.success) {
            renderResults(data);
        } else {
            alert('Analysis failed');
        }
    } catch (err) {
        console.error(err);
        alert('Error connecting to server');
    } finally {
        loader.classList.add('hidden');
    }
});

function renderResults(data) {
    resultsSection.classList.remove('hidden');
    annotatedImage.src = data.annotated_img_url + '?t=' + new Date().getTime();
    
    // 1. Render Flashcards from detected objects (Phase 1 Vision Upgrade)
    if (detectedCardsGrid) {
        detectedCardsGrid.innerHTML = '';
        const objects = data.detected_objects || [];
        if (objectsCountBadge) {
            objectsCountBadge.textContent = `${objects.length} đồ vật`;
        }

        if (objects.length > 0) {
            objects.forEach(obj => {
                const card = document.createElement('div');
                card.className = 'vocab-flashcard';
                card.dataset.label = obj.label;
                const confPercent = obj.confidence_percent || Math.round((obj.confidence || 0) * 100);
                const thumbHtml = obj.crop_url 
                    ? `<img class="card-thumb-img" src="${obj.crop_url}?t=${new Date().getTime()}" alt="${obj.label}" loading="lazy">` 
                    : `<div class="card-thumb-placeholder"><i class="fa-solid fa-image"></i></div>`;

                card.innerHTML = `
                    <div class="card-thumb-wrap">
                        ${thumbHtml}
                        <span class="card-conf-badge">${confPercent}%</span>
                    </div>
                    <div class="card-info">
                        <h4 class="card-word">${obj.label}</h4>
                        <div class="card-btn-row">
                            <button type="button" class="card-action-btn speak-btn" onclick="speak('${obj.label}')" title="Nghe phát âm" aria-label="Nghe ${obj.label}">
                                <i class="fa-solid fa-volume-high" aria-hidden="true"></i>
                                <span>Nghe</span>
                            </button>
                            <button type="button" class="card-action-btn practice-btn" onclick="openPractice('${obj.label}')" title="Luyện nói" aria-label="Luyện nói ${obj.label}">
                                <i class="fa-solid fa-microphone" aria-hidden="true"></i>
                                <span>Luyện</span>
                            </button>
                        </div>
                    </div>
                `;
                detectedCardsGrid.appendChild(card);
            });
        } else {
            detectedCardsGrid.innerHTML = `
                <p style="grid-column: 1 / -1; font-size: 0.88rem; color: var(--ink-caption); text-align: center; padding: 1rem;">
                    Không tìm thấy vật thể riêng biệt nào. Hãy thử chụp ảnh gần hơn và đủ sáng.
                </p>
            `;
        }
    }

    // 2. Render Quick Tags
    detectedTags.innerHTML = '';
    const labels = data.detected_label || [];
    labels.forEach(label => {
        const tag = document.createElement('div');
        tag.className = 'tag-btn';
        tag.innerHTML = `
            <span>${label}</span>
            <button type="button" class="tag-action-icon" onclick="event.stopPropagation(); speak('${label}')" title="Nghe ${label}" aria-label="Nghe ${label}">
                <i class="fa-solid fa-volume-high" aria-hidden="true"></i>
            </button>
            <button type="button" class="tag-action-icon" onclick="event.stopPropagation(); openPractice('${label}')" title="Luyện nói ${label}" aria-label="Luyện nói ${label}">
                <i class="fa-solid fa-microphone" aria-hidden="true"></i>
            </button>
        `;
        tag.addEventListener('click', () => speak(label));
        detectedTags.appendChild(tag);
    });

    // 3. Render Lesson
    lessonContent.innerHTML = marked.parse(data.lesson_context);

    // 4. Render Quiz
    if (data.quiz) {
        renderQuiz(data.quiz);
    } else {
        quizContainer.classList.add('hidden');
    }

    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

function renderQuiz(quiz) {
    quizContainer.classList.remove('hidden');
    quizQuestion.textContent = quiz.question;
    quizOptions.innerHTML = '';
    quizFeedback.classList.add('hidden');

    quiz.options.forEach(option => {
        const btn = document.createElement('button');
        btn.className = 'option-btn';
        btn.textContent = option;
        btn.onclick = () => {
            const allBtns = quizOptions.querySelectorAll('.option-btn');
            allBtns.forEach(b => b.disabled = true);
            
            if (option === quiz.answer) {
                btn.classList.add('correct');
                quizFeedback.textContent = "🎉 Correct! Well done.";
                quizFeedback.className = "quiz-feedback success";
            } else {
                btn.classList.add('wrong');
                quizFeedback.textContent = `💡 Oops! The correct answer is: ${quiz.answer}`;
                quizFeedback.className = "quiz-feedback error";
            }
            quizFeedback.classList.remove('hidden');
        };
        quizOptions.appendChild(btn);
    });
}

// --- 5. Voice & Practice ---
function speak(text) {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'en-US';
    window.speechSynthesis.speak(utterance);
}

function openPractice(word) {
    targetWordSpan.textContent = word;
    practiceModal.classList.remove('hidden');
    evaluationResult.classList.add('hidden');
    recordStatus.textContent = "Click to start recording";
    recordBtn.classList.remove('recording');
}

closeModal.onclick = () => {
    practiceModal.classList.add('hidden');
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
    }
};

recordBtn.onclick = async () => {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
        recordBtn.classList.remove('recording');
        recordStatus.textContent = "Processing...";
        return;
    }

    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];

        mediaRecorder.ondataavailable = (e) => audioChunks.push(e.data);
        
        mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            sendForEvaluation(audioBlob);
            stream.getTracks().forEach(track => track.stop());
        };

        mediaRecorder.start();
        recordBtn.classList.add('recording');
        recordStatus.textContent = "Recording... Click to stop";
        evaluationResult.classList.add('hidden');
    } catch (err) {
        alert('Could not access microphone');
    }
};

async function sendForEvaluation(blob) {
    const formData = new FormData();
    formData.append('audio_file', blob, 'recording.wav');
    formData.append('target_word', targetWordSpan.textContent);

    try {
        const response = await fetch('/api/v1/evaluate-pronunciation', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        evaluationResult.classList.remove('hidden');
        evalScore.textContent = data.score || 0;
        evalFeedback.textContent = data.feedback || "No feedback available";
        evalTip.textContent = data.tip || "Keep practicing!";
        recordStatus.textContent = "Click to record again";
        
    } catch (err) {
        console.error(err);
        recordStatus.textContent = "Evaluation failed";
    }
}
