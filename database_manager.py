import sqlite3
import hashlib
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class DatabaseManager:
    def __init__(self, db_path='assignment_system.db'):
        self.db_path = db_path
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL,
                user_type TEXT NOT NULL CHECK (user_type IN ('student', 'lecturer')),
                student_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Assignments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                due_date DATE NOT NULL,
                max_score INTEGER DEFAULT 100,
                lecturer_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lecturer_id) REFERENCES users (id)
            )
        ''')
        
        # Submissions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                assignment_id INTEGER NOT NULL,
                student_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                content TEXT,
                plagiarism_score REAL DEFAULT 0.0,
                score INTEGER,
                feedback TEXT,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                graded_at TIMESTAMP,
                FOREIGN KEY (assignment_id) REFERENCES assignments (id),
                FOREIGN KEY (student_id) REFERENCES users (id)
            )
        ''')
        
        # Plagiarism reports table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS plagiarism_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                submission_id INTEGER NOT NULL,
                similarity_score REAL NOT NULL,
                matched_content TEXT,
                report_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (submission_id) REFERENCES submissions (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # Create default admin user
        self.create_default_users()
    
    def create_default_users(self):
        # Create default lecturer
        self.create_user('admin', 'admin123', 'System Administrator', 
                        'admin@university.edu', 'lecturer', '')
        
        # Create default student
        self.create_user('student1', 'student123', 'John Doe', 
                        'john.doe@student.edu', 'student', 'STU001')
    
    def create_user(self, username, password, full_name, email, user_type, student_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            password_hash = generate_password_hash(password)
            cursor.execute('''
                INSERT INTO users (username, password_hash, full_name, email, user_type, student_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (username, password_hash, full_name, email, user_type, student_id))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
    
    def authenticate_user(self, username, password, user_type):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM users WHERE username = ? AND user_type = ?
        ''', (username, user_type))
        
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            return dict(user)
        return None
    
    def create_assignment(self, title, description, due_date, max_score, lecturer_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO assignments (title, description, due_date, max_score, lecturer_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (title, description, due_date, max_score, lecturer_id))
            assignment_id = cursor.lastrowid
            conn.commit()
            return assignment_id
        except Exception as e:
            print(f"Error creating assignment: {e}")
            return None
        finally:
            conn.close()
    
    def get_available_assignments(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT a.*, u.full_name as lecturer_name
            FROM assignments a
            JOIN users u ON a.lecturer_id = u.id
            WHERE a.due_date >= date('now')
            ORDER BY a.due_date ASC
        ''')
        
        assignments = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return assignments
    
    def get_lecturer_assignments(self, lecturer_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT a.*, COUNT(s.id) as submission_count
            FROM assignments a
            LEFT JOIN submissions s ON a.id = s.assignment_id
            WHERE a.lecturer_id = ?
            GROUP BY a.id
            ORDER BY a.created_at DESC
        ''', (lecturer_id,))
        
        assignments = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return assignments
    
    def get_assignment(self, assignment_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT a.*, u.full_name as lecturer_name
            FROM assignments a
            JOIN users u ON a.lecturer_id = u.id
            WHERE a.id = ?
        ''', (assignment_id,))
        
        assignment = cursor.fetchone()
        conn.close()
        return dict(assignment) if assignment else None
    
    def create_submission(self, assignment_id, student_id, filename, file_path, plagiarism_score, content):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO submissions (assignment_id, student_id, filename, file_path, 
                                       plagiarism_score, content)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (assignment_id, student_id, filename, file_path, plagiarism_score, content))
            submission_id = cursor.lastrowid
            conn.commit()
            return submission_id
        except Exception as e:
            print(f"Error creating submission: {e}")
            return None
        finally:
            conn.close()
    
    def get_student_submissions(self, student_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT s.*, a.title as assignment_title, a.max_score
            FROM submissions s
            JOIN assignments a ON s.assignment_id = a.id
            WHERE s.student_id = ?
            ORDER BY s.submitted_at DESC
        ''', (student_id,))
        
        submissions = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return submissions
    
    def get_assignment_submissions(self, assignment_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT s.*, u.full_name as student_name, u.student_id
            FROM submissions s
            JOIN users u ON s.student_id = u.id
            WHERE s.assignment_id = ?
            ORDER BY s.submitted_at DESC
        ''', (assignment_id,))
        
        submissions = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return submissions
    
    def get_submission(self, submission_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT s.*, a.title as assignment_title, u.full_name as student_name
            FROM submissions s
            JOIN assignments a ON s.assignment_id = a.id
            JOIN users u ON s.student_id = u.id
            WHERE s.id = ?
        ''', (submission_id,))
        
        submission = cursor.fetchone()
        conn.close()
        return dict(submission) if submission else None
    
    def grade_submission(self, submission_id, score, feedback):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE submissions 
                SET score = ?, feedback = ?, graded_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (score, feedback, submission_id))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error grading submission: {e}")
            return False
        finally:
            conn.close()
    
    def get_recent_submissions(self, limit=10):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT s.*, a.title as assignment_title, u.full_name as student_name
            FROM submissions s
            JOIN assignments a ON s.assignment_id = a.id
            JOIN users u ON s.student_id = u.id
            ORDER BY s.submitted_at DESC
            LIMIT ?
        ''', (limit,))
        
        submissions = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return submissions
    
    def get_plagiarism_statistics(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total_submissions,
                AVG(plagiarism_score) as avg_plagiarism_score,
                COUNT(CASE WHEN plagiarism_score > 30 THEN 1 END) as high_plagiarism_count,
                COUNT(CASE WHEN plagiarism_score > 50 THEN 1 END) as very_high_plagiarism_count
            FROM submissions
        ''')
        
        stats = dict(cursor.fetchone())
        conn.close()
        return stats
