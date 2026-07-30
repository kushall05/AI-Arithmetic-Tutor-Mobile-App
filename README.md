# AI Arithmetic Tutor 🧠📱

> An Intelligent Mobile Learning Application for Elementary & Middle School Students powered by AI-generated explanations, Socratic hints, adaptive practice, voice math, and gamification.

![AI Arithmetic Tutor Banner](https://img.shields.io/badge/Python-3.14-blue.svg) ![Flask](https://img.shields.io/badge/Flask-3.1-green.svg) ![Gemini API](https://img.shields.io/badge/AI-Gemini%20API-orange.svg) ![License](https://img.shields.io/badge/License-MIT-purple.svg)

---

## 🌟 Core Features

- ➕ **Core Operations**: Addition, Subtraction, Multiplication, Division with 4 difficulty levels (Easy, Medium, Hard, Challenge).
- 🦉 **AI Mistake Tutor (Gemini API & Fallback Engine)**: Explains errors step-by-step with Professor Owl character, encouraging tone, and clear visual steps.
- 💡 **Socratic Hint System**: Provides 3 progressive clues without revealing the answer.
- 🎙️ **Voice Math Assistance**: Web Speech API integration reads problems aloud (TTS) and accepts spoken numeric answers.
- ✏️ **Interactive Scratchpad**: On-screen drawing canvas for scratch work during practice.
- ⏱️ **Timed Quiz & Daily Challenge**: 90-second mixed quiz with progress ring & daily math marathon.
- 🏆 **Gamification & Badges**: 10 unlockable achievement badges and live top-10 leaderboard.
- 📄 **Export PDF Performance Report**: Generates downloadable PDF reports with accuracy stats and AI teacher recommendations.
- 🌙 **Dark & Light Mode**: HSL color design system with instant theme switching.

---

## 🏗️ Architecture & Tech Stack

- **Frontend**: HTML5, Vanilla CSS3 (HSL design system, Glassmorphic UI), JavaScript (SPA Router, Canvas API, Chart.js, Confetti, Web Speech API).
- **Backend**: Python 3.14 + Flask 3.1 REST API server.
- **Database**: SQLite3 (`database.py`) with tables for Users, Questions, Quiz Results, Progress, AI History, Badges, User Badges, and Daily Challenges.
- **AI Integration**: Google Gemini API + Deterministic Fallback Math Solver.
- **PDF Generation**: ReportLab engine (`pdf_generator.py`).

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.9+ installed

### Setup & Launch

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/AI-Arithmetic-Tutor-Mobile-App.git
   cd AI-Arithmetic-Tutor-Mobile-App
   ```

2. **Install Dependencies**:
   ```bash
   pip install flask requests reportlab
   ```

3. **Initialize Database & Run Application**:
   ```bash
   python database.py
   python app.py
   ```

4. **Open in Browser**:
   Navigate to **`http://127.0.0.1:5000`**

*(Optional)* Set your Gemini API key in `app.py` or via the in-app **Profile & Settings** menu.

---

## 📄 License
MIT License
