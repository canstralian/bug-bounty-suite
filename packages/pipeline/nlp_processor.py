import os
import logging
from typing import Optional, Dict

from langchain_mistralai.chat_models import ChatMistralAI
from langchain_mistralai.embeddings import MistralAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)

class NLPProcessor:
    def __init__(self):
        """Initialize the NLP processor with LangChain models"""
        logger.info("Initializing NLP processor...")
        self.mistral_api_key = os.environ.get('MISTRAL_API_KEY')
        self.text_splitter = RecursiveCharacterTextSplitter()
        self.llm = None
        self.embeddings = None
        
        try:
            if self.mistral_api_key:
                self.llm = ChatMistralAI(
                    mistral_api_key=self.mistral_api_key,
                    model="mistral-tiny"
                )
                self.embeddings = MistralAIEmbeddings(
                    model="mistral-embed",
                    mistral_api_key=self.mistral_api_key
                )
                logger.info("LangChain models initialized successfully")
            else:
                logger.warning("MISTRAL_API_KEY not found, falling back to basic processing")
        except Exception as e:
            logger.error(f"Error initializing LangChain models: {str(e)}")
            logger.info("Continuing with fallback processing")

    def _process_with_langchain(self, prompt_template: str, context: str) -> Optional[str]:
        """Process text using LangChain if available"""
        try:
            if self.llm:
                prompt = ChatPromptTemplate.from_template(prompt_template)
                result = self.llm.invoke(prompt.format(context=context))
                return result.content
        except Exception as e:
            logger.error(f"LangChain processing failed: {str(e)}")
        return None

    def classify_vulnerability(self, text: str) -> str:
        """Classify the type of vulnerability in the bug report"""
        logger.info("Classifying vulnerability...")
        
        prompt = """Based on the following bug report, classify the type of security vulnerability.
        Only return one of these categories: XSS, SQL Injection, CSRF, Authentication, Access Control, Other.
        
        Bug Report: {context}
        
        Classification:"""
        
        result = self._process_with_langchain(prompt, text)
        if result:
            return result.strip()
            
        # Fallback to basic keyword matching
        text_lower = text.lower()
        if "xss" in text_lower or "script" in text_lower:
            return "XSS"
        elif "sql" in text_lower or "injection" in text_lower:
            return "SQL Injection"
        elif "csrf" in text_lower:
            return "CSRF"
        elif "auth" in text_lower or "login" in text_lower:
            return "Authentication"
        elif "permission" in text_lower or "access" in text_lower:
            return "Access Control"
        return "Other"

    def generate_solution(self, vulnerability_type: str, description: str) -> str:
        """Generate a solution for the identified vulnerability"""
        prompt = """Based on the following vulnerability type and description, 
        provide a detailed technical solution with specific steps to fix the issue.
        
        Vulnerability Type: {context}
        Description: {description}
        
        Solution:"""
        
        result = self._process_with_langchain(prompt.format(context=vulnerability_type, description=description))
        if result:
            return result.strip()
            
        # Fallback solutions
        solutions: Dict[str, str] = {
            "XSS": """1. Implement input validation and sanitization
2. Use proper output encoding (e.g., HTML escape special characters)
3. Implement Content Security Policy (CSP)
4. Use secure frameworks that automatically escape output
5. Validate and sanitize all user inputs on both client and server side""",
            
            "SQL Injection": """1. Use parameterized queries or prepared statements
2. Implement proper input validation and sanitization
3. Use an ORM (Object-Relational Mapping)
4. Apply the principle of least privilege for database users
5. Regular security audits of database queries""",
            
            "CSRF": """1. Implement anti-CSRF tokens
2. Use SameSite cookie attribute
3. Verify Origin and Referer headers
4. Implement proper session management
5. Use secure framework CSRF protection""",
            
            "Authentication": """1. Implement secure password hashing
2. Use secure session management
3. Implement multi-factor authentication
4. Set secure cookie attributes
5. Implement account lockout policies""",
            
            "Access Control": """1. Implement role-based access control (RBAC)
2. Validate user permissions on every request
3. Use secure session management
4. Implement proper authentication checks
5. Regular security audits""",
            
            "Other": """1. Review security best practices
2. Implement input validation
3. Apply principle of least privilege
4. Regular security testing
5. Keep all dependencies updated"""
        }
        
        return solutions.get(vulnerability_type, solutions["Other"])

    def generate_response(self, vulnerability_type: str, description: str) -> str:
        """Generate a response for the bug bounty submission"""
        prompt = """Generate a professional and detailed response for a bug bounty submission.
        The response should acknowledge the issue, thank the researcher, and provide next steps.
        
        Vulnerability Type: {context}
        Description: {description}
        
        Response:"""
        
        result = self._process_with_langchain(prompt.format(context=vulnerability_type, description=description))
        if result:
            return result.strip()
            
        # Fallback response template
        return f"""Thank you for submitting this potential {vulnerability_type} vulnerability.

We take all security reports seriously and appreciate your responsible disclosure. Our security team has been notified and will investigate this issue promptly.

We will analyze the reported vulnerability and its potential impact on our systems. You can expect an update from our team within 2-3 business days.

Thank you again for helping us maintain the security of our platform."""
