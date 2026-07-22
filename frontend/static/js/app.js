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
    
    // Render Tags
    detectedTags.innerHTML = '';
    data.detected_label.forEach(label => {
        const tag = document.createElement('div');
        tag.className = 'tag';
        tag.innerHTML = `
            ${label}
            <button onclick="speak('${label}')" title="Listen"><i class="fas fa-volume-up"></i></button>
            <button class="practice-btn" onclick="openPractice('${label}')" title="Practice"><i class="fas fa-microphone"></i></button>
        `;
        detectedTags.appendChild(tag);
    });

    // Render Lesson
    lessonContent.innerHTML = marked.parse(data.lesson_context);

    // Render Quiz
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
