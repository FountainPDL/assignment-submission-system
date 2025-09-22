import os
import mimetypes
from pathlib import Path
import docx
import PyPDF2
import zipfile
import tempfile

class FileProcessor:
    def __init__(self):
        self.allowed_extensions = {
            'txt', 'pdf', 'doc', 'docx', 'py', 'java', 'cpp', 'c', 'js', 'html', 'css'
        }
        self.max_file_size = 16 * 1024 * 1024  # 16MB
    
    def allowed_file(self, filename):
        """Check if file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.allowed_extensions
    
    def get_file_type(self, filename):
        """Get file type from filename"""
        return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    def extract_text(self, filepath):
        """Extract text content from various file types"""
        try:
            file_ext = self.get_file_type(filepath)
            
            if file_ext == 'txt':
                return self.extract_from_txt(filepath)
            elif file_ext == 'pdf':
                return self.extract_from_pdf(filepath)
            elif file_ext in ['doc', 'docx']:
                return self.extract_from_docx(filepath)
            elif file_ext in ['py', 'java', 'cpp', 'c', 'js', 'html', 'css']:
                return self.extract_from_code(filepath)
            else:
                return self.extract_from_txt(filepath)  # Default to text
                
        except Exception as e:
            print(f"Error extracting text from {filepath}: {e}")
            return ""
    
    def extract_from_txt(self, filepath):
        """Extract text from plain text file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                return file.read()
        except UnicodeDecodeError:
            # Try with different encoding
            with open(filepath, 'r', encoding='latin-1') as file:
                return file.read()
    
    def extract_from_pdf(self, filepath):
        """Extract text from PDF file"""
        try:
            text = ""
            with open(filepath, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text
        except Exception as e:
            print(f"Error reading PDF: {e}")
            return ""
    
    def extract_from_docx(self, filepath):
        """Extract text from DOCX file"""
        try:
            doc = docx.Document(filepath)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            print(f"Error reading DOCX: {e}")
            return ""
    
    def extract_from_code(self, filepath):
        """Extract text from code files"""
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()
                
            # Remove comments for better plagiarism detection
            file_ext = self.get_file_type(filepath)
            
            if file_ext in ['py']:
                # Remove Python comments
                lines = content.split('\n')
                cleaned_lines = []
                for line in lines:
                    # Remove inline comments
                    if '#' in line:
                        line = line[:line.index('#')]
                    cleaned_lines.append(line)
                content = '\n'.join(cleaned_lines)
                
            elif file_ext in ['java', 'cpp', 'c', 'js']:
                # Remove C-style comments
                import re
                # Remove single line comments
                content = re.sub(r'//.*', '', content)
                # Remove multi-line comments
                content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
            
            return content
            
        except Exception as e:
            print(f"Error reading code file: {e}")
            return ""
    
    def validate_file(self, filepath):
        """Validate uploaded file"""
        if not os.path.exists(filepath):
            return False, "File does not exist"
        
        file_size = os.path.getsize(filepath)
        if file_size > self.max_file_size:
            return False, f"File size exceeds maximum limit of {self.max_file_size/1024/1024}MB"
        
        if file_size == 0:
            return False, "File is empty"
        
        filename = os.path.basename(filepath)
        if not self.allowed_file(filename):
            return False, f"File type not allowed. Allowed types: {', '.join(self.allowed_extensions)}"
        
        return True, "File is valid"
    
    def get_file_info(self, filepath):
        """Get detailed file information"""
        if not os.path.exists(filepath):
            return None
        
        stat = os.stat(filepath)
        filename = os.path.basename(filepath)
        
        return {
            'filename': filename,
            'size': stat.st_size,
            'size_mb': round(stat.st_size / (1024 * 1024), 2),
            'type': self.get_file_type(filename),
            'created': stat.st_ctime,
            'modified': stat.st_mtime,
            'mime_type': mimetypes.guess_type(filepath)[0]
        }
    
    def clean_filename(self, filename):
        """Clean filename for safe storage"""
        # Remove or replace unsafe characters
        unsafe_chars = '<>:"/\\|?*'
        for char in unsafe_chars:
            filename = filename.replace(char, '_')
        
        # Limit filename length
        name, ext = os.path.splitext(filename)
        if len(name) > 100:
            name = name[:100]
        
        return name + ext
