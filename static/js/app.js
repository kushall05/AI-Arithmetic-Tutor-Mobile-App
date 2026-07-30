/* ==========================================================================
   AI ARITHMETIC TUTOR - CLIENT CORE APPLICATION (APP.JS)
   ========================================================================== */

const app = {
    currentUser: null,
    currentScreen: 'splashScreen',
    currentPractice: {
        operation: 'Addition',
        difficulty: 'Easy',
        questions: [],
        currentIndex: 0,
        currentQuestion: null,
        selectedChoice: null,
        hintLevel: 0,
        startTime: null
    },
    quizState: {
        active: false,
        questions: [],
        currentIndex: 0,
        score: 0,
        timer: null,
        secondsLeft: 60,
        startTime: null
    },
    scratchpad: {
        canvas: null,
        ctx: null,
        isDrawing: false
    },
    chartInstance: null,

    init() {
        this.loadTheme();
        this.checkLocalUser();
        this.initScratchpad();
    },

    // --- NAVIGATION & SCREEN ROUTER ---
    showScreen(screenId) {
        document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
        const target = document.getElementById(screenId);
        if (target) {
            target.classList.add('active');
            this.currentScreen = screenId;
        }

        // Update Bottom Navbar Active State
        document.querySelectorAll('.nav-item').forEach(btn => btn.classList.remove('active'));
        if (screenId === 'dashboardScreen') document.getElementById('navDash')?.classList.add('active');
        if (screenId === 'practiceScreen') document.getElementById('navPractice')?.classList.add('active');
        if (screenId === 'tutorScreen') document.getElementById('navTutor')?.classList.add('active');
        if (screenId === 'progressScreen') {
            document.getElementById('navProgress')?.classList.add('active');
            this.loadProgressData();
        }
        if (screenId === 'profileScreen') {
            document.getElementById('navProfile')?.classList.add('active');
            this.loadProfileData();
        }
        if (screenId === 'leaderboardScreen') {
            this.loadLeaderboardData();
            this.loadBadgesData();
        }

        // Show/Hide Top Header & Navbar based on screen
        const isSplash = (screenId === 'splashScreen');
        document.getElementById('appNavbar').style.display = isSplash ? 'none' : 'flex';
    },

    // --- AUTHENTICATION ---
    checkLocalUser() {
        const stored = localStorage.getItem('tutor_user');
        if (stored) {
            try {
                this.currentUser = JSON.parse(stored);
                this.updateUserHeader();
                this.showScreen('dashboardScreen');
                this.refreshDashboard();
            } catch (e) {
                localStorage.removeItem('tutor_user');
            }
        }
    },

    openAuthModal(tab = 'login') {
        document.getElementById('authModal').classList.remove('hidden');
        this.switchAuthTab(tab);
    },

    closeAuthModal() {
        document.getElementById('authModal').classList.add('hidden');
    },

    switchAuthTab(tab) {
        const loginTab = document.getElementById('tabLoginBtn');
        const regTab = document.getElementById('tabRegisterBtn');
        const loginForm = document.getElementById('loginForm');
        const regForm = document.getElementById('registerForm');

        if (tab === 'login') {
            loginTab.classList.add('active');
            regTab.classList.remove('active');
            loginForm.classList.remove('hidden');
            regForm.classList.add('hidden');
        } else {
            regTab.classList.add('active');
            loginTab.classList.remove('active');
            regForm.classList.remove('hidden');
            loginForm.classList.add('hidden');
        }
    },

    async handleLogin(e) {
        e.preventDefault();
        const username = document.getElementById('loginUsername').value;
        const password = document.getElementById('loginPassword').value;

        try {
            const res = await fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });
            const data = await res.json();
            if (data.success) {
                this.currentUser = data.user;
                localStorage.setItem('tutor_user', JSON.stringify(data.user));
                this.updateUserHeader();
                this.closeAuthModal();
                this.showScreen('dashboardScreen');
                this.refreshDashboard();
            } else {
                alert('Login failed: ' + data.error);
            }
        } catch (err) {
            alert('Server error connecting to backend.');
        }
    },

    async handleRegister(e) {
        e.preventDefault();
        const username = document.getElementById('regUsername').value;
        const email = document.getElementById('regEmail').value;
        const password = document.getElementById('regPassword').value;
        const grade_level = document.getElementById('regGrade').value;

        try {
            const res = await fetch('/api/auth/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, email, password, grade_level })
            });
            const data = await res.json();
            if (data.success) {
                this.currentUser = data.user;
                localStorage.setItem('tutor_user', JSON.stringify(data.user));
                this.updateUserHeader();
                this.closeAuthModal();
                this.showScreen('dashboardScreen');
                this.refreshDashboard();
            } else {
                alert('Registration failed: ' + data.error);
            }
        } catch (err) {
            alert('Server error creating user account.');
        }
    },

    loginDemoUser() {
        this.currentUser = {
            id: 1,
            username: 'DemoStudent',
            email: 'demo@tutor.com',
            grade_level: 'Grade 4',
            avatar: '🦊',
            points: 240,
            streak: 3
        };
        localStorage.setItem('tutor_user', JSON.stringify(this.currentUser));
        this.updateUserHeader();
        this.showScreen('dashboardScreen');
        this.refreshDashboard();
    },

    logout() {
        this.currentUser = null;
        localStorage.removeItem('tutor_user');
        this.showScreen('splashScreen');
    },

    updateUserHeader() {
        if (!this.currentUser) return;
        document.getElementById('userGradeDisplay').textContent = this.currentUser.grade_level;
        document.getElementById('streakDisplay').textContent = this.currentUser.streak;
        document.getElementById('pointsDisplay').textContent = this.currentUser.points;
    },

    async refreshDashboard() {
        if (!this.currentUser) return;

        document.getElementById('dashGreeting').textContent = `Hello, ${this.currentUser.username}! 👋`;
        document.getElementById('dashAvatar').textContent = this.currentUser.avatar || '🦊';

        try {
            const res = await fetch(`/api/dashboard/${this.currentUser.id}`);
            const data = await res.json();
            if (data.success) {
                this.currentUser = { ...this.currentUser, ...data.user };
                localStorage.setItem('tutor_user', JSON.stringify(this.currentUser));
                this.updateUserHeader();

                // Update Level Badges on Cards
                data.progress.forEach(p => {
                    const el = document.getElementById(`lvl${p.operation}`);
                    if (el) el.textContent = `Level ${p.mastery_level} • ${p.correct_count} Solved`;
                });
            }
        } catch (e) {
            console.error('Error refreshing dashboard:', e);
        }
    },

    // --- PRACTICE MODULE ---
    async startPractice(operation) {
        if (!this.currentUser) return this.openAuthModal('login');

        this.currentPractice.operation = operation;
        this.currentPractice.difficulty = document.getElementById('diffSelect').value || 'Easy';
        this.currentPractice.currentIndex = 0;

        document.getElementById('practiceTitle').textContent = `${operation} Practice`;
        this.showScreen('practiceScreen');

        // Fetch 5 practice questions
        try {
            const res = await fetch('/api/practice/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    operation: operation,
                    difficulty: this.currentPractice.difficulty,
                    count: 5
                })
            });
            const data = await res.json();
            if (data.success && data.questions.length > 0) {
                this.currentPractice.questions = data.questions;
                this.renderPracticeQuestion();
            }
        } catch (e) {
            alert('Failed to generate practice questions.');
        }
    },

    changeDifficulty(diff) {
        this.currentPractice.difficulty = diff;
        this.startPractice(this.currentPractice.operation);
    },

    renderPracticeQuestion() {
        const q = this.currentPractice.questions[this.currentPractice.currentIndex];
        this.currentPractice.currentQuestion = q;
        this.currentPractice.selectedChoice = null;
        this.currentPractice.hintLevel = 0;
        this.currentPractice.startTime = Date.now();

        // Update UI
        document.getElementById('qCounter').textContent = `Question ${this.currentPractice.currentIndex + 1} of ${this.currentPractice.questions.length}`;
        document.getElementById('questionText').textContent = q.question_text;
        document.getElementById('hintCard').classList.add('hidden');
        document.getElementById('feedbackModal').classList.add('hidden');

        // Speak question out loud (TTS)
        VoiceModule.speak(q.question_text.replace('?', ''));

        // Render Choices
        const choicesGrid = document.getElementById('choicesGrid');
        choicesGrid.innerHTML = '';
        q.choices.forEach(val => {
            const btn = document.createElement('button');
            btn.className = 'choice-btn';
            btn.textContent = val;
            btn.onclick = () => this.selectPracticeChoice(val, btn);
            choicesGrid.appendChild(btn);
        });
    },

    async selectPracticeChoice(val, btnEl) {
        if (this.currentPractice.selectedChoice !== null) return; // Prevent double select
        this.currentPractice.selectedChoice = val;

        const timeTaken = Math.round((Date.now() - this.currentPractice.startTime) / 1000);
        const q = this.currentPractice.currentQuestion;

        // Visual selection state
        btnEl.classList.add('selected');

        try {
            const res = await fetch('/api/practice/submit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: this.currentUser.id,
                    operation: q.operation,
                    difficulty: q.difficulty,
                    operand1: q.operand1,
                    operand2: q.operand2,
                    user_answer: val,
                    correct_answer: q.correct_answer,
                    time_taken_seconds: timeTaken,
                    gemini_api_key: this.currentUser.gemini_api_key
                })
            });
            const data = await res.json();
            if (data.success) {
                // Show Answer Colors
                if (data.is_correct) {
                    btnEl.classList.remove('selected');
                    btnEl.classList.add('correct');
                    this.showFeedbackModal(true, data.gained_points);
                    confetti({ particleCount: 50, spread: 60, origin: { y: 0.7 } });
                    VoiceModule.speak('Correct! Outstanding work!');
                } else {
                    btnEl.classList.remove('selected');
                    btnEl.classList.add('incorrect');
                    
                    // Highlight correct answer button
                    document.querySelectorAll('.choice-btn').forEach(b => {
                        if (parseInt(b.textContent) === q.correct_answer) {
                            b.classList.add('correct');
                        }
                    });

                    this.showFeedbackModal(false, 0, data.explanation);
                    VoiceModule.speak('Not quite, but mistakes help us learn! Check Professor Owl\'s explanation.');
                }

                // Update Points
                this.currentUser.points += data.gained_points;
                document.getElementById('pointsDisplay').textContent = this.currentUser.points;
            }
        } catch (e) {
            console.error('Error submitting answer:', e);
        }
    },

    showFeedbackModal(isCorrect, pointsGained, explanationText = null) {
        const modal = document.getElementById('feedbackModal');
        const icon = document.getElementById('fbIcon');
        const title = document.getElementById('fbTitle');
        const sub = document.getElementById('fbSub');
        const expBox = document.getElementById('aiExplanationBox');
        const expContent = document.getElementById('aiExpContent');

        modal.classList.remove('hidden');

        if (isCorrect) {
            icon.textContent = '🎉';
            title.textContent = 'Correct Answer!';
            sub.textContent = `+${pointsGained} XP Earned! Great speed!`;
            expBox.classList.add('hidden');
        } else {
            icon.textContent = '💡';
            title.textContent = 'Keep Learning!';
            sub.textContent = 'Here is how to solve it step-by-step:';
            expBox.classList.remove('hidden');
            expContent.innerHTML = this.formatMarkdownText(explanationText || 'Solving step by step...');
        }
    },

    nextPracticeQuestion() {
        document.getElementById('feedbackModal').classList.add('hidden');
        this.currentPractice.currentIndex++;
        if (this.currentPractice.currentIndex < this.currentPractice.questions.length) {
            this.renderPracticeQuestion();
        } else {
            alert('🎉 Practice session completed! You earned bonus XP!');
            this.showScreen('dashboardScreen');
            this.refreshDashboard();
        }
    },

    async requestHint() {
        const q = this.currentPractice.currentQuestion;
        if (!q) return;

        this.currentPractice.hintLevel = Math.min(3, this.currentPractice.hintLevel + 1);

        try {
            const res = await fetch('/api/practice/hint', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    operand1: q.operand1,
                    operand2: q.operand2,
                    operation: q.operation,
                    hint_level: this.currentPractice.hintLevel,
                    gemini_api_key: this.currentUser?.gemini_api_key
                })
            });
            const data = await res.json();
            if (data.success) {
                const hintCard = document.getElementById('hintCard');
                const hintContent = document.getElementById('hintContent');
                hintCard.classList.remove('hidden');
                hintContent.innerHTML = this.formatMarkdownText(data.hint);
                VoiceModule.speak("Here is a hint!");
            }
        } catch (e) {
            alert('Unable to fetch hint.');
        }
    },

    startVoiceRecognition() {
        VoiceModule.listen((numericAnswer, fullText) => {
            // Find choice matching number
            const btns = document.querySelectorAll('.choice-btn');
            let matched = false;
            btns.forEach(btn => {
                if (parseInt(btn.textContent) === numericAnswer) {
                    matched = true;
                    btn.click();
                }
            });
            if (!matched) {
                alert(`Voice recognized: "${fullText}" (${numericAnswer}), but it is not one of the choices.`);
            }
        });
    },

    toggleVoiceTTS() {
        const q = this.currentPractice.currentQuestion;
        if (q) VoiceModule.speak(q.question_text);
    },

    // --- SCRATCHPAD DRAWING CANVAS ---
    initScratchpad() {
        const canvas = document.getElementById('scratchpadCanvas');
        if (!canvas) return;
        this.scratchpad.canvas = canvas;
        this.scratchpad.ctx = canvas.getContext('2d');

        const ctx = this.scratchpad.ctx;
        ctx.strokeStyle = '#4F46E5';
        ctx.lineWidth = 3;
        ctx.lineCap = 'round';

        const startDrawing = (e) => {
            this.scratchpad.isDrawing = true;
            ctx.beginPath();
            const rect = canvas.getBoundingClientRect();
            const clientX = e.touches ? e.touches[0].clientX : e.clientX;
            const clientY = e.touches ? e.touches[0].clientY : e.clientY;
            ctx.moveTo(clientX - rect.left, clientY - rect.top);
        };

        const draw = (e) => {
            if (!this.scratchpad.isDrawing) return;
            const rect = canvas.getBoundingClientRect();
            const clientX = e.touches ? e.touches[0].clientX : e.clientX;
            const clientY = e.touches ? e.touches[0].clientY : e.clientY;
            ctx.lineTo(clientX - rect.left, clientY - rect.top);
            ctx.stroke();
        };

        const stopDrawing = () => {
            this.scratchpad.isDrawing = false;
        };

        canvas.addEventListener('mousedown', startDrawing);
        canvas.addEventListener('mousemove', draw);
        canvas.addEventListener('mouseup', stopDrawing);
        canvas.addEventListener('touchstart', startDrawing);
        canvas.addEventListener('touchmove', draw);
        canvas.addEventListener('touchend', stopDrawing);
    },

    toggleScratchpad() {
        const box = document.getElementById('scratchpadBox');
        box.classList.toggle('hidden');
    },

    clearScratchpad() {
        if (this.scratchpad.canvas && this.scratchpad.ctx) {
            this.scratchpad.ctx.clearRect(0, 0, this.scratchpad.canvas.width, this.scratchpad.canvas.height);
        }
    },

    // --- AI TUTOR CHAT ---
    async sendChatMessage() {
        const input = document.getElementById('chatInput');
        const msg = input.value.strip ? input.value.strip() : input.value.trim();
        if (!msg) return;

        input.value = '';
        const chatContainer = document.getElementById('chatContainer');

        // Append User Bubble
        const userBubble = document.createElement('div');
        userBubble.className = 'chat-bubble user-bubble';
        userBubble.innerHTML = `<div class="bubble-sender">You</div><div class="bubble-text">${msg}</div>`;
        chatContainer.appendChild(userBubble);
        chatContainer.scrollTop = chatContainer.scrollHeight;

        // Append Loading Bot Bubble
        const botBubble = document.createElement('div');
        botBubble.className = 'chat-bubble bot-bubble';
        botBubble.innerHTML = `<div class="bubble-sender">🦉 Professor Owl</div><div class="bubble-text">Thinking... 🧠</div>`;
        chatContainer.appendChild(botBubble);
        chatContainer.scrollTop = chatContainer.scrollHeight;

        try {
            const res = await fetch('/api/ai/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: this.currentUser ? this.currentUser.id : null,
                    message: msg,
                    gemini_api_key: this.currentUser?.gemini_api_key
                })
            });
            const data = await res.json();
            if (data.success) {
                botBubble.querySelector('.bubble-text').innerHTML = this.formatMarkdownText(data.reply);
                VoiceModule.speak("Here is what I found!");
            } else {
                botBubble.querySelector('.bubble-text').textContent = 'Sorry, I could not answer that right now.';
            }
        } catch (e) {
            botBubble.querySelector('.bubble-text').textContent = 'Error connecting to AI Tutor.';
        }
        chatContainer.scrollTop = chatContainer.scrollHeight;
    },

    // --- TIMED QUIZ MODULE ---
    async startQuizModal() {
        if (!this.currentUser) return this.openAuthModal('login');

        try {
            const res = await fetch('/api/practice/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ operation: 'Mixed', difficulty: 'Medium', count: 10 })
            });
            const data = await res.json();
            if (data.success && data.questions.length > 0) {
                this.quizState = {
                    active: true,
                    questions: data.questions,
                    currentIndex: 0,
                    score: 0,
                    secondsLeft: 90,
                    startTime: Date.now(),
                    timer: null
                };
                this.showScreen('quizScreen');
                this.renderQuizQuestion();
                this.startQuizTimer();
            }
        } catch (e) {
            alert('Failed to start quiz.');
        }
    },

    startQuizTimer() {
        clearInterval(this.quizState.timer);
        this.quizState.timer = setInterval(() => {
            this.quizState.secondsLeft--;
            const mins = Math.floor(this.quizState.secondsLeft / 60);
            const secs = this.quizState.secondsLeft % 60;
            document.getElementById('quizTimer').textContent = `⏱️ ${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;

            if (this.quizState.secondsLeft <= 0) {
                clearInterval(this.quizState.timer);
                this.finishQuiz();
            }
        }, 1000);
    },

    renderQuizQuestion() {
        const q = this.quizState.questions[this.quizState.currentIndex];
        document.getElementById('quizQCounter').textContent = `Question ${this.quizState.currentIndex + 1} of 10`;
        document.getElementById('quizQuestionText').textContent = q.question_text;
        document.getElementById('quizLiveScore').textContent = `Score: ${this.quizState.score}/10`;

        const pct = ((this.quizState.currentIndex + 1) / 10) * 100;
        document.getElementById('quizProgressFill').style.width = `${pct}%`;

        const grid = document.getElementById('quizChoicesGrid');
        grid.innerHTML = '';
        q.choices.forEach(val => {
            const btn = document.createElement('button');
            btn.className = 'choice-btn';
            btn.textContent = val;
            btn.onclick = () => {
                if (val === q.correct_answer) {
                    this.quizState.score++;
                }
                this.quizState.currentIndex++;
                if (this.quizState.currentIndex < 10) {
                    this.renderQuizQuestion();
                } else {
                    this.finishQuiz();
                }
            };
            grid.appendChild(btn);
        });
    },

    async finishQuiz() {
        clearInterval(this.quizState.timer);
        const timeTaken = Math.round((Date.now() - this.quizState.startTime) / 1000);

        try {
            const res = await fetch('/api/quiz/submit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: this.currentUser.id,
                    operation: 'Mixed',
                    difficulty: 'Medium',
                    score: this.quizState.score,
                    total_questions: 10,
                    time_taken_seconds: timeTaken
                })
            });
            const data = await res.json();
            if (data.success) {
                const acc = Math.round(data.accuracy);
                document.getElementById('resScoreText').textContent = `${data.score} / 10`;
                document.getElementById('resAccText').textContent = `${acc}%`;
                document.getElementById('resXPText').textContent = `+${data.gained_points} XP`;

                if (acc >= 80) {
                    confetti({ particleCount: 100, spread: 70, origin: { y: 0.6 } });
                    VoiceModule.speak('Congratulations! Excellent quiz performance!');
                }

                this.showScreen('resultsScreen');
                this.refreshDashboard();
            }
        } catch (e) {
            console.error('Error submitting quiz:', e);
        }
    },

    startDailyChallenge() {
        this.startQuizModal();
    },

    // --- PROGRESS & ANALYTICS ---
    async loadProgressData() {
        if (!this.currentUser) return;

        try {
            const res = await fetch(`/api/progress/${this.currentUser.id}`);
            const data = await res.json();
            if (data.success) {
                const ops = data.progress;
                const labels = [];
                const accData = [];

                ops.forEach(p => {
                    const att = p.total_attempted;
                    const corr = p.correct_count;
                    const acc = att > 0 ? Math.round((corr / att) * 100) : 0;

                    labels.push(p.operation);
                    accData.push(acc);

                    const labelEl = document.getElementById(`${p.operation.slice(0,3).toLowerCase()}AccLabel`);
                    const fillEl = document.getElementById(`${p.operation.slice(0,3).toLowerCase()}BarFill`);

                    if (labelEl) labelEl.textContent = `${acc}%`;
                    if (fillEl) fillEl.style.width = `${acc}%`;
                });

                this.renderChart(labels, accData);
            }
        } catch (e) {
            console.error('Error loading progress:', e);
        }
    },

    renderChart(labels, dataValues) {
        const ctx = document.getElementById('progressChart')?.getContext('2d');
        if (!ctx) return;

        if (this.chartInstance) {
            this.chartInstance.destroy();
        }

        this.chartInstance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Accuracy (%)',
                    data: dataValues,
                    backgroundColor: ['#10B981', '#6366F1', '#F59E0B', '#EC4899'],
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: { beginAtZero: true, max: 100 }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });
    },

    async downloadPDFReport() {
        if (!this.currentUser) return this.openAuthModal('login');
        window.open(`/api/report/pdf/${this.currentUser.id}`, '_blank');
    },

    // --- LEADERBOARD & BADGES ---
    switchTab(tab) {
        const lbBtn = document.getElementById('tabLeaderboard');
        const bgBtn = document.getElementById('tabBadges');
        const lbContent = document.getElementById('leaderboardTabContent');
        const bgContent = document.getElementById('badgesTabContent');

        if (tab === 'leaderboard') {
            lbBtn.classList.add('active');
            bgBtn.classList.remove('active');
            lbContent.classList.remove('hidden');
            bgContent.classList.add('hidden');
        } else {
            bgBtn.classList.add('active');
            lbBtn.classList.remove('active');
            bgContent.classList.remove('hidden');
            lbContent.classList.add('hidden');
        }
    },

    async loadLeaderboardData() {
        try {
            const res = await fetch('/api/leaderboard');
            const data = await res.json();
            if (data.success) {
                const list = document.getElementById('leaderboardList');
                list.innerHTML = '';
                data.leaderboard.forEach((item, index) => {
                    const row = document.createElement('div');
                    row.className = 'lb-item';
                    row.innerHTML = `
                        <div class="lb-rank">#${index + 1}</div>
                        <div class="lb-avatar">${item.avatar || '🦊'}</div>
                        <div class="lb-user-info">
                            <div class="lb-name">${item.username}</div>
                            <div class="lb-grade">${item.grade_level} • 🔥 ${item.streak} Streak</div>
                        </div>
                        <div class="lb-score">${item.points} XP</div>
                    `;
                    list.appendChild(row);
                });
            }
        } catch (e) {
            console.error('Error loading leaderboard:', e);
        }
    },

    async loadBadgesData() {
        if (!this.currentUser) return;
        try {
            const res = await fetch(`/api/badges/${this.currentUser.id}`);
            const data = await res.json();
            if (data.success) {
                const grid = document.getElementById('badgesGrid');
                grid.innerHTML = '';
                data.badges.forEach(b => {
                    const card = document.createElement('div');
                    card.className = `badge-card ${b.is_unlocked ? 'unlocked' : ''}`;
                    card.innerHTML = `
                        <div class="badge-icon">${b.icon}</div>
                        <div class="badge-title">${b.title}</div>
                        <div class="badge-desc">${b.description}</div>
                    `;
                    grid.appendChild(card);
                });
            }
        } catch (e) {
            console.error('Error loading badges:', e);
        }
    },

    // --- PROFILE & SETTINGS ---
    loadProfileData() {
        if (!this.currentUser) return;
        document.getElementById('profileAvatar').textContent = this.currentUser.avatar || '🦊';
        document.getElementById('profileName').textContent = this.currentUser.username;
        document.getElementById('profileEmail').textContent = this.currentUser.email || 'student@example.com';
        document.getElementById('settingGrade').value = this.currentUser.grade_level || 'Grade 3';
        document.getElementById('settingApiKey').value = this.currentUser.gemini_api_key || '';
    },

    async saveProfileSettings() {
        if (!this.currentUser) return;
        const grade = document.getElementById('settingGrade').value;
        const apiKey = document.getElementById('settingApiKey').value;

        try {
            const res = await fetch('/api/auth/update_settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: this.currentUser.id,
                    avatar: this.currentUser.avatar || '🦊',
                    grade_level: grade,
                    gemini_api_key: apiKey
                })
            });
            const data = await res.json();
            if (data.success) {
                this.currentUser.grade_level = grade;
                this.currentUser.gemini_api_key = apiKey;
                localStorage.setItem('tutor_user', JSON.stringify(this.currentUser));
                this.updateUserHeader();
            }
        } catch (e) {
            console.error('Error saving settings:', e);
        }
    },

    openAvatarPicker() {
        const avatars = ['🦊', '🧙‍♂️', '🚀', '🐱', '🐼', '🦁', '🤖', '👑'];
        const chosen = prompt('Choose your avatar emoji:\n' + avatars.join('  '));
        if (chosen && avatars.includes(chosen.trim())) {
            this.currentUser.avatar = chosen.trim();
            document.getElementById('profileAvatar').textContent = chosen.trim();
            this.saveProfileSettings();
        }
    },

    // --- THEME & UTILITIES ---
    loadTheme() {
        document.documentElement.setAttribute('data-theme', 'dark');
    },

    formatMarkdownText(text) {
        if (!text) return '';
        let formatted = text
            .replace(/### (.*?)\n/g, '<h4 style="margin:6px 0; color:var(--primary);">$1</h4>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`([^`]+)`/g, '<code style="background:var(--bg-card); padding:2px 4px; border-radius:4px;">$1</code>')
            .replace(/\n/g, '<br>');
        return formatted;
    }
};

document.addEventListener('DOMContentLoaded', () => {
    app.init();
});
