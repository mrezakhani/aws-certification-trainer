#!/usr/bin/env python3
"""
AWS CLF-C02 Quiz Trainer - Web Interface
Flask-based web application for practicing AWS certification questions
"""

from flask import Flask, render_template, request, jsonify, session
import sqlite3
import os
import random


def shuffle_options(options):
    """Shuffle options and reassign letters A, B, C, D, etc."""
    # Shuffle the options
    shuffled = options.copy()
    random.shuffle(shuffled)

    # Reassign letters and track correct answers
    letters = 'ABCDEFGHIJ'
    new_options = []
    correct = []

    for i, opt in enumerate(shuffled):
        new_letter = letters[i]
        new_options.append({
            'letter': new_letter,
            'text': opt['text'],
            'is_correct': opt['is_correct']
        })
        if opt['is_correct']:
            correct.append(new_letter)

    return new_options, correct

app = Flask(__name__)
app.secret_key = 'aws-quiz-trainer-secret-key-2024'

DATABASE_PATH = os.path.join(os.path.dirname(__file__), "aws_quiz.db")


def get_db_connection():
    """Create database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_mastery_table():
    """Create mastery tracking table if it doesn't exist"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create mastery table to track correct answer counts
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS question_mastery (
            question_id INTEGER PRIMARY KEY,
            correct_count INTEGER DEFAULT 0,
            incorrect_count INTEGER DEFAULT 0,
            last_answered TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (question_id) REFERENCES questions(id)
        )
    ''')

    conn.commit()
    conn.close()


# Initialize mastery table on startup
init_mastery_table()


def get_questions(domain=None, limit=None):
    """Fetch questions from database"""
    conn = get_db_connection()
    cursor = conn.cursor()

    if domain and domain != 'all':
        cursor.execute('''
            SELECT id, question_text, domain, explanation
            FROM questions
            WHERE domain = ?
            ORDER BY RANDOM()
        ''', (domain,))
    else:
        cursor.execute('''
            SELECT id, question_text, domain, explanation
            FROM questions
            ORDER BY RANDOM()
        ''')

    rows = cursor.fetchall()

    if limit:
        rows = rows[:limit]

    questions = []
    for row in rows:
        # Get options for this question
        cursor.execute('''
            SELECT option_letter, option_text, is_correct
            FROM options
            WHERE question_id = ?
            ORDER BY option_letter
        ''', (row['id'],))

        options = []
        for opt in cursor.fetchall():
            options.append({
                'letter': opt['option_letter'],
                'text': opt['option_text'],
                'is_correct': opt['is_correct']
            })

        # Get correct answer letters (no shuffling - keep original order)
        correct = [opt['letter'] for opt in options if opt['is_correct']]

        questions.append({
            'id': row['id'],
            'question': row['question_text'],
            'domain': row['domain'],
            'explanation': row['explanation'] or '',
            'options': options,
            'correct': correct
        })

    conn.close()
    return questions


def get_stats():
    """Get database statistics"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as total FROM questions")
    total = cursor.fetchone()['total']

    cursor.execute('''
        SELECT domain, COUNT(*) as count
        FROM questions
        GROUP BY domain
        ORDER BY count DESC
    ''')
    domains = [{'name': row['domain'], 'count': row['count']} for row in cursor.fetchall()]

    # Get questions that need practice (answered but not mastered - less than 4 correct)
    cursor.execute('''
        SELECT COUNT(*) as count FROM question_mastery
        WHERE correct_count < 4 AND (correct_count > 0 OR incorrect_count > 0)
    ''')
    needs_practice = cursor.fetchone()['count']

    # Get mastered questions count (4+ correct answers)
    cursor.execute("SELECT COUNT(*) as count FROM question_mastery WHERE correct_count >= 4")
    mastered_count = cursor.fetchone()['count']

    # Get questions answered incorrectly at least once
    cursor.execute("SELECT COUNT(*) as count FROM question_mastery WHERE incorrect_count > 0 AND correct_count < 4")
    wrong_count = cursor.fetchone()['count']

    conn.close()
    return {
        'total': total,
        'domains': domains,
        'needs_practice': needs_practice,
        'mastered_count': mastered_count,
        'wrong_count': wrong_count
    }


def save_progress(question_id, is_correct):
    """Save user progress to database with mastery tracking"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Also save to user_progress for history
    cursor.execute('''
        INSERT INTO user_progress (question_id, answered_correctly)
        VALUES (?, ?)
    ''', (question_id, is_correct))

    # Update mastery table
    cursor.execute('''
        INSERT INTO question_mastery (question_id, correct_count, incorrect_count, last_answered)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(question_id) DO UPDATE SET
            correct_count = correct_count + ?,
            incorrect_count = incorrect_count + ?,
            last_answered = CURRENT_TIMESTAMP
    ''', (question_id,
          1 if is_correct else 0,
          0 if is_correct else 1,
          1 if is_correct else 0,
          0 if is_correct else 1))

    conn.commit()
    conn.close()


def get_mastery_info(question_id):
    """Get mastery info for a specific question"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT correct_count, incorrect_count
        FROM question_mastery
        WHERE question_id = ?
    ''', (question_id,))

    row = cursor.fetchone()
    conn.close()

    if row:
        return {'correct': row['correct_count'], 'incorrect': row['incorrect_count']}
    return {'correct': 0, 'incorrect': 0}


def get_missed_questions():
    """Get questions that need more practice (less than 4 correct answers)"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get questions with less than 4 correct answers (not mastered yet)
    cursor.execute('''
        SELECT q.id, q.question_text, q.domain, q.explanation,
               COALESCE(m.correct_count, 0) as correct_count,
               COALESCE(m.incorrect_count, 0) as incorrect_count
        FROM questions q
        INNER JOIN question_mastery m ON q.id = m.question_id
        WHERE m.correct_count < 4
        ORDER BY m.incorrect_count DESC, m.correct_count ASC, RANDOM()
    ''')

    rows = cursor.fetchall()

    questions = []
    for row in rows:
        # Get options for this question
        cursor.execute('''
            SELECT option_letter, option_text, is_correct
            FROM options
            WHERE question_id = ?
            ORDER BY option_letter
        ''', (row['id'],))

        options = []
        for opt in cursor.fetchall():
            options.append({
                'letter': opt['option_letter'],
                'text': opt['option_text'],
                'is_correct': opt['is_correct']
            })

        # Get correct answer letters (no shuffling - keep original order)
        correct = [opt['letter'] for opt in options if opt['is_correct']]

        questions.append({
            'id': row['id'],
            'question': row['question_text'],
            'domain': row['domain'],
            'explanation': row['explanation'] or '',
            'options': options,
            'correct': correct,
            'mastery': {
                'correct': row['correct_count'],
                'incorrect': row['incorrect_count']
            }
        })

    conn.close()
    return questions


def clear_progress():
    """Clear all user progress"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_progress")
    cursor.execute("DELETE FROM question_mastery")
    conn.commit()
    conn.close()


@app.route('/')
def index():
    """Home page with quiz options"""
    stats = get_stats()
    return render_template('index.html', stats=stats)


@app.route('/quiz')
def quiz():
    """Start a quiz session"""
    domain = request.args.get('domain', 'all')
    limit = request.args.get('limit', type=int)

    questions = get_questions(domain, limit)

    if not questions:
        return render_template('error.html', message="No questions available")

    # Store questions in session
    session['questions'] = questions
    session['current_index'] = 0
    session['score'] = 0
    session['answers'] = []
    session['domain'] = domain

    return render_template('quiz.html',
                         question=questions[0],
                         current=1,
                         total=len(questions),
                         domain=domain)


@app.route('/answer', methods=['POST'])
def answer():
    """Process an answer"""
    data = request.get_json()
    selected = data.get('selected', [])

    questions = session.get('questions', [])
    current_index = session.get('current_index', 0)

    if current_index >= len(questions):
        return jsonify({'error': 'Quiz completed'})

    question = questions[current_index]
    correct = set(question['correct'])
    selected_set = set(selected)

    is_correct = correct == selected_set

    if is_correct:
        session['score'] = session.get('score', 0) + 1

    # Record answer
    answers = session.get('answers', [])
    answers.append({
        'question_id': question['id'],
        'selected': selected,
        'correct': list(correct),
        'is_correct': is_correct
    })
    session['answers'] = answers

    # Save progress to database
    save_progress(question['id'], is_correct)

    # Get updated mastery info
    mastery = get_mastery_info(question['id'])

    return jsonify({
        'is_correct': is_correct,
        'correct_answers': list(correct),
        'explanation': question['explanation'],
        'mastery': mastery
    })


@app.route('/next')
def next_question():
    """Get next question"""
    questions = session.get('questions', [])
    current_index = session.get('current_index', 0) + 1
    session['current_index'] = current_index

    if current_index >= len(questions):
        return jsonify({'completed': True})

    question = questions[current_index]

    return jsonify({
        'completed': False,
        'question': question,
        'current': current_index + 1,
        'total': len(questions)
    })


@app.route('/results')
def results():
    """Show quiz results"""
    questions = session.get('questions', [])
    answers = session.get('answers', [])
    score = session.get('score', 0)
    domain = session.get('domain', 'all')

    total = len(questions)
    percentage = (score / total * 100) if total > 0 else 0
    passed = percentage >= 70

    # Calculate domain breakdown
    domain_scores = {}
    for i, answer in enumerate(answers):
        q_domain = questions[i]['domain']
        if q_domain not in domain_scores:
            domain_scores[q_domain] = {'correct': 0, 'total': 0}
        domain_scores[q_domain]['total'] += 1
        if answer['is_correct']:
            domain_scores[q_domain]['correct'] += 1

    return render_template('results.html',
                         score=score,
                         total=total,
                         percentage=percentage,
                         passed=passed,
                         domain_scores=domain_scores,
                         answers=answers,
                         questions=questions)


@app.route('/review')
def review():
    """Review all answers"""
    questions = session.get('questions', [])
    answers = session.get('answers', [])

    review_data = []
    for i, (question, answer) in enumerate(zip(questions, answers)):
        review_data.append({
            'number': i + 1,
            'question': question,
            'answer': answer
        })

    return render_template('review.html', review_data=review_data)


@app.route('/quiz/missed')
def quiz_missed():
    """Start a quiz with missed questions only"""
    questions = get_missed_questions()

    if not questions:
        return render_template('error.html', message="No missed questions to practice! Great job!")

    # Store questions in session
    session['questions'] = questions
    session['current_index'] = 0
    session['score'] = 0
    session['answers'] = []
    session['domain'] = 'Missed Questions'

    return render_template('quiz.html',
                         question=questions[0],
                         current=1,
                         total=len(questions),
                         domain='Missed Questions')


@app.route('/clear-progress')
def clear_progress_route():
    """Clear all user progress"""
    clear_progress()
    return render_template('error.html', message="Progress cleared! All missed questions have been reset.")


@app.route('/api/stats')
def api_stats():
    """API endpoint for statistics"""
    return jsonify(get_stats())


if __name__ == '__main__':
    # Check if database exists
    if not os.path.exists(DATABASE_PATH):
        print("Error: Database not found!")
        print("Please run import_github_questions.py first.")
        exit(1)

    print("=" * 50)
    print("AWS CLF-C02 Quiz Trainer - Web Interface")
    print("=" * 50)
    print("\nStarting web server...")
    print("Open your browser and go to: http://localhost:5000")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 50)

    app.run(debug=True, host='0.0.0.0', port=5000)
