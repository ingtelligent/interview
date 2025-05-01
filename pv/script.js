// Global variables
let sessionId = null;
let recognition = null;
let isRecording = false;
let interviewMode = null; // 'text' or 'voice'
let interviewTimer = null;
let interviewSeconds = 0;
let isMicMuted = false;
let isCameraOff = true;
let userInfo = {
    name: '',
    age: '',
    job: ''
};
const API_BASE_URL = 'http://localhost:5000'; // Base URL for API

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
            // Update the mic button
            const micButton = document.getElementById('toggle-mic');
            if (micButton) {
                micButton.classList.add('pulse-recording');
                micButton.querySelector('i').className = 'fas fa-microphone-slash';
            }
            
            // Update the mic status
            const micStatus = document.getElementById('mic-status-indicator');
            if (micStatus) {
                micStatus.textContent = 'Đang ghi âm...';
                micStatus.parentElement.classList.add('recording');
            }
            
            // Update the next button to show it's for submitting after recording
            const nextButton = document.getElementById('next-voice-question');
            if (nextButton) {
                nextButton.innerHTML = '<i class="fas fa-check-circle"></i> Gửi câu trả lời';
            }
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

            const answerText = document.getElementById('voice-answer-text');
            if (answerText) {
                // Append or replace the existing text
                if (finalTranscript) {
                    // Append final transcript with a space
                    const currentText = answerText.textContent || '';
                    answerText.textContent = currentText + (currentText ? ' ' : '') + finalTranscript;
                    
                    // Remove any interim indicator if present
                    const interimIndicator = document.getElementById('interim-transcript');
                    if (interimIndicator) {
                        interimIndicator.remove();
                    }
                } else if (interimTranscript) {
                    // Show interim results as overlay
                    let interimIndicator = document.getElementById('interim-transcript');
                    
                    // Create interim indicator if it doesn't exist
                    if (!interimIndicator) {
                        interimIndicator = document.createElement('div');
                        interimIndicator.id = 'interim-transcript';
                        interimIndicator.style.position = 'absolute';
                        interimIndicator.style.bottom = '10px';
                        interimIndicator.style.left = '15px';
                        interimIndicator.style.right = '15px';
                        interimIndicator.style.backgroundColor = 'rgba(52, 152, 219, 0.2)';
                        interimIndicator.style.borderRadius = '4px';
                        interimIndicator.style.padding = '8px';
                        interimIndicator.style.color = '#2980b9';
                        interimIndicator.style.fontStyle = 'italic';
                        
                        // Add it to the voice answer section
                        const voiceAnswerSection = document.getElementById('voice-answer-section');
                        if (voiceAnswerSection) {
                            voiceAnswerSection.style.position = 'relative';
                            voiceAnswerSection.appendChild(interimIndicator);
                        }
                    }
                    
                    // Update the text
                    interimIndicator.textContent = interimTranscript;
                }
            }
        };

        recognition.onend = function() {
            // If we're still supposed to be recording, restart the recognition
            if (isRecording) {
                try {
                    recognition.start();
                } catch (e) {
                    console.error('Error restarting recognition after onend:', e);
                    isRecording = false;
                    
                    // Update the mic button
                    const micButton = document.getElementById('toggle-mic');
                    if (micButton) {
                        micButton.classList.remove('pulse-recording');
                        micButton.querySelector('i').className = 'fas fa-microphone';
                    }
                    
                    // Update the mic status
                    const micStatus = document.getElementById('mic-status-indicator');
                    if (micStatus) {
                        micStatus.textContent = 'Ghi âm đã dừng';
                        micStatus.parentElement.classList.remove('recording');
                    }
                }
            } else {
                // Normal end of recording
                const micButton = document.getElementById('toggle-mic');
                if (micButton) {
                    micButton.classList.remove('pulse-recording');
                    micButton.querySelector('i').className = 'fas fa-microphone';
                }
                
                // Update the mic status
                const micStatus = document.getElementById('mic-status-indicator');
                if (micStatus) {
                    micStatus.textContent = 'Ghi âm đã dừng';
                    micStatus.parentElement.classList.remove('recording');
                }
            }
        };

        recognition.onerror = function(event) {
            console.error('Speech recognition error:', event.error);
            
            // Only change the state if it's a terminal error
            if (event.error === 'not-allowed' || event.error === 'service-not-allowed') {
                isRecording = false;
                
                // Update the mic button
                const micButton = document.getElementById('toggle-mic');
                if (micButton) {
                    micButton.classList.remove('pulse-recording');
                    micButton.querySelector('i').className = 'fas fa-microphone';
                }
                
                // Update the mic status
                const micStatus = document.getElementById('mic-status-indicator');
                if (micStatus) {
                    micStatus.textContent = 'Không có quyền truy cập mic';
                    micStatus.parentElement.classList.remove('recording');
                }
                
                alert('Vui lòng cấp quyền truy cập microphone để sử dụng chức năng phỏng vấn bằng giọng nói.');
            } else if (event.error === 'network') {
                // Network errors might be temporary
                console.warn('Network error occurred with speech recognition');
                
                // Update the mic status
                const micStatus = document.getElementById('mic-status-indicator');
                if (micStatus) {
                    micStatus.textContent = 'Lỗi kết nối mạng...';
                }
            } else if (event.error === 'aborted') {
                // We don't need to do anything special for aborted errors
                console.log('Speech recognition aborted');
            } else {
                // For any other errors, try to restart if we're still in recording mode
                if (isRecording) {
                    try {
                        setTimeout(() => {
                            recognition.start();
                            
                            // Update the mic status
                            const micStatus = document.getElementById('mic-status-indicator');
                            if (micStatus) {
                                micStatus.textContent = 'Đang ghi âm...';
                                micStatus.parentElement.classList.add('recording');
                            }
                        }, 1000); // Wait a second before restarting
                    } catch (e) {
                        console.error('Error restarting recognition after error:', e);
                        isRecording = false;
                        
                        // Update the mic button
                        const micButton = document.getElementById('toggle-mic');
                        if (micButton) {
                            micButton.classList.remove('pulse-recording');
                            micButton.querySelector('i').className = 'fas fa-microphone';
                        }
                        
                        // Update the mic status
                        const micStatus = document.getElementById('mic-status-indicator');
                        if (micStatus) {
                            micStatus.textContent = 'Lỗi ghi âm';
                            micStatus.parentElement.classList.remove('recording');
                        }
                    }
                }
            }
        };
    } else {
        alert('Trình duyệt của bạn không hỗ trợ chức năng nhận dạng giọng nói. Vui lòng sử dụng Chrome hoặc Edge phiên bản mới nhất.');
    }
}

// Fetch available careers from the API
async function fetchCareers() {
    try {
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
        // We already have hardcoded options as fallback
    }
}

// Setup event listeners
function setupEventListeners() {
    // Các sự kiện hiện có...
    document.getElementById('continue-to-mode').addEventListener('click', validateInfoAndContinue);
    document.getElementById('select-text-mode').addEventListener('click', function() {
        interviewMode = 'text';
        document.getElementById('select-text-mode').style.border = '3px solid #3498db';
        document.getElementById('select-voice-mode').style.border = 'none';
    });
    document.getElementById('select-voice-mode').addEventListener('click', function() {
        interviewMode = 'voice';
        document.getElementById('select-voice-mode').style.border = '3px solid #27ae60';
        document.getElementById('select-text-mode').style.border = 'none';
    });
    document.getElementById('start-interview').addEventListener('click', startInterview);
    document.getElementById('back-to-info').addEventListener('click', function() {
        switchScreen('info-screen');
    });
    document.getElementById('chat-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendChatMessage();
        }
    });
    document.getElementById('send-message').addEventListener('click', sendChatMessage);
    document.getElementById('toggle-mic').addEventListener('click', toggleMicrophone);
    document.getElementById('toggle-camera').addEventListener('click', toggleCamera);
    document.getElementById('end-interview').addEventListener('click', finishInterview);
    document.getElementById('clear-voice-answer').addEventListener('click', function() {
        const answerText = document.getElementById('voice-answer-text');
        if (answerText) answerText.textContent = '';
        const interimIndicator = document.getElementById('interim-transcript');
        if (interimIndicator) interimIndicator.remove();
    });
    document.getElementById('next-voice-question').addEventListener('click', submitVoiceAnswer);
    document.getElementById('finish-chat-interview').addEventListener('click', finishInterview);
    document.getElementById('finish-voice-interview').addEventListener('click', finishInterview);
    document.getElementById('restart').addEventListener('click', restartInterview);
    document.getElementById('download-result').addEventListener('click', downloadResults);

    // Sự kiện cho nút lặp lại câu hỏi
    document.getElementById('repeat-question').addEventListener('click', function() {
        const currentQuestion = document.getElementById('current-voice-question');
        if (currentQuestion) {
            speakQuestion(currentQuestion.textContent);
        }
    });
}

// Toggle microphone on/off
function toggleMicrophone() {
    if (recognition) {
        if (isRecording) {
            // User wants to stop recording
            isRecording = false;
            recognition.stop();
            isMicMuted = true;
            
            // Update the mic button
            const micButton = document.getElementById('toggle-mic');
            if (micButton) {
                micButton.classList.remove('pulse-recording');
                micButton.querySelector('i').className = 'fas fa-microphone';
            }
            
            // Update the mic status
            const micStatus = document.getElementById('mic-status-indicator');
            if (micStatus) {
                micStatus.textContent = 'Ghi âm đã dừng';
                micStatus.parentElement.classList.remove('recording');
            }
        } else {
            // User wants to start recording
            try {
                recognition.start();
                isRecording = true;
                isMicMuted = false;
                
                // The status updates will happen in the onstart callback
            } catch (e) {
                console.error('Error starting recognition:', e);
                if (e.name === 'InvalidStateError') {
                    // The recognition is already started, try stopping first
                    try {
                        recognition.stop();
                        // Wait a moment before trying to restart
                        setTimeout(() => {
                            recognition.start();
                            isRecording = true;
                            isMicMuted = false;
                            
                            // Update the mic button
                            const micButton = document.getElementById('toggle-mic');
                            if (micButton) {
                                micButton.classList.add('pulse-recording');
                                micButton.querySelector('i').className = 'fas fa-microphone-slash';
                            }
                            
                            // Update the mic status
                            const micStatus = document.getElementById('mic-status-indicator');
                            if (micStatus) {
                                micStatus.textContent = 'Đang ghi âm...';
                                micStatus.parentElement.classList.add('recording');
                            }
                        }, 200);
                    } catch (innerError) {
                        console.error('Error during recovery attempt:', innerError);
                        alert('Không thể bắt đầu nhận dạng giọng nói. Vui lòng tải lại trang và thử lại.');
                    }
                } else {
                    // Some other error
                    alert('Lỗi khi kích hoạt nhận dạng giọng nói: ' + e.message);
                }
            }
        }
    } else {
        // Try to initialize speech recognition again
        initSpeechRecognition();
        if (recognition) {
            try {
                recognition.start();
                isRecording = true;
                isMicMuted = false;
                
                // Update the mic button
                const micButton = document.getElementById('toggle-mic');
                if (micButton) {
                    micButton.classList.add('pulse-recording');
                    micButton.querySelector('i').className = 'fas fa-microphone-slash';
                }
                
                // Update the mic status
                const micStatus = document.getElementById('mic-status-indicator');
                if (micStatus) {
                    micStatus.textContent = 'Đang ghi âm...';
                    micStatus.parentElement.classList.add('recording');
                }
            } catch (e) {
                console.error('Error starting newly initialized recognition:', e);
                alert('Không thể bắt đầu nhận dạng giọng nói sau khi khởi tạo lại.');
            }
        }
    }
}

// Toggle camera on/off
function toggleCamera() {
    isCameraOff = !isCameraOff;
    const cameraButton = document.getElementById('toggle-camera');
    
    if (cameraButton) {
        if (isCameraOff) {
            cameraButton.querySelector('i').className = 'fas fa-video-slash';
            cameraButton.style.backgroundColor = '#f8f9fa';
            cameraButton.style.color = '#95a5a6';
        } else {
            cameraButton.querySelector('i').className = 'fas fa-video';
            cameraButton.style.backgroundColor = 'white';
            cameraButton.style.color = '#9b59b6';
        }
    }
}

// Validate information and continue to mode selection
function validateInfoAndContinue() {
    const nameInput = document.getElementById('name');
    const ageInput = document.getElementById('age');
    const jobSelect = document.getElementById('job');
    
    // Clear previous validation styling
    nameInput.style.borderColor = '';
    ageInput.style.borderColor = '';
    jobSelect.style.borderColor = '';
    
    // Validate inputs
    let isValid = true;
    
    if (!nameInput.value.trim()) {
        nameInput.style.borderColor = '#e74c3c';
        isValid = false;
    }
    
    if (!ageInput.value || ageInput.value < 18 || ageInput.value > 100) {
        ageInput.style.borderColor = '#e74c3c';
        isValid = false;
    }
    
    if (!jobSelect.value) {
        jobSelect.style.borderColor = '#e74c3c';
        isValid = false;
    }
    
    if (isValid) {
        // Store user info
        userInfo = {
            name: nameInput.value.trim(),
            age: parseInt(ageInput.value),
            job: jobSelect.value
        };
        
        // Update username display on the mode selection screen
        document.getElementById('user-name-display').textContent = userInfo.name;
        
        // Continue to mode selection screen
        switchScreen('mode-screen');
    } else {
        alert('Vui lòng điền đầy đủ thông tin trước khi tiếp tục');
    }
}

// Start the interview
async function startInterview() {
    if (!interviewMode) {
        alert('Vui lòng chọn phương thức phỏng vấn');
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
                name: userInfo.name,
                age: userInfo.age,
                job: userInfo.job,
                mode: interviewMode
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
        
        // Update UI based on interview mode
        if (interviewMode === 'text') {
            initializeTextInterview(data);
        } else if (interviewMode === 'voice') {
            initializeVoiceInterview(data);
        }
    } catch (error) {
        toggleLoadingIndicator(false);
        console.error('Error starting interview:', error);
        alert('Không thể bắt đầu phỏng vấn. Vui lòng thử lại sau.');
    }
}

// Send chat message
function sendChatMessage() {
    const chatInput = document.getElementById('chat-input');
    const message = chatInput.value.trim();
    
    if (!message) {
        return;
    }
    
    // Add user message to chat
    addChatMessage(message, 'user');
    
    // Clear input
    chatInput.value = '';
    
    // Submit answer to API
    submitChatAnswer(message);
}

// Add message to chat container
function addChatMessage(message, sender) {
    const chatContainer = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    
    messageDiv.className = `chat-message ${sender === 'user' ? 'user-message' : 'interviewer-message'}`;
    
    const now = new Date();
    const timeString = now.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
    
    messageDiv.innerHTML = `
        <div class="message-content">${message}</div>
        <div class="message-time">${timeString}</div>
    `;
    
    chatContainer.appendChild(messageDiv);
    
    // Scroll to bottom
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Start interview timer
function startInterviewTimer() {
    if (interviewTimer) {
        clearInterval(interviewTimer);
    }
    
    interviewSeconds = 0;
    updateTimerDisplay();
    
    interviewTimer = setInterval(function() {
        interviewSeconds++;
        updateTimerDisplay();
    }, 1000);
}

// Update timer display
function updateTimerDisplay() {
    const minutes = Math.floor(interviewSeconds / 60);
    const seconds = interviewSeconds % 60;
    
    document.getElementById('interview-timer').textContent = 
        `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
}

// Initialize text interview
function initializeTextInterview(data) {
    // Update UI elements
    const jobTitle = document.getElementById('chat-job-title');
    const candidateName = document.getElementById('chat-candidate-name');
    const candidateAge = document.getElementById('chat-candidate-age');
    
    if (jobTitle) jobTitle.textContent = userInfo.job;
    if (candidateName) candidateName.textContent = userInfo.name;
    if (candidateAge) candidateAge.textContent = userInfo.age;
    
    // Clear previous chat messages
    document.getElementById('chat-messages').innerHTML = '';
    
    // Add welcome message
    addChatMessage('Xin chào! Tôi là trợ lý phỏng vấn ảo. Tôi sẽ đặt những câu hỏi để đánh giá kỹ năng và kinh nghiệm của bạn. Hãy trả lời một cách đầy đủ và chân thực nhé.', 'interviewer');
    
    // Add first question
    addChatMessage(data.question, 'interviewer');
    
    // Update progress indicators
    updateProgressIndicators(data, 'chat');
    
    // Switch to chat interview screen
    switchScreen('chat-interview-screen');
}

// Initialize voice interview
function initializeVoiceInterview(data) {
    // Cập nhật giao diện
    const jobTitle = document.getElementById('voice-job-title');
    const candidateName = document.getElementById('voice-candidate-name');
    const candidateAge = document.getElementById('voice-candidate-age');
    const currentQuestion = document.getElementById('current-voice-question');

    if (jobTitle) jobTitle.textContent = userInfo.job;
    if (candidateName) candidateName.textContent = userInfo.name;
    if (candidateAge) candidateAge.textContent = userInfo.age;
    if (currentQuestion) currentQuestion.textContent = data.question;

    // Đọc câu hỏi bằng giọng nói
    if (data.question) {
        speakQuestion(data.question);
    }

    // Xóa câu trả lời trước đó
    const answerText = document.getElementById('voice-answer-text');
    if (answerText) answerText.textContent = '';

    // Xóa bất kỳ chỉ báo tạm thời nào
    const interimIndicator = document.getElementById('interim-transcript');
    if (interimIndicator) {
        interimIndicator.remove();
    }

    // Đặt lại chỉ báo trạng thái mic
    const micStatus = document.getElementById('mic-status-indicator');
    if (micStatus) {
        micStatus.textContent = 'Chưa bắt đầu ghi âm';
        micStatus.parentElement.classList.remove('recording');
    }

    // Cập nhật chỉ báo tiến độ
    updateProgressIndicators(data, 'voice');

    // Bắt đầu đồng hồ phỏng vấn
    startInterviewTimer();

    // Chuyển sang màn hình phỏng vấn bằng giọng nói
    switchScreen('voice-interview-screen');
}

// Update progress indicators
function updateProgressIndicators(data, prefix) {
    // Update progress indicators
    const criteriaIndex = data.progress.criteria_index + 1;
    const criteriaTotal = data.progress.criteria_total;
    const progressPercentage = (criteriaIndex / criteriaTotal) * 100;
    
    const currentCriteriaNumber = document.getElementById(`${prefix}-current-criteria-number`);
    const totalCriteriaNumber = document.getElementById(`${prefix}-total-criteria-number`);
    const interviewProgress = document.getElementById(`${prefix}-interview-progress`);
    
    if (currentCriteriaNumber) currentCriteriaNumber.textContent = criteriaIndex;
    if (totalCriteriaNumber) totalCriteriaNumber.textContent = criteriaTotal;
    if (interviewProgress) interviewProgress.style.width = `${progressPercentage}%`;
}

// Submit chat answer
async function submitChatAnswer(message) {
    if (!sessionId) {
        alert('Phiên phỏng vấn không hợp lệ. Vui lòng bắt đầu lại.');
        return;
    }
    
    if (!message.trim()) {
        alert('Vui lòng nhập câu trả lời.');
        return;
    }
    
    try {
        // Show loading indicator
        toggleLoadingIndicator(true, 'Đang đánh giá câu trả lời...');
        
        const response = await fetch(`${API_BASE_URL}/api/submit-answer`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: sessionId,
                answer: message,
                mode: 'text'
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
        
        // Check if interview is complete
        if (data.complete) {
            addChatMessage('Cảm ơn bạn! Buổi phỏng vấn đã kết thúc. Hệ thống sẽ tổng hợp kết quả.', 'interviewer');
            setTimeout(() => finishInterview(), 2000);
            return;
        }
        
        // Add next question to chat
        addChatMessage(data.question, 'interviewer');
        
        // Update progress indicators
        updateProgressIndicators(data, 'chat');
    } catch (error) {
        toggleLoadingIndicator(false);
        console.error('Error submitting answer:', error);
        alert('Không thể gửi câu trả lời. Vui lòng thử lại.');
    }
}

// Submit voice answer
async function submitVoiceAnswer() {
    const answerText = document.getElementById('voice-answer-text');
    if (!answerText) {
        console.error('Answer text element not found');
        return;
    }

    const answer = answerText.textContent.trim();
    if (!answer) {
        alert('Vui lòng trả lời câu hỏi trước khi tiếp tục.');
        return;
    }

    try {
        // Dừng ghi âm nếu đang hoạt động
        if (recognition && isRecording) {
            isRecording = false;
            recognition.stop();

            const micButton = document.getElementById('toggle-mic');
            if (micButton) {
                micButton.classList.remove('pulse-recording');
                micButton.querySelector('i').className = 'fas fa-microphone';
            }

            const micStatus = document.getElementById('mic-status-indicator');
            if (micStatus) {
                micStatus.textContent = 'Đang xử lý câu trả lời...';
                micStatus.parentElement.classList.remove('recording');
            }
        }

        // Hiển thị chỉ báo tải
        toggleLoadingIndicator(true, 'Đang đánh giá câu trả lời...');

        const response = await fetch(`${API_BASE_URL}/api/submit-answer`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: sessionId,
                answer: answer,
                mode: 'voice'
            })
        });

        if (!response.ok) {
            throw new Error(`Server responded with status ${response.status}`);
        }

        const data = await response.json();

        // Ẩn chỉ báo tải
        toggleLoadingIndicator(false);

        if (data.error) {
            alert(data.error);
            return;
        }

        // Kiểm tra xem phỏng vấn đã hoàn tất chưa
        if (data.complete) {
            document.getElementById('current-voice-question').textContent = 'Phỏng vấn đã kết thúc! Cảm ơn bạn đã tham gia.';
            setTimeout(() => finishInterview(), 1500);
            return;
        }

        // Cập nhật câu hỏi
        document.getElementById('current-voice-question').textContent = data.question;

        // Đọc câu hỏi mới bằng giọng nói
        speakQuestion(data.question);

        // Xóa câu trả lời
        answerText.textContent = '';

        // Xóa bất kỳ bản ghi tạm thời nào
        const interimIndicator = document.getElementById('interim-transcript');
        if (interimIndicator) {
            interimIndicator.remove();
        }

        // Đặt lại trạng thái mic
        const micStatus = document.getElementById('mic-status-indicator');
        if (micStatus) {
            micStatus.textContent = 'Chưa bắt đầu ghi âm';
            micStatus.parentElement.classList.remove('recording');
        }

        // Cập nhật chỉ báo tiến độ
        updateProgressIndicators(data, 'voice');
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
        // Stop recording if active
        if (recognition) {
            try {
                recognition.stop();
                isRecording = false;
                
                // Update the mic button
                const micButton = document.getElementById('toggle-mic');
                if (micButton) {
                    micButton.classList.remove('pulse-recording');
                    micButton.querySelector('i').className = 'fas fa-microphone';
                }
                
                // Update the mic status
                const micStatus = document.getElementById('mic-status-indicator');
                if (micStatus) {
                    micStatus.textContent = 'Phỏng vấn đã kết thúc';
                    micStatus.parentElement.classList.remove('recording');
                }
            } catch (e) {
                console.error('Error stopping recognition during interview finish:', e);
            }
        }
        
        // Stop timer if running
        if (interviewTimer) {
            clearInterval(interviewTimer);
        }
        
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
        const resultMode = document.getElementById('result-mode');
        const totalScore = document.getElementById('total-score');
        const maxScore = document.getElementById('max-score');
        const totalScoreFill = document.getElementById('total-score-fill');
        
        if (resultName) resultName.textContent = userInfo.name;
        if (resultAge) resultAge.textContent = userInfo.age;
        if (resultJob) resultJob.textContent = userInfo.job;
        if (resultMode) resultMode.textContent = interviewMode === 'text' ? 'Chat' : 'Giọng nói';
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
    // If we're leaving the voice-interview-screen, ensure recording is stopped
    const currentVoiceScreen = document.getElementById('voice-interview-screen');
    if (currentVoiceScreen && currentVoiceScreen.classList.contains('active') && 
        screenId !== 'voice-interview-screen' && recognition) {
        try {
            recognition.stop();
            isRecording = false;
        } catch (e) {
            console.error('Error stopping recognition during screen switch:', e);
        }
    }
    
    const screens = document.querySelectorAll('.screen');
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
// Hàm đọc câu hỏi bằng giọng nói
function speakQuestion(text) {
    if ('speechSynthesis' in window) {
        // Dừng ghi âm nếu đang hoạt động để tránh ghi âm giọng hệ thống
        if (recognition && isRecording) {
            recognition.stop();
            isRecording = false;

            const mic_performance = document.getElementById('toggle-mic');
            if (micButton) {
                micButton.classList.remove('pulse-recording');
                micButton.querySelector('i').className = 'fas fa-microphone';
            }

            const micStatus = document.getElementById('mic-status-indicator');
            if (micStatus) {
                micStatus.textContent = 'Đang đọc câu hỏi...';
                micStatus.parentElement.classList.remove('recording');
            }
        }

        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = 'vi-VN';
        utterance.volume = 1.0;
        utterance.rate = 1.0;
        utterance.pitch = 1.0;

        // Chọn giọng tiếng Việt nếu có
        const voices = window.speechSynthesis.getVoices();
        const vietnameseVoice = voices.find(voice => voice.lang === 'vi-VN');
        if (vietnameseVoice) {
            utterance.voice = vietnameseVoice;
        }

        // Tự động bắt đầu ghi âm sau khi đọc xong, trừ khi mic bị tắt
        utterance.onend = function() {
            if (recognition && !isMicMuted) {
                try {
                    recognition.start();
                    isRecording = true;

                    const micButton = document.getElementById('toggle-mic');
                    if (micButton) {
                        micButton.classList.add('pulse-recording');
                        micButton.querySelector('i').className = 'fas fa-microphone-slash';
                    }

                    const micStatus = document.getElementById('mic-status-indicator');
                    if (micStatus) {
                        micStatus.textContent = 'Đang ghi âm...';
                        micStatus.parentElement.classList.add('recording');
                    }
                } catch (e) {
                    console.error('Error starting recognition after speaking:', e);
                    alert('Không thể bắt đầu ghi âm. Vui lòng kiểm tra quyền truy cập microphone.');
                }
            }
        };

        window.speechSynthesis.speak(utterance);
    } else {
        console.warn('Trình duyệt không hỗ trợ Text-to-Speech.');
        alert('Trình duyệt của bạn không hỗ trợ tính năng đọc câu hỏi bằng giọng nói. Vui lòng sử dụng Chrome hoặc Edge.');
    }
}

// Đảm bảo danh sách giọng nói được tải
window.speechSynthesis.onvoiceschanged = function() {
    // Có thể lưu danh sách giọng nói nếu cần
};
// Restart the interview
function restartInterview() {
    // Reset session
    sessionId = null;
    interviewMode = null;
    
    // Stop timer if running
    if (interviewTimer) {
        clearInterval(interviewTimer);
        interviewTimer = null;
    }
    
    // Ensure speech recognition is stopped
    if (recognition) {
        try {
            recognition.stop();
            isRecording = false;
            
            // Update the mic button
            const micButton = document.getElementById('toggle-mic');
            if (micButton) {
                micButton.classList.remove('pulse-recording');
                micButton.querySelector('i').className = 'fas fa-microphone';
            }
            
            // Update the mic status
            const micStatus = document.getElementById('mic-status-indicator');
            if (micStatus) {
                micStatus.textContent = 'Chưa bắt đầu ghi âm';
                micStatus.parentElement.classList.remove('recording');
            }
            
            // Clear any interim transcript
            const interimIndicator = document.getElementById('interim-transcript');
            if (interimIndicator) {
                interimIndicator.remove();
            }
        } catch (e) {
            console.error('Error stopping recognition during restart:', e);
        }
    }
    
    // Reset mode selection styling
    document.getElementById('select-text-mode').style.border = 'none';
    document.getElementById('select-voice-mode').style.border = 'none';
    
    // Reset mode buttons
    if (document.getElementById('toggle-mic')) {
        document.getElementById('toggle-mic').classList.remove('pulse-recording');
        document.getElementById('toggle-mic').querySelector('i').className = 'fas fa-microphone';
    }
    
    if (document.getElementById('toggle-camera')) {
        document.getElementById('toggle-camera').querySelector('i').className = 'fas fa-video';
    }
    
    // Switch to starting screen
    switchScreen('info-screen');
}

// Download results as text file
function downloadResults() {
    const resultName = document.getElementById('result-name');
    const resultAge = document.getElementById('result-age');
    const resultJob = document.getElementById('result-job');
    const resultMode = document.getElementById('result-mode');
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
    const mode = resultMode.textContent;
    const score = totalScore.textContent;
    const max = maxScore.textContent;
    const evaluation = evaluationText.textContent;
    
    let resultText = `PHIẾU ĐÁNH GIÁ PHỎNG VẤN\n`;
    resultText += `==============================================\n\n`;
    resultText += `Thông tin ứng viên:\n`;
    resultText += `- Họ và tên: ${name}\n`;
    resultText += `- Tuổi: ${age}\n`;
    resultText += `- Vị trí ứng tuyển: ${job}\n`;
    resultText += `- Phương thức phỏng vấn: ${mode}\n\n`;
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