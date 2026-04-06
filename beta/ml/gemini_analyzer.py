"""
Gemini AI Integration Module
Handles text analysis, content generation, and Q&A with Google Gemini API
"""

import os
from typing import Optional, List, Dict, Any
import google.generativeai as genai


class GeminiAnalyzer:
    """Wrapper for Google Gemini API for advanced text analysis"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Gemini client"""
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not set in environment")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-pro')
    
    def analyze_content(self, text: str, analysis_type: str = "summary") -> Dict[str, Any]:
        """
        Analyze content with Gemini
        
        Args:
            text: Content to analyze
            analysis_type: "summary", "insights", "questions", "improvement"
        
        Returns:
            Dictionary with analysis results
        """
        prompts = {
            "summary": f"Provide a concise 2-sentence summary of: {text}",
            "insights": f"Extract key insights and takeaways from: {text}",
            "questions": f"Generate 3 interesting discussion questions about: {text}",
            "improvement": f"Suggest how to improve this content for engagement: {text}",
            "critique": f"Provide constructive feedback on this post: {text}"
        }
        
        prompt = prompts.get(analysis_type, prompts["summary"])
        
        try:
            response = self.model.generate_content(prompt)
            return {
                "status": "success",
                "analysis_type": analysis_type,
                "result": response.text,
                "model": "gemini-pro"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "analysis_type": analysis_type
            }
    
    def generate_response(self, question: str, context: Optional[str] = None) -> str:
        """Generate a response to a question with optional context"""
        if context:
            prompt = f"Context: {context}\n\nQuestion: {question}\n\nProvide a helpful answer."
        else:
            prompt = question
        
        response = self.model.generate_content(prompt)
        return response.text
    
    def batch_analyze(self, texts: List[str], analysis_type: str = "summary") -> List[Dict[str, Any]]:
        """Analyze multiple texts"""
        results = []
        for text in texts:
            result = self.analyze_content(text, analysis_type)
            results.append(result)
        return results
    
    def detect_topics(self, text: str) -> Dict[str, Any]:
        """Detect main topics in text using Gemini"""
        prompt = f"""Analyze this text and identify the main topics/themes.
Format as JSON with 'topics' (list of strings) and 'relevance' (0-1 for each).
Text: {text}"""
        
        try:
            response = self.model.generate_content(prompt)
            # Parse response text as JSON
            import json
            # Try to extract JSON from response
            response_text = response.text
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = response_text[start:end]
                topics_data = json.loads(json_str)
            else:
                topics_data = {"topics": response_text.split(", "), "relevance": [1.0] * 5}
            
            return {
                "status": "success",
                "topics": topics_data
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }


def get_gemini_analyzer() -> Optional[GeminiAnalyzer]:
    """Factory function to get Gemini analyzer instance
    
    Returns:
        GeminiAnalyzer instance if GEMINI_API_KEY is set, None otherwise
    """
    try:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return None
        return GeminiAnalyzer(api_key=api_key)
    except Exception as e:
        print(f"Failed to initialize Gemini analyzer: {e}")
        return None
