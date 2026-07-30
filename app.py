import os
import json
import random
import sqlite3
from datetime import datetime, date
import io
from flask import Flask, request, jsonify, render_template, send_file, Response

from database import get_db_connection, init_db, hash_password
import ai_engine
import pdf_generator

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-tutor-key-2026'

# Ensure Database is Initialized on Start
init_db()

# --- HELPER FUNCTIONS ---
def update_user_streak(cursor, user_id):
    cursor.execute("SELECT last_active_date, streak FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        return 1
    
    last_date_str, streak = row['last_active_date'], row['streak']
    today_str = date.today().isoformat()
    
    if last_date_str == today_str:
        return streak
    
    if last_date_str:
        try:
            last_d = date.fromisoformat(last_date_str)
            diff = (date.today() - last_d).days
            if diff == 1:
                new_streak = streak + 1
            elif diff > 1:
                new_streak = 1
            else:
                new_streak = streak
        except Exception:
            new_streak = 1
    else:
        new_streak = 1

    cursor.execute("UPDATE users SET streak = ?, last_active_date = ? WHERE id = ?", (new_streak, today_str, user_id))
    return new_streak

def check_and_award_badges(conn, user_id):
    cursor = conn.cursor()
    unlocked_new = []

    cursor.execute("SELECT points, streak FROM users WHERE id = ?", (user_id,))
    user_row = cursor.fetchone()
    if not user_row:
        return []

    streak = user_row['streak']

    # Fetch user's existing badges
    cursor.execute("SELECT badge_id FROM user_badges WHERE user_id = ?", (user_id,))
    existing_badge_ids = {r[0] for r in cursor.fetchall()}

    # Fetch all badges
    cursor.execute("SELECT * FROM badges")
    all_badges = cursor.fetchall()

    # Progress stats
    cursor.execute("SELECT operation, correct_count FROM progress WHERE user_id = ?", (user_id,))
    op_counts = {r['operation']: r['correct_count'] for r in cursor.fetchall()}

    # Total questions answered
    total_correct = sum(op_counts.values())

    for badge in all_badges:
        b_id = badge['id']
        code = badge['code']
        req_val = badge['requirement_value']

        if b_id in existing_badge_ids:
            continue

        should_unlock = False

        if code == 'first_step' and total_correct >= 1:
            should_unlock = True
        elif code == 'streak_3' and streak >= 3:
            should_unlock = True
        elif code == 'streak_7' and streak >= 7:
            should_unlock = True
        elif code == 'add_master' and op_counts.get('Addition', 0) >= 25:
            should_unlock = True
        elif code == 'sub_master' and op_counts.get('Subtraction', 0) >= 25:
            should_unlock = True
        elif code == 'mul_master' and op_counts.get('Multiplication', 0) >= 25:
            should_unlock = True
        elif code == 'div_master' and op_counts.get('Division', 0) >= 25:
            should_unlock = True

        if should_unlock:
            cursor.execute("INSERT OR IGNORE INTO user_badges (user_id, badge_id) VALUES (?, ?)", (user_id, b_id))
            unlocked_new.append(dict(badge))

    conn.commit()
    return unlocked_new

def generate_math_problem(operation, difficulty):
    # Difficulty ranges
    if difficulty == "Easy":
        min_val, max_val = 1, 12
    elif difficulty == "Medium":
        min_val, max_val = 10, 50
    elif difficulty == "Hard":
        min_val, max_val = 20, 100
    else: # Challenge
        min_val, max_val = 50, 250

    if operation == "Addition":
        a = random.randint(min_val, max_val)
        b = random.randint(min_val, max_val)
        correct = a + b
        symbol = "+"
    elif operation == "Subtraction":
        a = random.randint(min_val + 5, max_val + 10)
        b = random.randint(min_val, a) # ensure positive result
        correct = a - b
        symbol = "-"
    elif operation == "Multiplication":
        if difficulty == "Easy":
            a, b = random.randint(1, 10), random.randint(1, 10)
        elif difficulty == "Medium":
            a, b = random.randint(2, 12), random.randint(2, 15)
        else:
            a, b = random.randint(5, 20), random.randint(3, 15)
        correct = a * b
        symbol = "×"
    else: # Division
        if difficulty == "Easy":
            b = random.randint(1, 10)
            correct = random.randint(1, 10)
        elif difficulty == "Medium":
            b = random.randint(2, 12)
            correct = random.randint(2, 12)
        else:
            b = random.randint(3, 15)
            correct = random.randint(5, 20)
        a = b * correct # clean division
        symbol = "÷"

    question_text = f"What is {a} {symbol} {b}?"

    # Generate 3 plausible distractors
    distractors = set()
    offsets = [-2, -1, 1, 2, -10, 10, -5, 5]
    random.shuffle(offsets)
    for offset in offsets:
        cand = correct + offset
        if cand > 0 and cand != correct:
            distractors.add(cand)
        if len(distractors) == 3:
            break

    while len(distractors) < 3:
        cand = correct + random.randint(1, 10)
        if cand != correct:
            distractors.add(cand)

    choices = list(distractors) + [correct]
    random.shuffle(choices)

    return {
        "operation": operation,
        "difficulty": difficulty,
        "question_text": question_text,
        "operand1": a,
        "operand2": b,
        "correct_answer": correct,
        "choices": choices
    }

# --- ROUTES ---

@app.route("/")
def index():
    return render_template("index.html")

# 1. Auth Endpoints
@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.json or {}
    username = data.get("username", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()
    grade = data.get("grade_level", "Grade 3")

    if not username or not email or not password:
        return jsonify({"success": False, "error": "All fields are required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        pass_hash = hash_password(password)
        today_str = date.today().isoformat()
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, grade_level, last_active_date)
            VALUES (?, ?, ?, ?, ?)
        ''', (username, email, pass_hash, grade, today_str))
        user_id = cursor.lastrowid

        # Init progress records for 4 operations
        for op in ["Addition", "Subtraction", "Multiplication", "Division"]:
            cursor.execute('''
                INSERT INTO progress (user_id, operation, total_attempted, correct_count, total_time_seconds, mastery_level)
                VALUES (?, ?, 0, 0, 0, 1)
            ''', (user_id, op))

        conn.commit()
        
        # Award First Step Badge
        check_and_award_badges(conn, user_id)

        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user_row = dict(cursor.fetchone())
        del user_row["password_hash"]

        conn.close()
        return jsonify({"success": True, "user": user_row})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"success": False, "error": "Username or Email already exists"}), 400

@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.json or {}
    username_or_email = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username_or_email or not password:
        return jsonify({"success": False, "error": "Username and password required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    pass_hash = hash_password(password)
    cursor.execute('''
        SELECT * FROM users WHERE (username = ? OR email = ?) AND password_hash = ?
    ''', (username_or_email, username_or_email, pass_hash))

    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({"success": False, "error": "Invalid username or password"}), 401

    user_dict = dict(row)
    user_id = user_dict["id"]
    
    # Update Streak
    streak = update_user_streak(cursor, user_id)
    user_dict["streak"] = streak
    conn.commit()

    # Check Badges
    check_and_award_badges(conn, user_id)

    del user_dict["password_hash"]
    conn.close()
    return jsonify({"success": True, "user": user_dict})

@app.route("/api/auth/user/<int:user_id>", methods=["GET"])
def get_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email, grade_level, avatar, points, streak, gemini_api_key, created_at FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return jsonify({"success": False, "error": "User not found"}), 404
    return jsonify({"success": True, "user": dict(row)})

@app.route("/api/auth/update_settings", methods=["POST"])
def update_settings():
    data = request.json or {}
    user_id = data.get("user_id")
    avatar = data.get("avatar")
    grade_level = data.get("grade_level")
    gemini_key = data.get("gemini_api_key", "").strip()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE users SET avatar = ?, grade_level = ?, gemini_api_key = ? WHERE id = ?
    ''', (avatar, grade_level, gemini_key, user_id))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": "Settings updated successfully"})

# 2. Practice & Quiz Question Endpoints
@app.route("/api/practice/generate", methods=["POST"])
def generate_questions():
    data = request.json or {}
    operation = data.get("operation", "Addition")
    difficulty = data.get("difficulty", "Easy")
    count = min(int(data.get("count", 5)), 20)

    questions = []
    for _ in range(count):
        if operation == "Mixed":
            actual_op = random.choice(["Addition", "Subtraction", "Multiplication", "Division"])
        else:
            actual_op = operation
        q = generate_math_problem(actual_op, difficulty)
        questions.append(q)

    return jsonify({"success": True, "questions": questions})

@app.route("/api/practice/submit", methods=["POST"])
def submit_answer():
    data = request.json or {}
    user_id = data.get("user_id")
    operation = data.get("operation", "Addition")
    difficulty = data.get("difficulty", "Easy")
    operand1 = int(data.get("operand1", 0))
    operand2 = int(data.get("operand2", 0))
    user_ans = int(data.get("user_answer", 0))
    correct_ans = int(data.get("correct_answer", 0))
    time_taken = int(data.get("time_taken_seconds", 5))
    user_key = data.get("gemini_api_key")

    is_correct = (user_ans == correct_ans)

    conn = get_db_connection()
    cursor = conn.cursor()

    # Points logic: Easy=10, Medium=15, Hard=20, Challenge=30
    pts = 10
    if difficulty == "Medium": pts = 15
    elif difficulty == "Hard": pts = 20
    elif difficulty == "Challenge": pts = 30

    gained_points = pts if is_correct else 2

    # Update User Points & Streak
    cursor.execute("UPDATE users SET points = points + ? WHERE id = ?", (gained_points, user_id))
    update_user_streak(cursor, user_id)

    # Update Progress
    cursor.execute("SELECT * FROM progress WHERE user_id = ? AND operation = ?", (user_id, operation))
    prog = cursor.fetchone()
    if prog:
        new_att = prog['total_attempted'] + 1
        new_corr = prog['correct_count'] + (1 if is_correct else 0)
        new_time = prog['total_time_seconds'] + time_taken

        # Mastery calculation (1 to 5)
        acc = new_corr / new_att if new_att > 0 else 0
        mastery = 1
        if new_att >= 5 and acc >= 0.5: mastery = 2
        if new_att >= 10 and acc >= 0.7: mastery = 3
        if new_att >= 20 and acc >= 0.85: mastery = 4
        if new_att >= 35 and acc >= 0.92: mastery = 5

        cursor.execute('''
            UPDATE progress 
            SET total_attempted = ?, correct_count = ?, total_time_seconds = ?, mastery_level = ?, last_updated = CURRENT_TIMESTAMP
            WHERE user_id = ? AND operation = ?
        ''', (new_att, new_corr, new_time, mastery, user_id, operation))

    explanation = None
    if not is_correct:
        explanation = ai_engine.explain_mistake(operand1, operand2, operation, user_ans, correct_ans, user_key=user_key)
        # Log to AI History
        cursor.execute('''
            INSERT INTO ai_history (user_id, question_text, user_answer, correct_answer, explanation_type, response_text)
            VALUES (?, ?, ?, ?, 'mistake_explanation', ?)
        ''', (user_id, f"{operand1} {operation} {operand2}", user_ans, correct_ans, explanation))

    conn.commit()
    new_badges = check_and_award_badges(conn, user_id)
    conn.close()

    return jsonify({
        "success": True,
        "is_correct": is_correct,
        "gained_points": gained_points,
        "correct_answer": correct_ans,
        "explanation": explanation,
        "unlocked_badges": new_badges
    })

@app.route("/api/practice/hint", methods=["POST"])
def get_hint():
    data = request.json or {}
    op1 = int(data.get("operand1", 0))
    op2 = int(data.get("operand2", 0))
    op = data.get("operation", "Addition")
    user_ans = data.get("user_answer")
    hint_lvl = int(data.get("hint_level", 1))
    user_key = data.get("gemini_api_key")

    hint_text = ai_engine.generate_socratic_hint(op1, op2, op, user_answer=user_ans, hint_level=hint_lvl, user_key=user_key)
    return jsonify({"success": True, "hint": hint_text})

# 3. AI Tutor Endpoints
@app.route("/api/ai/explain", methods=["POST"])
def ai_explain():
    data = request.json or {}
    op1 = int(data.get("operand1", 0))
    op2 = int(data.get("operand2", 0))
    op = data.get("operation", "Addition")
    user_ans = int(data.get("user_answer", 0))
    correct_ans = int(data.get("correct_answer", 0))
    user_key = data.get("gemini_api_key")

    explanation = ai_engine.explain_mistake(op1, op2, op, user_ans, correct_ans, user_key=user_key)
    return jsonify({"success": True, "explanation": explanation})

@app.route("/api/ai/chat", methods=["POST"])
def ai_chat():
    data = request.json or {}
    user_id = data.get("user_id")
    message = data.get("message", "").strip()
    user_key = data.get("gemini_api_key")

    if not message:
        return jsonify({"success": False, "error": "Message cannot be empty"}), 400

    reply = ai_engine.ask_tutor_chat(message, user_key=user_key)

    if user_id:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO ai_history (user_id, question_text, user_answer, correct_answer, explanation_type, response_text)
            VALUES (?, ?, NULL, 0, 'chat', ?)
        ''', (user_id, message, reply))
        
        # Award AI scholar badge check
        cursor.execute("SELECT COUNT(*) FROM ai_history WHERE user_id = ?", (user_id,))
        count = cursor.fetchone()[0]
        if count >= 5:
            check_and_award_badges(conn, user_id)
        
        conn.commit()
        conn.close()

    return jsonify({"success": True, "reply": reply})

@app.route("/api/ai/history/<int:user_id>", methods=["GET"])
def ai_history(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ai_history WHERE user_id = ? ORDER BY created_at DESC LIMIT 10", (user_id,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify({"success": True, "history": rows})

# 4. Quiz Endpoints
@app.route("/api/quiz/submit", methods=["POST"])
def quiz_submit():
    data = request.json or {}
    user_id = data.get("user_id")
    op = data.get("operation", "Mixed")
    difficulty = data.get("difficulty", "Medium")
    score = int(data.get("score", 0))
    total = int(data.get("total_questions", 10))
    time_taken = int(data.get("time_taken_seconds", 60))

    accuracy = (score / total) * 100 if total > 0 else 0

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO quiz_results (user_id, quiz_type, operation, difficulty, score, total_questions, accuracy, time_taken_seconds)
        VALUES (?, 'Quiz', ?, ?, ?, ?, ?, ?)
    ''', (user_id, op, difficulty, score, total, accuracy, time_taken))

    # Reward points for quiz completion (10 pts per correct answer + 20 bonus for perfect score)
    gained = (score * 10) + (30 if score == total else 0)
    cursor.execute("UPDATE users SET points = points + ? WHERE id = ?", (gained, user_id))

    # If 100% score, award Quiz Champion badge
    if score == total:
        cursor.execute("SELECT id FROM badges WHERE code = 'quiz_champion'")
        b_row = cursor.fetchone()
        if b_row:
            cursor.execute("INSERT OR IGNORE INTO user_badges (user_id, badge_id) VALUES (?, ?)", (user_id, b_row[0]))

    conn.commit()
    new_badges = check_and_award_badges(conn, user_id)
    conn.close()

    return jsonify({
        "success": True,
        "score": score,
        "total": total,
        "accuracy": accuracy,
        "gained_points": gained,
        "unlocked_badges": new_badges
    })

# 5. Dashboard, Progress, Leaderboard & Badges
@app.route("/api/dashboard/<int:user_id>", methods=["GET"])
def dashboard(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # User Profile
    cursor.execute("SELECT id, username, email, grade_level, avatar, points, streak, gemini_api_key FROM users WHERE id = ?", (user_id,))
    user_row = cursor.fetchone()
    if not user_row:
        conn.close()
        return jsonify({"success": False, "error": "User not found"}), 404

    user = dict(user_row)

    # Progress per operation
    cursor.execute("SELECT * FROM progress WHERE user_id = ?", (user_id,))
    progress_rows = [dict(r) for r in cursor.fetchall()]

    # Unlocked badges count
    cursor.execute("SELECT COUNT(*) FROM user_badges WHERE user_id = ?", (user_id,))
    unlocked_badges_count = cursor.fetchone()[0]

    # Total questions solved
    total_solved = sum(p['correct_count'] for p in progress_rows)

    conn.close()
    return jsonify({
        "success": True,
        "user": user,
        "progress": progress_rows,
        "unlocked_badges_count": unlocked_badges_count,
        "total_solved": total_solved
    })

@app.route("/api/progress/<int:user_id>", methods=["GET"])
def get_progress(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM progress WHERE user_id = ?", (user_id,))
    progress_rows = [dict(r) for r in cursor.fetchall()]
    
    cursor.execute("SELECT * FROM quiz_results WHERE user_id = ? ORDER BY created_at DESC LIMIT 10", (user_id,))
    quizzes = [dict(r) for r in cursor.fetchall()]

    conn.close()
    return jsonify({
        "success": True,
        "progress": progress_rows,
        "recent_quizzes": quizzes
    })

@app.route("/api/leaderboard", methods=["GET"])
def leaderboard():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, avatar, grade_level, points, streak FROM users ORDER BY points DESC, streak DESC LIMIT 10")
    leaderboard_rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify({"success": True, "leaderboard": leaderboard_rows})

@app.route("/api/badges/<int:user_id>", methods=["GET"])
def get_badges(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM badges")
    all_badges = [dict(b) for b in cursor.fetchall()]

    cursor.execute("SELECT badge_id, unlocked_at FROM user_badges WHERE user_id = ?", (user_id,))
    unlocked_map = {r['badge_id']: r['unlocked_at'] for r in cursor.fetchall()}

    for badge in all_badges:
        b_id = badge['id']
        badge['is_unlocked'] = b_id in unlocked_map
        badge['unlocked_at'] = unlocked_map.get(b_id)

    conn.close()
    return jsonify({"success": True, "badges": all_badges})

@app.route("/api/daily_challenge/<int:user_id>", methods=["GET"])
def daily_challenge(user_id):
    today_str = date.today().isoformat()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM daily_challenges WHERE challenge_date = ?", (today_str,))
    row = cursor.fetchone()

    if not row:
        # Generate 3 challenge questions for today
        q1 = generate_math_problem("Addition", "Medium")
        q2 = generate_math_problem("Multiplication", "Medium")
        q3 = generate_math_problem("Division", "Hard")
        challenge_q = [q1, q2, q3]
        
        cursor.execute('''
            INSERT INTO daily_challenges (challenge_date, title, description, questions_json, reward_points)
            VALUES (?, 'Daily Math Marathon', 'Solve 3 medium-to-hard arithmetic puzzles for +50 Bonus XP!', ?, 50)
        ''', (today_str, json.dumps(challenge_q)))
        conn.commit()
        
        challenge_data = {
            "title": "Daily Math Marathon",
            "description": "Solve 3 medium-to-hard arithmetic puzzles for +50 Bonus XP!",
            "questions": challenge_q,
            "reward_points": 50,
            "challenge_date": today_str
        }
    else:
        challenge_data = {
            "title": row['title'],
            "description": row['description'],
            "questions": json.loads(row['questions_json']),
            "reward_points": row['reward_points'],
            "challenge_date": row['challenge_date']
        }

    conn.close()
    return jsonify({"success": True, "daily_challenge": challenge_data})

# 6. PDF Report Download
@app.route("/api/report/pdf/<int:user_id>", methods=["GET"])
def download_pdf_report(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, username, email, grade_level, points, streak FROM users WHERE id = ?", (user_id,))
    user_row = cursor.fetchone()
    if not user_row:
        conn.close()
        return jsonify({"error": "User not found"}), 404

    user_data = dict(user_row)

    cursor.execute("SELECT * FROM progress WHERE user_id = ?", (user_id,))
    progress_data = [dict(r) for r in cursor.fetchall()]

    cursor.execute('''
        SELECT b.title, b.icon FROM badges b
        JOIN user_badges ub ON b.id = ub.badge_id
        WHERE ub.user_id = ?
    ''', (user_id,))
    badges_data = [dict(r) for r in cursor.fetchall()]

    conn.close()

    pdf_bytes = pdf_generator.generate_pdf_report(user_data, progress_data, badges_data)
    
    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-Disposition": f"attachment;filename=AI_Tutor_Report_{user_data['username']}.pdf"}
    )

if __name__ == "__main__":
    print("Starting AI Arithmetic Tutor Flask Application on http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
