import os
import json
import requests
import random

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

def get_gemini_api_key(user_key=None):
    if user_key and user_key.strip():
        return user_key.strip()
    return os.environ.get("GEMINI_API_KEY", "").strip()

def call_gemini_api(prompt, system_instruction=None, api_key=None):
    key = get_gemini_api_key(api_key)
    if not key:
        return None  # Will trigger fallback solver

    url = f"{GEMINI_API_URL}?key={key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    if system_instruction:
        payload["system_instruction"] = {"parts": [{"text": system_instruction}]}

    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            try:
                text = data['candidates'][0]['content']['parts'][0]['text']
                return text.strip()
            except (KeyError, IndexError):
                return None
    except Exception as e:
        print(f"Gemini API Call error: {e}")
        return None

def explain_mistake(operand1, operand2, operation, user_answer, correct_answer, user_key=None):
    op_symbol_map = {"Addition": "+", "Subtraction": "-", "Multiplication": "×", "Division": "÷"}
    symbol = op_symbol_map.get(operation, "+")
    question_str = f"{operand1} {symbol} {operand2}"

    system_prompt = (
        "You are 'Professor Owl', a friendly, encouraging AI Math Tutor for elementary/middle school students. "
        "Explain math mistakes clearly, step-by-step, using emojis, bullet points, and positive encouragement. "
        "Keep steps short, simple, and easy to read on a mobile screen."
    )

    user_prompt = (
        f"The student attempted the math problem: {question_str}.\n"
        f"They answered: {user_answer}\n"
        f"The correct answer is: {correct_answer}\n\n"
        f"Please provide:\n"
        f"1. A friendly note acknowledging their attempt.\n"
        f"2. A clear 3-step breakdown showing how to calculate {question_str} correctly.\n"
        f"3. Highlight what likely went wrong with their answer ({user_answer}) in a helpful way.\n"
        f"4. A quick encouragement or high-five for trying again."
    )

    ai_response = call_gemini_api(user_prompt, system_instruction=system_prompt, api_key=user_key)
    if ai_response:
        return ai_response

    # --- DETERMINISTIC FALLBACK AI SOLVER ---
    return generate_fallback_mistake_explanation(operand1, operand2, operation, user_answer, correct_answer)

def generate_fallback_mistake_explanation(a, b, op, user_ans, correct_ans):
    op_lower = op.lower()
    
    if "add" in op_lower:
        return (
            f"### 🦉 Professor Owl's Step-by-Step Breakdown\n\n"
            f"Great effort trying **{a} + {b}**! Mistakes are just steps on the path to mastery. Let's solve it together! 🌟\n\n"
            f"#### 🔍 Step-by-Step Solution:\n"
            f"1. **Start with the First Number**: Imagine you have **{a}** blocks.\n"
            f"2. **Add the Second Number**: Count forward **{b}** more: "
            f"`{' + '.join([str(a)] + ['1']*min(b, 5))}`...\n"
            f"3. **Combine Total**: Combining {a} and {b} gives exactly **{correct_ans}**!\n\n"
            f"💡 *Tip*: You typed **{user_ans}**. "
            f"{'You were very close! Check your ones column again.' if abs(user_ans - correct_ans) <= 3 else 'Double check your mental addition step by step!'}\n\n"
            f"💪 **You've got this! Try the next problem!**"
        )
    elif "sub" in op_lower:
        return (
            f"### 🦉 Professor Owl's Step-by-Step Breakdown\n\n"
            f"Nice attempt on **{a} - {b}**! Subtraction is all about finding the difference between two quantities. 🔍\n\n"
            f"#### 🔍 Step-by-Step Solution:\n"
            f"1. **Start at {a}**: Think of a number line starting at **{a}**.\n"
            f"2. **Take Away {b}**: Jump backward by **{b}** units.\n"
            f"3. **Land on the Answer**: {a} minus {b} leaves **{correct_ans}**!\n\n"
            f"💡 *Analysis*: You answered **{user_ans}**. "
            f"{'Remember: order matters in subtraction! Make sure you subtract the smaller number from the larger number.' if user_ans > a else 'Check if you needed to borrow from the next column!'}\n\n"
            f"🌟 **Keep practicing, you are getting smarter every minute!**"
        )
    elif "mul" in op_lower:
        return (
            f"### 🦉 Professor Owl's Step-by-Step Breakdown\n\n"
            f"Multiplication **{a} × {b}** is just fast repeated addition! Let's break it down! 🚀\n\n"
            f"#### 🔍 Step-by-Step Solution:\n"
            f"1. **Think of Groups**: {a} × {b} means **{a} groups of {b}** (or {b} groups of {a}).\n"
            f"2. **Repeated Addition**: Adding {b} a total of {a} times: "
            f"`{' + '.join([str(b)]*min(a, 4))}`{'...' if a > 4 else ''}\n"
            f"3. **Final Result**: The product of {a} and {b} is **{correct_ans}**!\n\n"
            f"💡 *Notice*: You gave **{user_ans}**. "
            f"{'Check if you accidentally added instead of multiplied!' if user_ans == a + b else 'Recite your times tables aloud to lock it into memory!'}\n\n"
            f"🎉 **Great try! Multiplication power unlocked!**"
        )
    else:  # Division
        return (
            f"### 🦉 Professor Owl's Step-by-Step Breakdown\n\n"
            f"Division **{a} ÷ {b}** is sharing equally into equal piles! 🍕\n\n"
            f"#### 🔍 Step-by-Step Solution:\n"
            f"1. **Total Amount**: Start with **{a}** total items.\n"
            f"2. **Group Size**: Divide them into equal groups of **{b}**.\n"
            f"3. **Count the Groups**: How many groups of {b} fit into {a}? Exactly **{correct_ans}** groups! ({correct_ans} × {b} = {a})\n\n"
            f"💡 *Analysis*: Your answer **{user_ans}** was close! "
            f"Ask yourself: *'What number times {b} equals {a}?'* The answer is **{correct_ans}**!\n\n"
            f"⭐ **Awesome effort! Division mastery takes practice!**"
        )

def generate_socratic_hint(operand1, operand2, operation, user_answer=None, hint_level=1, user_key=None):
    op_symbol_map = {"Addition": "+", "Subtraction": "-", "Multiplication": "×", "Division": "÷"}
    symbol = op_symbol_map.get(operation, "+")
    question_str = f"{operand1} {symbol} {operand2}"

    system_prompt = (
        "You are an encouraging AI Socratic Math Tutor. Provide a helpful hint for a student trying to solve a problem. "
        "DO NOT reveal the exact numerical answer! Give a strategic clue, mental trick, or visual prompt."
    )

    user_prompt = f"Problem: {question_str}. Hint Level {hint_level} of 3. Give a helpful clue without revealing the final answer."

    ai_response = call_gemini_api(user_prompt, system_instruction=system_prompt, api_key=user_key)
    if ai_response:
        return ai_response

    # Fallback hint generator
    if hint_level == 1:
        if operation == "Addition":
            return f"💡 **Hint 1**: Break the numbers into tens and ones! What is {operand1} rounded to the nearest 10?"
        elif operation == "Subtraction":
            return f"💡 **Hint 1**: Count UP from {operand2} to {operand1}! How many steps to reach the next ten?"
        elif operation == "Multiplication":
            return f"💡 **Hint 1**: Think of this as adding {operand2} repeatedly, {operand1} times!"
        else:
            return f"💡 **Hint 1**: Ask yourself: What number multiplied by {operand2} gives {operand1}?"
    elif hint_level == 2:
        if operation == "Addition":
            half_b = operand2 // 2
            return f"💡 **Hint 2**: Try adding {half_b} first to {operand1}, then add the remaining {operand2 - half_b}!"
        elif operation == "Subtraction":
            return f"💡 **Hint 2**: The answer is between {max(1, operand1 - operand2 - 5)} and {operand1 - operand2 + 5}!"
        elif operation == "Multiplication":
            return f"💡 **Hint 2**: Did you know {operand1} × 5 is {(operand1 * 5)}? Use that to estimate!"
        else:
            return f"💡 **Hint 2**: Try skip counting by {operand2} until you reach {operand1}!"
    else:
        ans = eval_math(operand1, operand2, operation)
        return f"💡 **Final Clue**: The answer is a number ending in **{ans % 10}**!"

def eval_math(a, b, op):
    if op == "Addition": return a + b
    if op == "Subtraction": return a - b
    if op == "Multiplication": return a * b
    if op == "Division": return a // b if b != 0 else 0
    return a + b

def ask_tutor_chat(user_message, conversation_history=[], user_key=None):
    system_prompt = (
        "You are Professor Owl, an expert AI Math Tutor for young students. "
        "Answer questions about arithmetic, numbers, shapes, and study strategies in an engaging, joyful, educational manner. "
        "Use markdown formatting, emojis, and clear short paragraphs."
    )

    ai_response = call_gemini_api(user_message, system_instruction=system_prompt, api_key=user_key)
    if ai_response:
        return ai_response

    # Fallback responses for common math questions
    msg_lower = user_message.lower()
    if "zero" in msg_lower or "divide" in msg_lower and "0" in msg_lower:
        return (
            "🦉 **Why can't we divide by zero?**\n\n"
            "Imagine you have 10 cookies 🍪 and you want to share them among **0 friends**.\n"
            "How many cookies does each friend get? It doesn't make sense because there are no friends to give them to!\n\n"
            "In mathematics, division by zero is **undefined**! 🚫"
        )
    elif "multiply" in msg_lower or "times" in msg_lower:
        return (
            "🦉 **Multiplication Secret Trick!**\n\n"
            "To multiply any number by 10, just add a **0** to the end! e.g., 7 × 10 = 70.\n"
            "To multiply by 9, multiply by 10 and subtract the original number once! e.g., 9 × 6 = (60 - 6) = 54. 🪄"
        )
    else:
        return (
            f"🦉 **Professor Owl says:**\n\n"
            f"Math is like a puzzle adventure! When solving arithmetic problems, always start from the ones place, "
            f"keep your numbers aligned, and double-check your work!\n\n"
            f"Ask me anything specific like *'How do I subtract with regrouping?'* or *'What is a prime number?'*!"
        )
