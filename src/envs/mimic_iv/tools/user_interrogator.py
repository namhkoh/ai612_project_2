import json
from typing import Dict, Any, List
from pydantic import BaseModel, Field

class UserInterrogator(BaseModel):
    """
    A tool that generates targeted follow-up questions to clarify ambiguous or incomplete user requests.
    Particularly useful for complex EHR queries where specificity is crucial.
    """
    
    class Config:
        arbitrary_types_allowed = True

    def invoke(self, user_request: str, context_type: str = "medical", focus_area: str = "general") -> str:
        """
        Generate targeted follow-up questions based on the user's request.
        
        Args:
            user_request: The original user request that needs clarification
            context_type: The domain context ("medical", "administrative", "research")
            focus_area: Specific area to focus questions on ("dates", "codes", "demographics", "procedures", "medications", "labs", "general")
        """
        try:
            questions = self._generate_questions(user_request, context_type, focus_area)
            
            if not questions:
                return "The request seems clear. No additional questions needed."
            
            # Format the questions nicely
            question_text = "To provide the most accurate results, I need to clarify a few details:\n\n"
            for i, question in enumerate(questions, 1):
                question_text += f"{i}. {question}\n"
            
            question_text += "\nPlease provide any relevant details to help me generate the correct SQL query."
            
            return question_text
            
        except Exception as e:
            return f"Error generating questions: {str(e)}"

    def _generate_questions(self, user_request: str, context_type: str, focus_area: str) -> List[str]:
        """Generate context-appropriate questions based on the request analysis."""
        
        request_lower = user_request.lower()
        questions = []
        
        # Medical/EHR specific question patterns
        if context_type == "medical":
            questions.extend(self._get_medical_questions(request_lower, focus_area))
        
        # General database questions
        questions.extend(self._get_general_questions(request_lower, focus_area))
        
        # Remove duplicates while preserving order
        seen = set()
        unique_questions = []
        for q in questions:
            if q not in seen:
                seen.add(q)
                unique_questions.append(q)
        
        # Limit to most relevant questions (max 5)
        return unique_questions[:5]

    def _get_medical_questions(self, request_lower: str, focus_area: str) -> List[str]:
        """Generate medical/EHR specific questions."""
        questions = []
        
        # Diagnosis related questions
        if any(word in request_lower for word in ['diagnos', 'condition', 'disease', 'disorder', 'icd']):
            if focus_area in ["codes", "general"]:
                questions.extend([
                    "Which specific diagnosis codes should I use (e.g., ICD-10 codes like 'E11' for Type 2 diabetes)?",
                    "Are you looking for primary diagnoses only, or should I include secondary diagnoses?",
                    "Do you want to include related/similar diagnoses or only exact matches?"
                ])
        
        # Procedure related questions  
        if any(word in request_lower for word in ['procedure', 'surgery', 'operation', 'treatment']):
            if focus_area in ["procedures", "codes", "general"]:
                questions.extend([
                    "Which specific procedure codes should I search for (e.g., CPT or ICD-10-PCS codes)?",
                    "Are you interested in inpatient procedures, outpatient procedures, or both?",
                    "Do you want to include related procedures or only the specific procedure mentioned?"
                ])
        
        # Medication related questions
        if any(word in request_lower for word in ['medication', 'drug', 'prescription', 'med']):
            if focus_area in ["medications", "general"]:
                questions.extend([
                    "Are you looking for specific drug names, drug classes, or both?",
                    "Should I include all formulations (oral, IV, etc.) or specific routes of administration?",
                    "Do you want current medications, medications during admission, or historical medications?"
                ])
        
        # Lab/test related questions
        if any(word in request_lower for word in ['lab', 'test', 'result', 'value', 'level']):
            if focus_area in ["labs", "general"]:
                questions.extend([
                    "Which specific lab tests are you interested in (e.g., 'HbA1c', 'Creatinine')?",
                    "Do you need specific value ranges or thresholds (e.g., 'HbA1c > 7.0')?",
                    "Are you looking for the most recent results or results from a specific time period?"
                ])
        
        # Patient demographics
        if any(word in request_lower for word in ['patient', 'age', 'gender', 'male', 'female']):
            if focus_area in ["demographics", "general"]:
                questions.extend([
                    "What specific age range should I use (e.g., 'over 65', '18-65', 'pediatric')?",
                    "Should I include any other demographic criteria (gender, ethnicity, etc.)?",
                    "Are you looking for patients at admission or current patient characteristics?"
                ])
        
        # Date/time related questions
        if any(word in request_lower for word in ['when', 'date', 'time', 'during', 'recent', 'last']):
            if focus_area in ["dates", "general"]:
                questions.extend([
                    "What specific date range should I use (e.g., 'last 30 days', 'Q1 2025', '2024-01-01 to 2024-12-31')?",
                    "Are you referring to admission dates, procedure dates, or other specific timestamps?",
                    "Should I use admission time, discharge time, or the time when procedures/events occurred?"
                ])
        
        return questions

    def _get_general_questions(self, request_lower: str, focus_area: str) -> List[str]:
        """Generate general database questions."""
        questions = []
        
        # Ambiguous quantities
        if any(word in request_lower for word in ['some', 'many', 'few', 'several', 'multiple']):
            questions.append("Can you specify the exact number or range you're looking for?")
        
        # Vague time references
        if any(word in request_lower for word in ['recent', 'lately', 'soon', 'old']):
            if focus_area in ["dates", "general"]:
                questions.append("Can you provide specific dates or time periods?")
        
        # Output format preferences
        if focus_area in ["general"]:
            if 'count' not in request_lower and 'how many' not in request_lower:
                questions.extend([
                    "What specific information would you like to see in the results (patient IDs, names, dates, values, etc.)?",
                    "Do you want individual records or summary/aggregate information?"
                ])
        
        # Scope clarification
        if any(word in request_lower for word in ['all', 'every', 'any']):
            questions.append("Should I include all matching records or limit to a specific subset?")
        
        return questions

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "user_interrogator_tool",
                "description": "Generate targeted follow-up questions to clarify ambiguous or incomplete user requests. Helps gather specific details needed for accurate EHR SQL query generation.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_request": {
                            "type": "string", 
                            "description": "The original user request that needs clarification."
                        },
                        "context_type": {
                            "type": "string",
                            "enum": ["medical", "administrative", "research"],
                            "description": "The domain context to focus questions on. 'medical' for clinical queries, 'administrative' for operational data, 'research' for analytical queries."
                        },
                        "focus_area": {
                            "type": "string",
                            "enum": ["dates", "codes", "demographics", "procedures", "medications", "labs", "general"],
                            "description": "Specific area to focus clarifying questions on, or 'general' for broad clarification."
                        }
                    },
                    "required": ["user_request"]
                }
            }
        } 