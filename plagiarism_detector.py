import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import SVC
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.model_selection import train_test_split
import pickle
import os
import re
from datetime import datetime
import hashlib

class PlagiarismDetector:
    def __init__(self, model_path='plagiarism_model.pkl'):
        self.model_path = model_path
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 3),
            lowercase=True
        )
        self.svm_model = SVC(kernel='rbf', probability=True, random_state=42)
        self.similarity_threshold = 0.3
        self.plagiarism_threshold = 30.0
        
        # Database of known texts for comparison
        self.reference_texts = []
        self.load_or_create_model()
    
    def preprocess_text(self, text):
        """Clean and preprocess text for analysis"""
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,!?;:]', '', text)
        
        # Convert to lowercase
        text = text.lower()
        
        return text
    
    def extract_features(self, text):
        """Extract features from text for SVM classification"""
        # Basic text statistics
        word_count = len(text.split())
        char_count = len(text)
        sentence_count = len(re.split(r'[.!?]+', text))
        avg_word_length = np.mean([len(word) for word in text.split()])
        
        # Vocabulary richness
        unique_words = len(set(text.split()))
        vocabulary_richness = unique_words / word_count if word_count > 0 else 0
        
        # Punctuation density
        punctuation_count = len(re.findall(r'[.,!?;:]', text))
        punctuation_density = punctuation_count / char_count if char_count > 0 else 0
        
        return np.array([
            word_count, char_count, sentence_count, avg_word_length,
            vocabulary_richness, punctuation_density
        ])
    
    def generate_training_data(self):
        """Generate synthetic training data for the SVM model"""
        # Original texts (low plagiarism)
        original_texts = [
            "Machine learning is a subset of artificial intelligence that focuses on algorithms.",
            "The importance of data preprocessing cannot be overstated in machine learning projects.",
            "Neural networks are inspired by the biological neural networks of animal brains.",
            "Deep learning has revolutionized computer vision and natural language processing.",
            "Support vector machines are effective for classification and regression tasks.",
            "Cross-validation is essential for evaluating machine learning model performance.",
            "Feature engineering plays a crucial role in the success of machine learning models.",
            "Overfitting occurs when a model learns the training data too well.",
            "Regularization techniques help prevent overfitting in machine learning models.",
            "Ensemble methods combine multiple models to improve prediction accuracy."
        ]
        
        # Plagiarized texts (high plagiarism - slight modifications of originals)
        plagiarized_texts = [
            "Machine learning is a part of artificial intelligence that concentrates on algorithms.",
            "The significance of data preprocessing cannot be understated in ML projects.",
            "Neural nets are inspired by the biological neural networks of animal minds.",
            "Deep learning has transformed computer vision and natural language processing.",
            "Support vector machines are useful for classification and regression problems.",
            "Cross validation is essential for evaluating machine learning model performance.",
            "Feature engineering has a crucial role in the success of ML models.",
            "Overfitting happens when a model learns the training data too well.",
            "Regularization methods help prevent overfitting in machine learning models.",
            "Ensemble techniques combine multiple models to improve prediction accuracy."
        ]
        
        # Combine and label data
        texts = original_texts + plagiarized_texts
        labels = [0] * len(original_texts) + [1] * len(plagiarized_texts)  # 0: original, 1: plagiarized
        
        return texts, labels
    
    def train_model(self):
        """Train the SVM model for plagiarism detection"""
        texts, labels = self.generate_training_data()
        
        # Extract features
        features = []
        for text in texts:
            processed_text = self.preprocess_text(text)
            text_features = self.extract_features(processed_text)
            features.append(text_features)
        
        features = np.array(features)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            features, labels, test_size=0.2, random_state=42
        )
        
        # Train SVM model
        self.svm_model.fit(X_train, y_train)
        
        # Store reference texts for similarity comparison
        self.reference_texts = [self.preprocess_text(text) for text in texts]
        
        # Save model
        self.save_model()
        
        print(f"Model trained with accuracy: {self.svm_model.score(X_test, y_test):.2f}")
    
    def save_model(self):
        """Save the trained model and vectorizer"""
        model_data = {
            'svm_model': self.svm_model,
            'vectorizer': self.vectorizer,
            'reference_texts': self.reference_texts
        }
        
        with open(self.model_path, 'wb') as f:
            pickle.dump(model_data, f)
    
    def load_model(self):
        """Load the trained model and vectorizer"""
        try:
            with open(self.model_path, 'rb') as f:
                model_data = pickle.load(f)
                self.svm_model = model_data['svm_model']
                self.vectorizer = model_data['vectorizer']
                self.reference_texts = model_data['reference_texts']
            return True
        except FileNotFoundError:
            return False
    
    def load_or_create_model(self):
        """Load existing model or create new one"""
        if not self.load_model():
            print("Training new plagiarism detection model...")
            self.train_model()
    
    def calculate_similarity_score(self, text):
        """Calculate similarity with reference texts"""
        if not self.reference_texts:
            return 0.0
        
        processed_text = self.preprocess_text(text)
        
        # Combine with reference texts for vectorization
        all_texts = self.reference_texts + [processed_text]
        
        try:
            # Fit vectorizer on all texts
            tfidf_matrix = self.vectorizer.fit_transform(all_texts)
            
            # Calculate similarity with each reference text
            similarities = cosine_similarity(tfidf_matrix[-1:], tfidf_matrix[:-1])
            max_similarity = np.max(similarities)
            
            return float(max_similarity)
        except:
            return 0.0
    
    def detect_plagiarism(self, text):
        """Main plagiarism detection function"""
        if not text or len(text.strip()) < 10:
            return 0.0
        
        processed_text = self.preprocess_text(text)
        
        # Extract features for SVM
        text_features = self.extract_features(processed_text)
        
        # Get SVM prediction probability
        try:
            svm_probability = self.svm_model.predict_proba([text_features])[0][1]
        except:
            svm_probability = 0.0
        
        # Calculate similarity score
        similarity_score = self.calculate_similarity_score(text)
        
        # Combine scores (weighted average)
        final_score = (svm_probability * 0.6 + similarity_score * 0.4) * 100
        
        return min(final_score, 100.0)  # Cap at 100%
    
    def get_detailed_report(self, text):
        """Generate detailed plagiarism report"""
        processed_text = self.preprocess_text(text)
        plagiarism_score = self.detect_plagiarism(text)
        
        # Extract features
        features = self.extract_features(processed_text)
        similarity_score = self.calculate_similarity_score(text)
        
        # Determine risk level
        if plagiarism_score < 15:
            risk_level = "Low"
            risk_color = "green"
        elif plagiarism_score < 30:
            risk_level = "Medium"
            risk_color = "yellow"
        elif plagiarism_score < 50:
            risk_level = "High"
            risk_color = "orange"
        else:
            risk_level = "Very High"
            risk_color = "red"
        
        report = {
            'plagiarism_score': round(plagiarism_score, 2),
            'similarity_score': round(similarity_score * 100, 2),
            'risk_level': risk_level,
            'risk_color': risk_color,
            'word_count': len(processed_text.split()),
            'character_count': len(processed_text),
            'unique_words': len(set(processed_text.split())),
            'recommendations': self.get_recommendations(plagiarism_score),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return report
    
    def get_recommendations(self, score):
        """Get recommendations based on plagiarism score"""
        if score < 15:
            return ["Content appears to be original.", "Good academic integrity maintained."]
        elif score < 30:
            return [
                "Some similarities detected with existing content.",
                "Review citations and references.",
                "Consider paraphrasing similar sections."
            ]
        elif score < 50:
            return [
                "Significant similarities found.",
                "Manual review recommended.",
                "Check for proper citations and quotations.",
                "Consider rewriting similar sections."
            ]
        else:
            return [
                "High plagiarism risk detected.",
                "Immediate manual review required.",
                "Substantial rewriting may be necessary.",
                "Verify all sources are properly cited."
            ]
    
    def add_reference_text(self, text):
        """Add new reference text to the database"""
        processed_text = self.preprocess_text(text)
        if processed_text not in self.reference_texts:
            self.reference_texts.append(processed_text)
            self.save_model()
