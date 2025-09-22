#!/usr/bin/env python3
"""
Test script for the plagiarism detection system
"""

from plagiarism_detector import PlagiarismDetector
import time

def test_plagiarism_detection():
    """Test the plagiarism detection functionality"""
    print("Testing Plagiarism Detection System")
    print("=" * 50)
    
    # Initialize detector
    detector = PlagiarismDetector()
    
    # Test texts
    test_cases = [
        {
            'name': 'Original Text',
            'text': '''
            Artificial intelligence represents a revolutionary approach to computing that aims to create 
            systems capable of performing tasks that typically require human intelligence. This field 
            encompasses various subdomains including machine learning, natural language processing, 
            computer vision, and robotics. The development of AI systems involves complex algorithms 
            and mathematical models that enable computers to learn from data and make decisions.
            '''
        },
        {
            'name': 'Slightly Modified (Low Plagiarism)',
            'text': '''
            Artificial intelligence is a groundbreaking approach to computing that seeks to develop 
            systems capable of executing tasks that usually require human intelligence. This domain 
            includes various subfields such as machine learning, natural language processing, 
            computer vision, and robotics. Creating AI systems requires sophisticated algorithms 
            and mathematical models that allow computers to learn from information and make choices.
            '''
        },
        {
            'name': 'Heavily Copied (High Plagiarism)',
            'text': '''
            Machine learning is a subset of artificial intelligence that focuses on algorithms.
            The importance of data preprocessing cannot be overstated in machine learning projects.
            Neural networks are inspired by the biological neural networks of animal brains.
            '''
        },
        {
            'name': 'Original Research Text',
            'text': '''
            The implementation of blockchain technology in educational systems presents unique 
            opportunities for credential verification and academic record management. This research 
            explores the potential applications of distributed ledger technology in creating 
            tamper-proof academic transcripts and certificates. The proposed system utilizes 
            smart contracts to automate verification processes while maintaining student privacy.
            '''
        }
    ]
    
    # Test each case
    for i, case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {case['name']}")
        print("-" * 30)
        
        start_time = time.time()
        score = detector.detect_plagiarism(case['text'])
        end_time = time.time()
        
        report = detector.get_detailed_report(case['text'])
        
        print(f"Plagiarism Score: {score:.2f}%")
        print(f"Risk Level: {report['risk_level']}")
        print(f"Processing Time: {(end_time - start_time):.3f} seconds")
        print(f"Word Count: {report['word_count']}")
        print(f"Recommendations: {', '.join(report['recommendations'][:2])}")
    
    print("\n" + "=" * 50)
    print("Plagiarism Detection Test Complete!")

def test_file_processing():
    """Test file processing capabilities"""
    print("\nTesting File Processing")
    print("=" * 30)
    
    from file_processor import FileProcessor
    processor = FileProcessor()
    
    # Test allowed file types
    test_files = [
        'document.txt',
        'assignment.pdf',
        'code.py',
        'report.docx',
        'script.js',
        'invalid.exe'
    ]
    
    for filename in test_files:
        is_allowed = processor.allowed_file(filename)
        print(f"{filename}: {'✓ Allowed' if is_allowed else '✗ Not allowed'}")

if __name__ == "__main__":
    test_plagiarism_detection()
    test_file_processing()
