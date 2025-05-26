import re
import json
from typing import Dict, List, Any, ClassVar
from difflib import SequenceMatcher
from sqlalchemy import text
from sqlalchemy.engine import Engine
from pydantic import BaseModel, Field

class ClinicalTermMapper(BaseModel):
    """
    A tool to map clinical terms, abbreviations, and natural language 
    to their corresponding database representations in MIMIC-IV.
    """
    engine: Engine = Field(..., description="The engine to access database schema.")

    class Config:
        arbitrary_types_allowed = True

    # Define medical abbreviations as class variables
    medical_abbreviations: ClassVar[Dict[str, str]] = {
        # Common lab abbreviations
        'hb': 'hemoglobin',
        'hgb': 'hemoglobin', 
        'wbc': 'white blood cell',
        'rbc': 'red blood cell',
        'plt': 'platelet',
        'bun': 'blood urea nitrogen',
        'cr': 'creatinine',
        'na': 'sodium',
        'k': 'potassium',
        'cl': 'chloride',
        'co2': 'carbon dioxide',
        'glucose': 'glucose',
        'bilirubin': 'bilirubin',
        'alt': 'alanine aminotransferase',
        'ast': 'aspartate aminotransferase',
        'ldh': 'lactate dehydrogenase',
        'ck': 'creatine kinase',
        'troponin': 'troponin',
        'pt': 'prothrombin time',
        'ptt': 'partial thromboplastin time',
        'inr': 'international normalized ratio',
        
        # Vital signs
        'bp': 'blood pressure',
        'hr': 'heart rate',
        'rr': 'respiratory rate',
        'temp': 'temperature',
        'o2sat': 'oxygen saturation',
        'spo2': 'oxygen saturation',
        
        # Medical conditions
        'mi': 'myocardial infarction',
        'chf': 'congestive heart failure',
        'copd': 'chronic obstructive pulmonary disease',
        'dm': 'diabetes mellitus',
        'htn': 'hypertension',
        'afib': 'atrial fibrillation',
        'pe': 'pulmonary embolism',
        'dvt': 'deep vein thrombosis',
        'uti': 'urinary tract infection',
        'pneumonia': 'pneumonia',
        
        # Medications
        'abx': 'antibiotics',
        'ace': 'angiotensin converting enzyme',
        'arb': 'angiotensin receptor blocker',
        'bb': 'beta blocker',
        'ccb': 'calcium channel blocker',
        'nsaid': 'nonsteroidal anti-inflammatory drug',
        'ppi': 'proton pump inhibitor',
        'h2': 'histamine-2 receptor antagonist'
    }
    
    # Common medical term variations as class variables
    term_variations: ClassVar[Dict[str, List[str]]] = {
        'lab': ['laboratory', 'labs', 'lab test', 'lab result'],
        'medication': ['med', 'meds', 'drug', 'drugs', 'prescription'],
        'diagnosis': ['dx', 'diagnoses', 'condition', 'disease'],
        'procedure': ['proc', 'surgery', 'operation', 'intervention'],
        'admission': ['admit', 'hospitalization', 'stay'],
        'discharge': ['dc', 'disch', 'release'],
        'patient': ['pt', 'subject', 'individual', 'person'],
        'doctor': ['physician', 'md', 'provider', 'clinician'],
        'nurse': ['rn', 'nursing', 'caregiver']
    }

    def invoke(self, term: str) -> str:
        """
        Map a clinical term to potential database representations.
        
        Args:
            term: The clinical term to map
            
        Returns:
            JSON string with mapping results
        """
        term_lower = term.lower().strip()
        mappings = []
        
        # Direct abbreviation lookup
        if term_lower in self.medical_abbreviations:
            mappings.append({
                'original_term': term,
                'mapped_term': self.medical_abbreviations[term_lower],
                'mapping_type': 'abbreviation_expansion',
                'confidence': 0.95
            })
        
        # Reverse abbreviation lookup
        for abbrev, full_term in self.medical_abbreviations.items():
            if term_lower == full_term or term_lower in full_term:
                mappings.append({
                    'original_term': term,
                    'mapped_term': abbrev,
                    'mapping_type': 'term_to_abbreviation',
                    'confidence': 0.90
                })
        
        # Term variation lookup
        for base_term, variations in self.term_variations.items():
            if term_lower == base_term or term_lower in variations:
                mappings.append({
                    'original_term': term,
                    'mapped_term': base_term,
                    'mapping_type': 'term_standardization',
                    'confidence': 0.85
                })
        
        # Database column/table fuzzy matching
        db_matches = self._find_database_matches(term_lower)
        mappings.extend(db_matches)
        
        # Sort by confidence score
        mappings.sort(key=lambda x: x['confidence'], reverse=True)
        
        # Get related terms
        related_terms = self._get_related_terms(term)
        
        result = {
            'original_term': term,
            'mappings': mappings[:5],  # Return top 5 matches
            'related_terms': related_terms
        }
        
        return json.dumps(result, indent=2)

    def _find_database_matches(self, term: str) -> List[Dict[str, Any]]:
        """Find fuzzy matches in database schema."""
        matches = []
        
        try:
            with self.engine.connect() as conn:
                # Get all table names
                result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
                tables = [row[0] for row in result.fetchall()]
                
                # Get all column names from all tables
                columns = []
                for table in tables:
                    try:
                        result = conn.execute(text(f"PRAGMA table_info({table})"))
                        table_columns = [(table, row[1]) for row in result.fetchall()]
                        columns.extend(table_columns)
                    except:
                        continue  # Skip tables that can't be accessed
                
                # Fuzzy match against table names
                for table in tables:
                    similarity = SequenceMatcher(None, term.lower(), table.lower()).ratio()
                    if similarity > 0.6:
                        matches.append({
                            'original_term': term,
                            'mapped_term': table,
                            'mapping_type': 'table_name_match',
                            'confidence': similarity * 0.8,  # Scale down confidence
                            'table': table
                        })
                
                # Fuzzy match against column names
                for table, column in columns:
                    similarity = SequenceMatcher(None, term.lower(), column.lower()).ratio()
                    if similarity > 0.6:
                        matches.append({
                            'original_term': term,
                            'mapped_term': column,
                            'mapping_type': 'column_name_match',
                            'confidence': similarity * 0.7,  # Scale down confidence
                            'table': table,
                            'column': column
                        })
                        
        except Exception as e:
            # If database access fails, continue with other mappings
            pass
        
        return matches

    def _get_related_terms(self, term: str) -> List[str]:
        """Get related medical terms that might be relevant."""
        term_lower = term.lower().strip()
        related = []
        
        # If it's an abbreviation, add the full term
        if term_lower in self.medical_abbreviations:
            related.append(self.medical_abbreviations[term_lower])
        
        # If it's a full term, add abbreviations
        for abbrev, full_term in self.medical_abbreviations.items():
            if term_lower in full_term.lower():
                related.append(abbrev)
        
        # Add term variations
        for base_term, variations in self.term_variations.items():
            if term_lower == base_term:
                related.extend(variations)
            elif term_lower in variations:
                related.append(base_term)
                related.extend([v for v in variations if v != term_lower])
        
        return list(set(related))  # Remove duplicates

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "clinical_term_mapper",
                "description": "Map clinical terms, abbreviations, and natural language to their corresponding database representations. Helps resolve medical terminology ambiguities.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "term": {
                            "type": "string",
                            "description": "The clinical term, abbreviation, or medical concept to map to database representations."
                        }
                    },
                    "required": ["term"]
                }
            }
        }


class QueryAnalyzer(BaseModel):
    """
    A tool to analyze user queries and suggest better search terms for database exploration.
    """
    engine: Engine = Field(..., description="The engine to access database schema.")

    class Config:
        arbitrary_types_allowed = True

    def invoke(self, user_query: str) -> str:
        """
        Analyze a user query and suggest better search terms for database exploration.
        
        Args:
            user_query: The natural language query from the user
            
        Returns:
            JSON string with suggestions
        """
        suggestions = {
            'mapped_terms': [],
            'related_terms': [],
            'search_patterns': []
        }
        
        # Extract potential medical terms (simple approach)
        words = re.findall(r'\b\w+\b', user_query.lower())
        
        # Create a temporary mapper to use the class attributes
        mapper = ClinicalTermMapper(engine=self.engine)
        
        for word in words:
            # Get mappings for each word
            mapping_result = json.loads(mapper.invoke(word))
            if mapping_result['mappings']:
                suggestions['mapped_terms'].extend([m['mapped_term'] for m in mapping_result['mappings'][:2]])
                
            if mapping_result['related_terms']:
                suggestions['related_terms'].extend(mapping_result['related_terms'])
        
        # Generate search patterns based on query content
        query_lower = user_query.lower()
        if 'recent' in query_lower:
            suggestions['search_patterns'].append('ORDER BY charttime DESC LIMIT')
        if 'lab' in query_lower or 'test' in query_lower:
            suggestions['search_patterns'].append('labevents table')
        if 'medication' in query_lower or 'drug' in query_lower:
            suggestions['search_patterns'].append('prescriptions table')
        if 'admission' in query_lower or 'admit' in query_lower:
            suggestions['search_patterns'].append('admissions table')
        if 'diagnosis' in query_lower or 'condition' in query_lower:
            suggestions['search_patterns'].append('diagnoses_icd table')
        if 'procedure' in query_lower or 'surgery' in query_lower:
            suggestions['search_patterns'].append('procedures_icd table')
        
        # Remove duplicates and empty values
        for key in suggestions:
            suggestions[key] = list(set([s for s in suggestions[key] if s]))
        
        return json.dumps(suggestions, indent=2)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "analyze_user_query",
                "description": "Analyze a user query and suggest better search terms, related medical concepts, and database exploration patterns.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_query": {
                            "type": "string",
                            "description": "The natural language query from the user to analyze for medical terms and database search patterns."
                        }
                    },
                    "required": ["user_query"]
                }
            }
        } 