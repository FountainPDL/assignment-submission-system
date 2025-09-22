from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import os
from datetime import datetime
import hashlib
from plagiarism_detector import PlagiarismDetector
from database_manager import DatabaseManager
from file_processor import FileProcessor
import json

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize components
db_manager = DatabaseManager()
plagiarism_detector = PlagiarismDetector()
file_processor = FileProcessor()

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login')
def index():
    if 'user_id' in session:
        if session['user_type'] == 'student':
            return redirect(url_for('student_dashboard'))
        else:
            return redirect(url_for('lecturer_dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_type = request.form['user_type']
        
        user = db_manager.authenticate_user(username, password, user_type)
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['user_type'] = user['user_type']
            session['full_name'] = user['full_name']
            
            if user_type == 'student':
                return redirect(url_for('student_dashboard'))
            else:
                return redirect(url_for('lecturer_dashboard'))
        else:
            flash('Invalid credentials')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        full_name = request.form['full_name']
        email = request.form['email']
        user_type = request.form['user_type']
        student_id = request.form.get('student_id', '')
        
        if db_manager.create_user(username, password, full_name, email, user_type, student_id):
            flash('Registration successful! Please login.')
            return redirect(url_for('login'))
        else:
            flash('Registration failed. Username may already exist.')
    
    return render_template('register.html')

@app.route('/student_dashboard')
def student_dashboard():
    if 'user_id' not in session or session['user_type'] != 'student':
        return redirect(url_for('login'))
    
    assignments = db_manager.get_available_assignments()
    submissions = db_manager.get_student_submissions(session['user_id'])
    
    return render_template('student_dashboard.html',
                         assignments=assignments,
                         submissions=submissions,
                         user=session)

@app.route('/lecturer_dashboard')
def lecturer_dashboard():
    if 'user_id' not in session or session['user_type'] != 'lecturer':
        return redirect(url_for('login'))
    
    assignments = db_manager.get_lecturer_assignments(session['user_id'])
    recent_submissions = db_manager.get_recent_submissions()
    
    return render_template('lecturer_dashboard.html',
                         assignments=assignments,
                         recent_submissions=recent_submissions,
                         user=session)

@app.route('/create_assignment', methods=['GET', 'POST'])
def create_assignment():
    if 'user_id' not in session or session['user_type'] != 'lecturer':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        due_date = request.form['due_date']
        max_score = request.form['max_score']
        
        assignment_id = db_manager.create_assignment(
            title, description, due_date, max_score, session['user_id']
        )
        
        if assignment_id:
            flash('Assignment created successfully!')
            return redirect(url_for('lecturer_dashboard'))
        else:
            flash('Failed to create assignment.')
    
    return render_template('create_assignment.html', user=session)

@app.route('/submit_assignment/<int:assignment_id>', methods=['GET', 'POST'])
def submit_assignment(assignment_id):
    if 'user_id' not in session or session['user_type'] != 'student':
        return redirect(url_for('login'))
    
    assignment = db_manager.get_assignment(assignment_id)
    if not assignment:
        flash('Assignment not found.')
        return redirect(url_for('student_dashboard'))
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected.')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected.')
            return redirect(request.url)
        
        if file and file_processor.allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{session['user_id']}_{assignment_id}_{timestamp}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Process file and detect plagiarism
            file_content = file_processor.extract_text(filepath)
            plagiarism_score = plagiarism_detector.detect_plagiarism(file_content)
            
            # Save submission to database
            submission_id = db_manager.create_submission(
                assignment_id, session['user_id'], filename, filepath, 
                plagiarism_score, file_content
            )
            
            if submission_id:
                flash(f'Assignment submitted successfully! Plagiarism score: {plagiarism_score:.2f}%')
                return redirect(url_for('student_dashboard'))
            else:
                flash('Failed to submit assignment.')
        else:
            flash('Invalid file type.')
    
    return render_template('submit_assignment.html', assignment=assignment, user=session)

@app.route('/view_submissions/<int:assignment_id>')
def view_submissions(assignment_id):
    if 'user_id' not in session or session['user_type'] != 'lecturer':
        return redirect(url_for('login'))
    
    assignment = db_manager.get_assignment(assignment_id)
    submissions = db_manager.get_assignment_submissions(assignment_id)
    
    return render_template('view_submissions.html',
                         assignment=assignment,
                         submissions=submissions,
                         user=session)

@app.route('/grade_submission/<int:submission_id>', methods=['POST'])
def grade_submission(submission_id):
    if 'user_id' not in session or session['user_type'] != 'lecturer':
        return redirect(url_for('login'))
    
    score = request.form['score']
    feedback = request.form['feedback']
    
    if db_manager.grade_submission(submission_id, score, feedback):
        flash('Submission graded successfully!')
    else:
        flash('Failed to grade submission.')
    
    return redirect(request.referrer)

@app.route('/download_submission/<int:submission_id>')
def download_submission(submission_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    submission = db_manager.get_submission(submission_id)
    if submission and os.path.exists(submission['file_path']):
        return send_file(submission['file_path'], as_attachment=True)
    else:
        flash('File not found.')
        return redirect(request.referrer)

@app.route('/plagiarism_report/<int:submission_id>')
def plagiarism_report(submission_id):
    if 'user_id' not in session or session['user_type'] != 'lecturer':
        return redirect(url_for('login'))
    
    submission = db_manager.get_submission(submission_id)
    if submission:
        detailed_report = plagiarism_detector.get_detailed_report(submission['content'])
        return render_template('plagiarism_report.html',
                             submission=submission,
                             report=detailed_report,
                             user=session)
    else:
        flash('Submission not found.')
        return redirect(url_for('lecturer_dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/api/plagiarism_stats')
def plagiarism_stats():
    if 'user_id' not in session or session['user_type'] != 'lecturer':
        return jsonify({'error': 'Unauthorized'}), 401
    
    stats = db_manager.get_plagiarism_statistics()
    return jsonify(stats)

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

@app.errorhandler(413)
def too_large(error):
    flash('File too large. Maximum size is 16MB.')
    return redirect(request.url)

if __name__ == '__main__':
    db_manager.init_database()
    app.run(debug=True, host='0.0.0.0', port=5000)
