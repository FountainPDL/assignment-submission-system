#!/usr/bin/env python3
"""
Database initialization script for the Assignment Submission System
Run this script to create the database and initial data
"""

from database_manager import DatabaseManager
import os

def main():
    print("Initializing Assignment Submission System Database...")
    
    # Create database manager instance
    db_manager = DatabaseManager()
    
    # Initialize database
    db_manager.init_database()
    
    print("Database initialized successfully!")
    print("\nDefault users created:")
    print("Lecturer: username='admin', password='admin123'")
    print("Student: username='student1', password='student123'")
    
    # Create uploads directory
    os.makedirs('uploads', exist_ok=True)
    print("\nUploads directory created.")
    
    print("\nSystem is ready to use!")
    print("Run 'python app.py' to start the web application.")

if __name__ == "__main__":
    main()
