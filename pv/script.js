// Global variables
let sessionId = null;
let recognition = null;
let isRecording = false;
const API_BASE_URL = 'http://localhost:5000'; // Add this line to define the base URL

// Initial setup
document.addEventListener('DOMContentLoaded', function() {
    // Initialize speech recognition
    initSpeechRecognition();
    
    // Fetch available careers for dropdown
    fetchCareers();
    
    // Setup event listeners
    setupEventListeners();
});

// Initialize speech recognition
function initSpeechRecognition() {
    if ('webkitSpeechRecognition' in window) {
        recognition = new webkitSpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'vi-VN';

        recognition.onstart = function() {
            isRecording = true;
            const listenBtn = document.getElementById('listen-btn');
            const recordingStatus = document.getElementById('recording-status');
            
            if (listenBtn) listenBtn.style.display = 'none';
            if (recordingStatus) recordingStatus.style.display = 'flex';
        };

        recognition.onresult = function(event) {
            let interimTranscript = '';
            let finalTranscript = '';

            for (let i = event.resultIndex; i < event.results.length; i++) {
                if (event.results[i].isFinal) {
                    finalTranscript += event.results[i][0].transcript;
                } else {
                    interimTranscript += event.results[i][0].transcript;
                }
            }

            const answerText = document.getElementById('answer-text');
            if (answerText) {
                answerText.textContent = finalTranscript || interimTranscript;
            }
        };

        recognition.onend = function() {
            isRecording = false;
            const listenBtn = document.getElementById('listen-btn');
            const recordingStatus = document.getElementById('recording-status');
            
            if (listenBtn) listenBtn.style.display = 'flex';
            if (recordingStatus) recordingStatus.style.display = 'none';
        };

        recognition.onerror = function(event) {
            console.error('Speech recognition error:', event.error);
            isRecording = false;
            const listenBtn = document.getElementById('listen-btn');
            const recordingStatus = document.getElementById('recording-status');
            
            if (listenBtn) listenBtn.style.display = 'flex';
            if (recordingStatus) recordingStatus.style.display = 'none';
            
            if (event.error === 'not-allowed') {
                alert('Vui lòng cấp quyền truy cập microphone để sử dụng chức năng phỏng vấn bằng giọng nói.');
            }
        };
    } else {
        alert('Trình duyệt của bạn không hỗ trợ chức năng nhận dạng giọng nói. Vui lòng sử dụng Chrome hoặc Edge phiên bản mới nhất.');
    }
}

// Fetch available careers from the API
async function fetchCareers() {
    try {
        // Make sure we have a server running
        const response = await fetch(`${API_BASE_URL}/api/careers`);
        
        if (!response.ok) {
            throw new Error(`Server responded with status ${response.status}`);
        }
        
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            throw new Error('Response is not JSON');
        }
        
        const careers = await response.json();
        
        const jobSelect = document.getElementById('job');
        if (!jobSelect) {
            console.error('Job select element not found');
            return;
        }
        
        // Clear existing options except the first one
        jobSelect.innerHTML = '<option value="">Chọn nghề nghiệp</option>';
        
        // Add new options
        careers.forEach(career => {
            const option = document.createElement('option');
            option.value = career.name;
            option.textContent = career.name;
            jobSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Error fetching careers:', error);
        // No need to alert as we already have hardcoded options
    }
}

// Setup event listeners
function setupEventListeners() {
    // Start interview button
    const startInterviewBtn = document.getElementById('start-interview');
    if (startInterviewBtn) {
        startInterviewBtn.addEventListener('click', startInterview);
    }
    
    // Voice control buttons
    const listenBtn = document.getElementById('listen-btn');
    if (listenBtn) {
        listenBtn.addEventListener('click', toggleSpeechRecognition);
    }
    
    const clearAnswerBtn = document.getElementById('clear-answer');
    if (clearAnswerBtn) {
        clearAnswerBtn.addEventListener('click', clearAnswer);
    }
    
    // Navigation buttons
    const nextQuestionBtn = document.getElementById('next-question');
    if (nextQuestionBtn) {
        nextQuestionBtn.addEventListener('click', submitAnswer);
    }
    
    const finishInterviewBtn = document.getElementById('finish-interview');
    if (finishInterviewBtn) {
        finishInterviewBtn.addEventListener('click', finishInterview);
    }
    
    const restartBtn = document.getElementById('restart');
    if (restartBtn) {
        restartBtn.addEventListener('click', restartInterview);
    }
    
    const downloadResultBtn = document.getElementById('download-result');
    if (downloadResultBtn) {
        downloadResultBtn.addEventListener('click', downloadResults);
    }
}

// Toggle speech recognition
function toggleSpeechRecognition() {
    if (recognition) {
        if (isRecording) {
            recognition.stop();
        } else {
            try {
                recognition.start();
            } catch (e) {
                console.error('Error starting recognition:', e);
                recognition.stop();
            }
        }
    }
}

// Clear answer text
function clearAnswer() {
    const answerText = document.getElementById('answer-text');
    if (answerText) {
        answerText.textContent = '';
    }
}

// Start the interview
async function startInterview() {
    // Get candidate information
    const nameInput = document.getElementById('name');
    const ageInput = document.getElementById('age');
    const jobSelect = document.getElementById('job');
    
    if (!nameInput || !ageInput || !jobSelect) {
        console.error('Form elements not found');
        return;
    }
    
    // Validate inputs
    if (!nameInput.value.trim()) {
        alert('Vui lòng nhập họ và tên');
        nameInput.focus();
        return;
    }
    
    if (!ageInput.value || ageInput.value < 18 || ageInput.value > 100) {
        alert('Vui lòng nhập tuổi hợp lệ (18-100)');
        ageInput.focus();
        return;
    }
    
    if (!jobSelect.value) {
        alert('Vui lòng chọn nghề nghiệp ứng tuyển');
        jobSelect.focus();
        return;
    }
    
    try {
        // Show loading indicator
        toggleLoadingIndicator(true, 'Đang bắt đầu phỏng vấn...');
        
        // Start interview session with API
        const response = await fetch(`${API_BASE_URL}/api/start-interview`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: nameInput.value.trim(),
                age: parseInt(ageInput.value),
                job: jobSelect.value
            })
        });
        
        if (!response.ok) {
            throw new Error(`Server responded with status ${response.status}`);
        }
        
        const data = await response.json();
        
        // Hide loading indicator
        toggleLoadingIndicator(false);
        
        if (data.error) {
            alert(data.error);
            return;
        }
        
        // Save session ID
        sessionId = data.session_id;
        
        // Update UI
        const jobTitle = document.getElementById('job-title');
        const candidateName = document.getElementById('candidate-name');
        const candidateAge = document.getElementById('candidate-age');
        
        if (jobTitle) jobTitle.textContent = jobSelect.value;
        if (candidateName) candidateName.textContent = nameInput.value.trim();
        if (candidateAge) candidateAge.textContent = ageInput.value;
        
        // Display first question
        updateQuestion(data);
        
        // Switch to interview screen
        switchScreen('interview-screen');
    } catch (error) {
        toggleLoadingIndicator(false);
        console.error('Error starting interview:', error);
        alert('Không thể bắt đầu phỏng vấn. Vui lòng thử lại sau.');
    }
}

// Update the question display
function updateQuestion(data) {
    if (data.complete) {
        // Interview is complete
        finishInterview();
        return;
    }
    
    const currentCriteria = document.getElementById('current-criteria');
    const currentQuestion = document.getElementById('current-question');
    const answerText = document.getElementById('answer-text');
    
    if (currentCriteria) currentCriteria.textContent = data.criteria.name;
    if (currentQuestion) currentQuestion.textContent = data.question;
    if (answerText) answerText.textContent = '';
    
    // Update progress indicators
    const criteriaIndex = data.progress.criteria_index + 1;
    const criteriaTotal = data.progress.criteria_total;
    const progressPercentage = (criteriaIndex / criteriaTotal) * 100;
    
    const currentCriteriaNumber = document.getElementById('current-criteria-number');
    const totalCriteriaNumber = document.getElementById('total-criteria-number');
    const interviewProgress = document.getElementById('interview-progress');
    
    if (currentCriteriaNumber) currentCriteriaNumber.textContent = criteriaIndex;
    if (totalCriteriaNumber) totalCriteriaNumber.textContent = criteriaTotal;
    if (interviewProgress) interviewProgress.style.width = `${progressPercentage}%`;
}

// Submit answer and move to next question
async function submitAnswer() {
    if (!sessionId) {
        alert('Phiên phỏng vấn không hợp lệ. Vui lòng bắt đầu lại.');
        return;
    }
    
    const answerText = document.getElementById('answer-text');
    if (!answerText) {
        console.error('Answer text element not found');
        return;
    }
    
    const answer = answerText.textContent.trim();
    if (!answer) {
        alert('Vui lòng trả lời câu hỏi hiện tại trước khi chuyển tiếp.');
        return;
    }
    
    try {
        // Show loading indicator - AI evaluation takes time
        toggleLoadingIndicator(true, 'Đang đánh giá câu trả lời...');
        
        const response = await fetch(`${API_BASE_URL}/api/submit-answer`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: sessionId,
                answer: answer
            })
        });
        
        if (!response.ok) {
            throw new Error(`Server responded with status ${response.status}`);
        }
        
        const data = await response.json();
        
        // Hide loading indicator
        toggleLoadingIndicator(false);
        
        if (data.error) {
            alert(data.error);
            return;
        }
        
        // Update question
        updateQuestion(data);
    } catch (error) {
        toggleLoadingIndicator(false);
        console.error('Error submitting answer:', error);
        alert('Không thể gửi câu trả lời. Vui lòng thử lại.');
    }
}

// Finish the interview
async function finishInterview() {
    if (!sessionId) {
        alert('Phiên phỏng vấn không hợp lệ. Vui lòng bắt đầu lại.');
        return;
    }
    
    try {
        // Show loading indicator
        toggleLoadingIndicator(true, 'Đang hoàn thành phỏng vấn và tạo báo cáo...');
        
        const response = await fetch(`${API_BASE_URL}/api/finish-interview`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: sessionId
            })
        });
        
        if (!response.ok) {
            throw new Error(`Server responded with status ${response.status}`);
        }
        
        const results = await response.json();
        
        // Hide loading indicator
        toggleLoadingIndicator(false);
        
        if (results.error) {
            alert(results.error);
            return;
        }
        
        // Update result screen
        const resultName = document.getElementById('result-name');
        const resultAge = document.getElementById('result-age');
        const resultJob = document.getElementById('result-job');
        const totalScore = document.getElementById('total-score');
        const maxScore = document.getElementById('max-score');
        const totalScoreFill = document.getElementById('total-score-fill');
        
        if (resultName) resultName.textContent = results.candidate.name;
        if (resultAge) resultAge.textContent = results.candidate.age;
        if (resultJob) resultJob.textContent = results.candidate.job;
        if (totalScore) totalScore.textContent = results.total_score;
        if (maxScore) maxScore.textContent = results.max_score;
        
        // Update score bar
        if (totalScoreFill) totalScoreFill.style.width = `${results.score_percentage}%`;
        
        // Generate detailed scores
        const criteriaScoresContainer = document.getElementById('criteria-scores');
        if (criteriaScoresContainer) {
            criteriaScoresContainer.innerHTML = '';
            
            results.detailed_results.forEach(result => {
                const scorePercentage = (result.score / 4) * 100;
                
                const scoreItem = document.createElement('div');
                scoreItem.className = 'criteria-score-item';
                
                // Create HTML for the score item
                let scoreItemHTML = `
                    <div class="criteria-name">${result.criteria_name}</div>
                    <div class="criteria-bar">
                        <div class="criteria-bar-fill" style="width: ${scorePercentage}%"></div>
                    </div>
                    <div class="criteria-score">${result.score}/4</div>
                `;
                
                // Add reasoning if available
                if (result.reasoning) {
                    scoreItemHTML += `
                        <div class="criteria-reasoning">
                            <div class="reasoning-toggle">
                                <i class="fas fa-chevron-down"></i> Xem đánh giá
                            </div>
                            <div class="reasoning-content" style="display: none;">
                                ${result.reasoning}
                            </div>
                        </div>
                    `;
                }
                
                scoreItem.innerHTML = scoreItemHTML;
                criteriaScoresContainer.appendChild(scoreItem);
                
                // Add event listener for toggling reasoning
                const toggleButton = scoreItem.querySelector('.reasoning-toggle');
                if (toggleButton) {
                    toggleButton.addEventListener('click', function() {
                        const content = this.nextElementSibling;
                        const icon = this.querySelector('i');
                        
                        if (content.style.display === 'block') {
                            content.style.display = 'none';
                            icon.className = 'fas fa-chevron-down';
                            this.innerHTML = this.innerHTML.replace('Ẩn đánh giá', 'Xem đánh giá');
                        } else {
                            content.style.display = 'block';
                            icon.className = 'fas fa-chevron-up';
                            this.innerHTML = this.innerHTML.replace('Xem đánh giá', 'Ẩn đánh giá');
                        }
                    });
                }
            });
        }
        
        // Update evaluation text
        const evaluationText = document.getElementById('evaluation-text');
        if (evaluationText) evaluationText.textContent = results.evaluation;
        
        // Switch to result screen
        switchScreen('result-screen');
    } catch (error) {
        toggleLoadingIndicator(false);
        console.error('Error finishing interview:', error);
        alert('Không thể hoàn thành phỏng vấn. Vui lòng thử lại.');
    }
}

// Toggle loading indicator
function toggleLoadingIndicator(show, message = 'Đang xử lý...') {
    // Check if loading indicator exists, if not create it
    let loadingElement = document.getElementById('loading-indicator');
    
    if (!loadingElement) {
        loadingElement = document.createElement('div');
        loadingElement.id = 'loading-indicator';
        loadingElement.className = 'loading';
        loadingElement.innerHTML = `
            <div class="loading-spinner"></div>
            <p id="loading-message">${message}</p>
        `;
        document.body.appendChild(loadingElement);
    } else {
        const loadingMessage = document.getElementById('loading-message');
        if (loadingMessage) loadingMessage.textContent = message;
    }
    
    loadingElement.style.display = show ? 'flex' : 'none';
}

// Switch between screens
function switchScreen(screenId) {
    const screens = document.querySelectorAll('.screen');
    if (screens.length === 0) {
        console.error('No screen elements found');
        return;
    }
    
    screens.forEach(screen => {
        screen.classList.remove('active');
    });
    
    const targetScreen = document.getElementById(screenId);
    if (targetScreen) {
        targetScreen.classList.add('active');
    } else {
        console.error(`Screen with ID ${screenId} not found`);
    }
}

// Restart the interview
function restartInterview() {
    // Reset session
    sessionId = null;
    
    // Reset form
    const nameInput = document.getElementById('name');
    const ageInput = document.getElementById('age');
    const jobSelect = document.getElementById('job');
    
    if (nameInput) nameInput.value = '';
    if (ageInput) ageInput.value = '';
    if (jobSelect) jobSelect.value = '';
    
    // Switch to start screen
    switchScreen('start-screen');
}

// Download results as text file
function downloadResults() {
    const resultName = document.getElementById('result-name');
    const resultAge = document.getElementById('result-age');
    const resultJob = document.getElementById('result-job');
    const totalScore = document.getElementById('total-score');
    const maxScore = document.getElementById('max-score');
    const evaluationText = document.getElementById('evaluation-text');
    
    if (!resultName || !resultAge || !resultJob || !totalScore || !maxScore || !evaluationText) {
        console.error('Result elements not found');
        return;
    }
    
    const name = resultName.textContent;
    const age = resultAge.textContent;
    const job = resultJob.textContent;
    const score = totalScore.textContent;
    const max = maxScore.textContent;
    const evaluation = evaluationText.textContent;
    
    let resultText = `PHIẾU ĐÁNH GIÁ PHỎNG VẤN\n`;
    resultText += `==============================================\n\n`;
    resultText += `Thông tin ứng viên:\n`;
    resultText += `- Họ và tên: ${name}\n`;
    resultText += `- Tuổi: ${age}\n`;
    resultText += `- Vị trí ứng tuyển: ${job}\n\n`;
    resultText += `Kết quả đánh giá:\n`;
    resultText += `- Tổng điểm: ${score}/${max}\n\n`;
    
    resultText += `Chi tiết đánh giá theo tiêu chí:\n`;
    const criteriaItems = document.querySelectorAll('.criteria-score-item');
    criteriaItems.forEach(item => {
        const criteriaName = item.querySelector('.criteria-name');
        const criteriaScore = item.querySelector('.criteria-score');
        
        if (criteriaName && criteriaScore) {
            resultText += `- ${criteriaName.textContent}: ${criteriaScore.textContent}\n`;
            
            const reasoningContent = item.querySelector('.reasoning-content');
            if (reasoningContent) {
                resultText += `  Nhận xét: ${reasoningContent.textContent.trim()}\n\n`;
            }
        }
    });
    
    resultText += `\nĐÁNH GIÁ TỔNG QUAN:\n${evaluation}\n\n`;
    resultText += `==============================================\n`;
    resultText += `Ngày đánh giá: ${new Date().toLocaleDateString('vi-VN')}\n`;
    
    const blob = new Blob([resultText], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `phong-van-${name.replace(/\s+/g, '-')}-${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    
    setTimeout(() => {
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }, 100);
}