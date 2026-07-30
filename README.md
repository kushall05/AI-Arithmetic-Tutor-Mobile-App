# AI Arithmetic Tutor 🧠📱🌐

> An Intelligent Mobile & Web Learning Application for Elementary & Middle School Students powered by AI-generated explanations, Socratic hints, adaptive practice, voice math, and gamification.

![AI Arithmetic Tutor Banner](https://img.shields.io/badge/Python-3.14-blue.svg) ![Flask](https://img.shields.io/badge/Flask-3.1-green.svg) ![Gemini API](https://img.shields.io/badge/AI-Gemini%20API-orange.svg) ![PWA Ready](https://img.shields.io/badge/PWA-Ready-success.svg) ![License](https://img.shields.io/badge/License-MIT-purple.svg)

---

## 🌐 Deploy to Web (Free Hosting)

### Option A: Render.com (Recommended for Python/Flask)
1. Go to [Render.com](https://render.com) and click **New + -> Web Service**.
2. Connect your GitHub repository: `https://github.com/kushall05/AI-Arithmetic-Tutor-Mobile-App`
3. Render will auto-detect `render.yaml` and deploy your Web Application instantly with a free `https://ai-arithmetic-tutor.onrender.com` link!

### Option B: Vercel
1. Go to [Vercel.com](https://vercel.com) and import your GitHub repository.
2. Vercel will detect `vercel.json` and deploy it as a Serverless Web Application.

---

## 🌟 Core Features

- 🌐 **Web & Mobile Hybrid**: Run as a Web App, PWA ("Add to Home Screen"), or Android APK.
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

## 🚀 Local Quick Start

```bash
pip install -r requirements.txt
python database.py
python app.py
```
Open **`http://127.0.0.1:5000`** in your browser.
