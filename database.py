import sqlite3
import json
import os
import hashlib
from datetime import datetime, date

def get_db_path():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    if os.environ.get("VERCEL") or not os.access(base_dir, os.W_OK):
        return "/tmp/tutor.db"
    return os.path.join(base_dir, "tutor.db")

def get_db_connection():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            grade_level TEXT DEFAULT 'Grade 3',
            avatar TEXT DEFAULT '🧙‍♂️',
            points INTEGER DEFAULT 100,
            streak INTEGER DEFAULT 1,
            last_active_date TEXT,
            gemini_api_key TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 2. Questions Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            operation TEXT NOT NULL, -- Addition, Subtraction, Multiplication, Division
            difficulty TEXT NOT NULL, -- Easy, Medium, Hard, Challenge
            question_text TEXT NOT NULL,
            operand1 INTEGER NOT NULL,
            operand2 INTEGER NOT NULL,
            correct_answer INTEGER NOT NULL,
            choices_json TEXT NOT NULL,
            explanation TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 3. Quiz Results Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quiz_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            quiz_type TEXT NOT NULL, -- Practice or Quiz
            operation TEXT NOT NULL,
            difficulty TEXT NOT NULL,
            score INTEGER NOT NULL,
            total_questions INTEGER NOT NULL,
            accuracy REAL NOT NULL,
            time_taken_seconds INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # 4. Progress Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            operation TEXT NOT NULL,
            total_attempted INTEGER DEFAULT 0,
            correct_count INTEGER DEFAULT 0,
            total_time_seconds INTEGER DEFAULT 0,
            mastery_level INTEGER DEFAULT 1,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, operation),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # 5. AI History Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            question_text TEXT NOT NULL,
            user_answer INTEGER,
            correct_answer INTEGER NOT NULL,
            explanation_type TEXT DEFAULT 'mistake_explanation', -- mistake_explanation, hint, chat
            response_text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # 6. Badges Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS badges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            icon TEXT NOT NULL,
            category TEXT DEFAULT 'general',
            requirement_value INTEGER DEFAULT 1
        )
    ''')

    # 7. User Badges Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_badges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            badge_id INTEGER NOT NULL,
            unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, badge_id),
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (badge_id) REFERENCES badges (id)
        )
    ''')

    # 8. Daily Challenges Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_challenges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            challenge_date TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            questions_json TEXT NOT NULL,
            reward_points INTEGER DEFAULT 50
        )
    ''')

    # Seed Default Badges if empty
    cursor.execute("SELECT COUNT(*) FROM badges")
    if cursor.fetchone()[0] == 0:
        seed_badges = [
            ('first_step', 'First Step', 'Complete your very first arithmetic question', '🚀', 'general', 1),
            ('streak_3', 'On Fire', 'Maintain a 3-day practice streak', '🔥', 'streak', 3),
            ('streak_7', 'Unstoppable', 'Maintain a 7-day practice streak', '⚡', 'streak', 7),
            ('add_master', 'Addition Ace', 'Solve 25 Addition problems correctly', '➕', 'operation', 25),
            ('sub_master', 'Subtraction Star', 'Solve 25 Subtraction problems correctly', '➖', 'operation', 25),
            ('mul_master', 'Multiplication Wizard', 'Solve 25 Multiplication problems correctly', '✖️', 'operation', 25),
            ('div_master', 'Division Dynamo', 'Solve 25 Division problems correctly', '➗', 'operation', 25),
            ('quiz_champion', 'Quiz Champion', 'Score 100% on any Arithmetic Quiz', '🏆', 'quiz', 1),
            ('ai_scholar', 'AI Scholar', 'Ask the AI Tutor for 5 step-by-step explanations', '🧠', 'ai', 5),
            ('voice_master', 'Voice Scholar', 'Solve a question using Voice Input', '🎙️', 'voice', 1)
        ]
        cursor.executemany(
            "INSERT INTO badges (code, title, description, icon, category, requirement_value) VALUES (?, ?, ?, ?, ?, ?)",
            seed_badges
        )

    # Seed Default Demo User if empty
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        demo_pass = hash_password("student123")
        today_str = date.today().isoformat()
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, grade_level, avatar, points, streak, last_active_date)
            VALUES ('DemoStudent', 'demo@tutor.com', ?, 'Grade 4', '🦊', 240, 3, ?)
        ''', (demo_pass, today_str))
        demo_id = cursor.lastrowid

        # Seed progress for Demo User
        operations = [
            ('Addition', 20, 18, 240, 3),
            ('Subtraction', 15, 12, 200, 2),
            ('Multiplication', 12, 9, 180, 2),
            ('Division', 10, 7, 150, 1)
        ]
        for op, att, corr, tm, lvl in operations:
            cursor.execute('''
                INSERT INTO progress (user_id, operation, total_attempted, correct_count, total_time_seconds, mastery_level)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (demo_id, op, att, corr, tm, lvl))

        # Award first badge to demo user
        cursor.execute("SELECT id FROM badges WHERE code = 'first_step'")
        badge_row = cursor.fetchone()
        if badge_row:
            cursor.execute("INSERT OR IGNORE INTO user_badges (user_id, badge_id) VALUES (?, ?)", (demo_id, badge_row[0]))

    conn.commit()
    conn.close()
    print("Database initialized successfully.")

if __name__ == "__main__":
    init_db()
