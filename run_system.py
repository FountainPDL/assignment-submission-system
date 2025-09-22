#!/usr/bin/env python3
"""
Main runner script for the Assignment Submission System
This script sets up the environment and starts the application
"""

import os
import sys
from database_manager import DatabaseManager
from plagiarism_detector import PlagiarismDetector

def setup_system():
    """Setup the system components"""
    print("Setting up Assignment Submission System...")
    
    # Create necessary directories
    directories = ['uploads', 'templates', 'static/css', 'static/js']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Created directory: {directory}")
    
    # Initialize database
    print("Initializing database...")
    db_manager = DatabaseManager()
    db_manager.init_database()
    print("Database initialized successfully!")
    
    # Initialize plagiarism detector
    print("Initializing plagiarism detection system...")
    plagiarism_detector = PlagiarismDetector()
    print("Plagiarism detection system ready!")
    
    print("\nSystem setup complete!")
    print("Default users:")
    print("- Lecturer: admin / admin123")
    print("- Student: student1 / student123")

def main():
    """Main function to run the system"""
    setup_system()
    
    print("\nStarting web application...")
    print("Access the system at: http://localhost:5000")
    
    # Import and run the Flask app
    from app import app
    app.run(debug=True, host='0.0.0.0', port=5000)

if __name__ == "__main__":
    main()
