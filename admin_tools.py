#!/usr/bin/env python3
"""
Administrative tools for the Assignment Submission System
"""

from database_manager import DatabaseManager
from plagiarism_detector import PlagiarismDetector
import os
import sqlite3
from datetime import datetime, timedelta

class AdminTools:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.plagiarism_detector = PlagiarismDetector()
    
    def create_sample_data(self):
        """Create sample assignments and submissions for testing"""
        print("Creating sample data...")
        
        # Create sample assignments
        assignments = [
            {
                'title': 'Introduction to Machine Learning',
                'description': 'Write a comprehensive essay on machine learning fundamentals, algorithms, and applications.',
                'due_date': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
                'max_score': 100,
                'lecturer_id': 1  # Admin user
            },
            {
                'title': 'Database Design Project',
                'description': 'Design and implement a database system for a library management system.',
                'due_date': (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d'),
                'max_score': 150,
                'lecturer_id': 1
            },
            {
                'title': 'Web Development Assignment',
                'description': 'Create a responsive web application using modern web technologies.',
                'due_date': (datetime.now() + timedelta(days=21)).strftime('%Y-%m-%d'),
                'max_score': 120,
                'lecturer_id': 1
            }
        ]
        
        for assignment in assignments:
            assignment_id = self.db_manager.create_assignment(
                assignment['title'],
                assignment['description'],
                assignment['due_date'],
                assignment['max_score'],
                assignment['lecturer_id']
            )
            print(f"Created assignment: {assignment['title']} (ID: {assignment_id})")
        
        print("Sample data created successfully!")
    
    def generate_system_report(self):
        """Generate comprehensive system report"""
        print("Generating System Report")
        print("=" * 50)
        
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        # User statistics
        cursor.execute("SELECT user_type, COUNT(*) FROM users GROUP BY user_type")
        user_stats = cursor.fetchall()
        
        print("User Statistics:")
        for user_type, count in user_stats:
            print(f"  {user_type.title()}s: {count}")
        
        # Assignment statistics
        cursor.execute("SELECT COUNT(*) FROM assignments")
        total_assignments = cursor.fetchone()[0]
        print(f"\nTotal Assignments: {total_assignments}")
        
        # Submission statistics
        cursor.execute("SELECT COUNT(*) FROM submissions")
        total_submissions = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM submissions WHERE score IS NOT NULL")
        graded_submissions = cursor.fetchone()[0]
        
        cursor.execute("SELECT AVG(plagiarism_score) FROM submissions")
        avg_plagiarism = cursor.fetchone()[0] or 0
        
        print(f"Total Submissions: {total_submissions}")
        print(f"Graded Submissions: {graded_submissions}")
        print(f"Average Plagiarism Score: {avg_plagiarism:.2f}%")
        
        # High plagiarism submissions
        cursor.execute("SELECT COUNT(*) FROM submissions WHERE plagiarism_score > 30")
        high_plagiarism = cursor.fetchone()[0]
        
        print(f"High Plagiarism Submissions (>30%): {high_plagiarism}")
        
        # Recent activity
        cursor.execute('''
            SELECT s.submitted_at, u.full_name, a.title, s.plagiarism_score
            FROM submissions s
            JOIN users u ON s.student_id = u.id
            JOIN assignments a ON s.assignment_id = a.id
            ORDER BY s.submitted_at DESC
            LIMIT 5
        ''')
        
        recent_submissions = cursor.fetchall()
        
        print("\nRecent Submissions:")
        for submission in recent_submissions:
            print(f"  {submission[0]} - {submission[1]} - {submission[2]} (Plagiarism: {submission[3]:.1f}%)")
        
        conn.close()
    
    def cleanup_old_files(self, days_old=30):
        """Clean up old uploaded files"""
        print(f"Cleaning up files older than {days_old} days...")
        
        upload_dir = 'uploads'
        if not os.path.exists(upload_dir):
            print("Upload directory not found.")
            return
        
        cutoff_date = datetime.now() - timedelta(days=days_old)
        cleaned_count = 0
        
        for filename in os.listdir(upload_dir):
            filepath = os.path.join(upload_dir, filename)
            if os.path.isfile(filepath):
                file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                if file_time < cutoff_date:
                    try:
                        os.remove(filepath)
                        cleaned_count += 1
                        print(f"Removed: {filename}")
                    except Exception as e:
                        print(f"Error removing {filename}: {e}")
        
        print(f"Cleanup complete. Removed {cleaned_count} files.")
    
    def backup_database(self):
        """Create database backup"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"backup_assignment_system_{timestamp}.db"
        
        try:
            # Copy database file
            import shutil
            shutil.copy2('assignment_system.db', backup_filename)
            print(f"Database backup created: {backup_filename}")
        except Exception as e:
            print(f"Backup failed: {e}")
    
    def reset_plagiarism_scores(self):
        """Recalculate all plagiarism scores"""
        print("Recalculating plagiarism scores...")
        
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, content FROM submissions WHERE content IS NOT NULL")
        submissions = cursor.fetchall()
        
        updated_count = 0
        for submission_id, content in submissions:
            if content:
                new_score = self.plagiarism_detector.detect_plagiarism(content)
                cursor.execute(
                    "UPDATE submissions SET plagiarism_score = ? WHERE id = ?",
                    (new_score, submission_id)
                )
                updated_count += 1
                print(f"Updated submission {submission_id}: {new_score:.2f}%")
        
        conn.commit()
        conn.close()
        
        print(f"Updated {updated_count} submissions.")

def main():
    """Main admin interface"""
    admin = AdminTools()
    
    while True:
        print("\n" + "=" * 50)
        print("Assignment Submission System - Admin Tools")
        print("=" * 50)
        print("1. Create sample data")
        print("2. Generate system report")
        print("3. Cleanup old files")
        print("4. Backup database")
        print("5. Reset plagiarism scores")
        print("6. Exit")
        
        choice = input("\nSelect option (1-6): ").strip()
        
        if choice == '1':
            admin.create_sample_data()
        elif choice == '2':
            admin.generate_system_report()
        elif choice == '3':
            days = input("Enter days old (default 30): ").strip()
            days = int(days) if days.isdigit() else 30
            admin.cleanup_old_files(days)
        elif choice == '4':
            admin.backup_database()
        elif choice == '5':
            admin.reset_plagiarism_scores()
        elif choice == '6':
            print("Goodbye!")
            break
        else:
            print("Invalid option. Please try again.")

if __name__ == "__main__":
    main()
