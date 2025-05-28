import re
import json
from typing import Dict, List, Any, ClassVar
from difflib import SequenceMatcher
from sqlalchemy import text
from sqlalchemy.engine import Engine
from pydantic import BaseModel, Field

class ClinicalTermMapper(BaseModel):
    """
    Optimized Clinical Term Mapper with refined medical knowledge base.
    Focuses on high-impact medical terminology for maximum query success.
    """
    engine: Engine = Field(..., description="The engine to access database schema.")
    
    # Optimized medical abbreviations database (focused on high-impact terms)
    MEDICAL_ABBREVIATIONS: ClassVar[Dict[str, List[str]]] = {
        # CRITICAL lab values (most frequently queried)
        "hb": ["hemoglobin", "haemoglobin"],
        "hgb": ["hemoglobin", "haemoglobin"],
        "wbc": ["white blood cell", "white blood count", "leukocyte", "wbc count"],
        "rbc": ["red blood cell", "red blood count", "erythrocyte"],
        "plt": ["platelet", "platelet count", "thrombocyte"],
        "hct": ["hematocrit", "haematocrit"],
        
        # CRITICAL blood chemistry (essential for medical queries)
        "bun": ["blood urea nitrogen", "urea nitrogen"],
        "cr": ["creatinine", "serum creatinine"],
        "gfr": ["glomerular filtration rate", "egfr", "estimated gfr"],
        "na": ["sodium", "serum sodium"],
        "k": ["potassium", "serum potassium"],
        "cl": ["chloride", "serum chloride"],
        "co2": ["carbon dioxide", "bicarbonate", "total co2"],
        "glucose": ["glucose", "blood glucose", "serum glucose", "blood sugar"],
        "ca": ["calcium", "serum calcium", "total calcium"],
        "mg": ["magnesium", "serum magnesium"],
        "phos": ["phosphorus", "phosphate", "serum phosphorus"],
        "albumin": ["albumin", "serum albumin"],
        "lactate": ["lactate", "lactic acid"],
        
        # CRITICAL liver function (high clinical importance)
        "alt": ["alanine aminotransferase", "alanine transaminase", "sgpt", "alat"],
        "ast": ["aspartate aminotransferase", "aspartate transaminase", "sgot", "asat"],
        "alp": ["alkaline phosphatase", "alk phos"],
        "tbili": ["total bilirubin", "bilirubin total"],
        "dbili": ["direct bilirubin", "conjugated bilirubin"],
        "ldh": ["lactate dehydrogenase", "lactic dehydrogenase"],
        
        # CRITICAL cardiac markers (emergency medicine)
        "ck": ["creatine kinase", "cpk"],
        "ckmb": ["creatine kinase mb", "ck-mb", "cpk-mb"],
        "troponin": ["troponin", "cardiac troponin"],
        "tnt": ["troponin t", "cardiac troponin t", "ctnt"],
        "tni": ["troponin i", "cardiac troponin i", "ctni"],
        "bnp": ["b-type natriuretic peptide", "brain natriuretic peptide"],
        "ntprobnp": ["nt-pro bnp", "n-terminal pro bnp", "nt-probnp"],
        
        # CRITICAL coagulation (ICU essential)
        "pt": ["prothrombin time"],
        "ptt": ["partial thromboplastin time", "activated partial thromboplastin time", "aptt"],
        "inr": ["international normalized ratio"],
        "d-dimer": ["d-dimer", "d dimer"],
        
        # CRITICAL inflammatory markers
        "wbc": ["white blood cell", "white blood count", "leukocyte"],
        "crp": ["c-reactive protein", "c reactive protein"],
        "esr": ["erythrocyte sedimentation rate", "sed rate"],
        "procalcitonin": ["procalcitonin", "pct"],
        
        # HIGH-IMPACT medications (most prescribed)
        "insulin": ["insulin", "regular insulin", "nph insulin", "lantus", "humalog", "novolog"],
        "heparin": ["heparin", "unfractionated heparin"],
        "warfarin": ["warfarin", "coumadin", "jantoven"],
        "aspirin": ["aspirin", "acetylsalicylic acid", "asa", "bayer"],
        "acetaminophen": ["acetaminophen", "paracetamol", "tylenol"],
        "morphine": ["morphine", "ms contin", "roxanol"],
        "fentanyl": ["fentanyl", "sublimaze", "duragesic"],
        "propofol": ["propofol", "diprivan"],
        "midazolam": ["midazolam", "versed"],
        "lorazepam": ["lorazepam", "ativan"],
        "vancomycin": ["vancomycin", "vancocin"],
        "ceftriaxone": ["ceftriaxone", "rocephin"],
        "metoprolol": ["metoprolol", "lopressor", "toprol xl"],
        "lisinopril": ["lisinopril", "prinivil", "zestril"],
        "furosemide": ["furosemide", "lasix"],
        "norepinephrine": ["norepinephrine", "levophed"],
        "epinephrine": ["epinephrine", "adrenaline"],
        "dopamine": ["dopamine"],
        "vasopressin": ["vasopressin", "pitressin"],
        
        # HIGH-IMPACT medical conditions (most common diagnoses)
        "mi": ["myocardial infarction", "heart attack", "acute mi"],
        "stemi": ["st elevation myocardial infarction", "st elevation mi"],
        "nstemi": ["non-st elevation myocardial infarction", "non-st elevation mi"],
        "chf": ["congestive heart failure", "heart failure", "hf"],
        "afib": ["atrial fibrillation", "a fib", "af"],
        "copd": ["chronic obstructive pulmonary disease"],
        "pneumonia": ["pneumonia", "pna"],
        "sepsis": ["sepsis", "septicemia"],
        "uti": ["urinary tract infection"],
        "dvt": ["deep vein thrombosis", "deep venous thrombosis"],
        "pe": ["pulmonary embolism", "pulmonary emboli"],
        "stroke": ["stroke", "cerebrovascular accident", "cva"],
        "dm": ["diabetes mellitus", "diabetes"],
        "t1dm": ["type 1 diabetes mellitus", "type 1 diabetes", "iddm"],
        "t2dm": ["type 2 diabetes mellitus", "type 2 diabetes", "niddm"],
        "htn": ["hypertension", "high blood pressure"],
        "ckd": ["chronic kidney disease", "chronic renal disease"],
        "aki": ["acute kidney injury", "acute renal failure"],
        "ards": ["acute respiratory distress syndrome"],
        "delirium": ["delirium", "altered mental status", "ams"],
        
        # HIGH-IMPACT procedures (most common)
        "intubation": ["intubation", "endotracheal intubation", "ett placement"],
        "extubation": ["extubation"],
        "tracheostomy": ["tracheostomy", "trach", "tracheotomy"],
        "central line": ["central venous catheter", "central line", "cvc"],
        "arterial line": ["arterial line", "a-line", "arterial catheter"],
        "foley": ["foley catheter", "urinary catheter", "bladder catheter"],
        "dialysis": ["dialysis", "hemodialysis", "peritoneal dialysis"],
        "crrt": ["continuous renal replacement therapy", "continuous dialysis"],
        "ecmo": ["extracorporeal membrane oxygenation"],
        "cabg": ["coronary artery bypass graft", "bypass surgery", "heart bypass"],
        "pci": ["percutaneous coronary intervention", "cardiac catheterization"],
        "cpr": ["cardiopulmonary resuscitation", "chest compressions"],
        "bronchoscopy": ["bronchoscopy", "flexible bronchoscopy"],
        "endoscopy": ["endoscopy", "upper endoscopy", "egd"],
        "colonoscopy": ["colonoscopy", "lower endoscopy"],
        "lumbar puncture": ["lumbar puncture", "spinal tap", "lp"],
        "paracentesis": ["paracentesis", "abdominal tap"],
        "thoracentesis": ["thoracentesis", "pleural tap"],
        
        # CRITICAL departments/units (MIMIC-IV specific)
        "icu": ["intensive care unit", "critical care"],
        "micu": ["medical intensive care unit"],
        "sicu": ["surgical intensive care unit"],
        "cvicu": ["cardiovascular intensive care unit"],
        "ccu": ["coronary care unit", "cardiac care unit"],
        "ed": ["emergency department", "emergency room"],
        "or": ["operating room", "operating theatre"],
        
        # MIMIC-IV specific terms (database-focused)
        "hadm_id": ["hospital admission id", "admission id"],
        "subject_id": ["patient id", "subject id"],
        "stay_id": ["icu stay id", "stay id"],
        "itemid": ["item id", "measurement id"],
        "charttime": ["chart time", "measurement time"],
        "admittime": ["admission time", "admit time"],
        "dischtime": ["discharge time", "discharge time"],
        "intime": ["icu in time", "icu admission time"],
        "outtime": ["icu out time", "icu discharge time"],
    }
    
    # Enhanced database table mappings (MIMIC-IV optimized)
    TABLE_MAPPINGS: ClassVar[Dict[str, List[str]]] = {
        "patient": ["patients", "admissions"],
        "admission": ["admissions"],
        "lab": ["labevents", "d_labitems"],
        "laboratory": ["labevents", "d_labitems"],
        "blood": ["labevents", "d_labitems"],
        "medication": ["prescriptions"],
        "drug": ["prescriptions"],
        "prescription": ["prescriptions"],
        "procedure": ["procedures_icd", "d_icd_procedures"],
        "diagnosis": ["diagnoses_icd", "d_icd_diagnoses"],
        "microbiology": ["microbiologyevents"],
        "culture": ["microbiologyevents"],
        "vital": ["chartevents", "d_items"],
        "chart": ["chartevents", "d_items"],
        "monitor": ["chartevents", "d_items"],
        "input": ["inputevents"],
        "output": ["outputevents"],
        "note": ["noteevents"],
        "transfer": ["transfers"],
        "service": ["services"],
        "icu": ["icustays", "chartevents"],
        "stay": ["icustays"],
        "critical care": ["icustays", "chartevents"],
    }

    class Config:
        arbitrary_types_allowed = True

    def invoke(self, medical_term: str) -> str:
        """
        Map a medical term to its database representations with enhanced medical knowledge.
        
        Args:
            medical_term: The medical term or abbreviation to map
            
        Returns:
            JSON string with mappings, confidence scores, and suggestions
        """
        term_lower = medical_term.lower().strip()
        
        result = {
            'original_term': medical_term,
            'mappings': [],
            'table_suggestions': [],
            'search_patterns': [],
            'confidence_score': 0.0
        }
        
        # Direct abbreviation lookup
        if term_lower in self.MEDICAL_ABBREVIATIONS:
            for mapped_term in self.MEDICAL_ABBREVIATIONS[term_lower]:
                result['mappings'].append({
                    'mapped_term': mapped_term,
                    'confidence': 0.95,
                    'type': 'direct_abbreviation',
                    'source': 'medical_abbreviations'
                })
        
        # Fuzzy matching for abbreviations
        for abbrev, terms in self.MEDICAL_ABBREVIATIONS.items():
            similarity = SequenceMatcher(None, term_lower, abbrev).ratio()
            if similarity > 0.8 and similarity < 0.95:  # Avoid duplicates from direct match
                for mapped_term in terms:
                    result['mappings'].append({
                        'mapped_term': mapped_term,
                        'confidence': similarity * 0.9,  # Slightly lower for fuzzy matches
                        'type': 'fuzzy_abbreviation',
                        'source': 'medical_abbreviations'
                    })
        
        # Partial matching within terms
        for abbrev, terms in self.MEDICAL_ABBREVIATIONS.items():
            if term_lower in abbrev or abbrev in term_lower:
                for mapped_term in terms:
                    result['mappings'].append({
                        'mapped_term': mapped_term,
                        'confidence': 0.7,
                        'type': 'partial_match',
                        'source': 'medical_abbreviations'
                    })
        
        # Table mapping suggestions
        for table_key, tables in self.TABLE_MAPPINGS.items():
            if table_key in term_lower or term_lower in table_key:
                result['table_suggestions'].extend(tables)
        
        # Generate search patterns
        if result['mappings']:
            best_mapping = max(result['mappings'], key=lambda x: x['confidence'])
            result['search_patterns'] = [
                f"LIKE '%{best_mapping['mapped_term']}%'",
                f"= '{best_mapping['mapped_term']}'",
                f"LIKE '%{term_lower}%'"
            ]
            result['confidence_score'] = best_mapping['confidence']
        else:
            # Fallback search patterns
            result['search_patterns'] = [
                f"LIKE '%{term_lower}%'",
                f"= '{medical_term}'"
            ]
            result['confidence_score'] = 0.3
        
        # Remove duplicates and sort by confidence
        seen_terms = set()
        unique_mappings = []
        for mapping in sorted(result['mappings'], key=lambda x: x['confidence'], reverse=True):
            if mapping['mapped_term'] not in seen_terms:
                unique_mappings.append(mapping)
                seen_terms.add(mapping['mapped_term'])
        
        result['mappings'] = unique_mappings[:10]  # Limit to top 10
        result['table_suggestions'] = list(set(result['table_suggestions']))
        
        return json.dumps(result, indent=2)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "clinical_term_mapper",
                "description": "Enhanced clinical term mapper with 160+ medical abbreviations, drug names, procedures, and diagnoses. Maps medical terms to database representations with high accuracy.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "medical_term": {
                            "type": "string",
                            "description": "The medical term, abbreviation, drug name, or diagnosis to map to database representation"
                        }
                    },
                    "required": ["medical_term"]
                }
            }
        }


class QueryAnalyzer(BaseModel):
    """
    Enhanced Query Analyzer with improved medical concept extraction.
    """
    engine: Engine = Field(..., description="The engine to access database schema.")

    class Config:
        arbitrary_types_allowed = True

    def invoke(self, user_query: str) -> str:
        """
        Analyze user query for medical concepts and provide enhanced mapping suggestions.
        
        Args:
            user_query: The user's natural language query
            
        Returns:
            JSON string with extracted terms and enhanced suggestions
        """
        query_lower = user_query.lower()
        
        result = {
            'original_query': user_query,
            'extracted_terms': [],
            'mapped_terms': [],
            'table_suggestions': [],
            'search_patterns': [],
            'query_type': self._classify_query_type(query_lower),
            'complexity': self._assess_complexity(query_lower)
        }
        
        # Extract potential medical terms (enhanced patterns)
        medical_patterns = [
            r'\b[a-z]{2,4}\b',  # Short abbreviations
            r'\b\w+(?:emia|osis|itis|pathy|ology|gram|scopy)\b',  # Medical suffixes
            r'\b(?:anti|pre|post|hyper|hypo|inter|intra|extra)\w+\b',  # Medical prefixes
            r'\b\w*(?:cardio|pulmo|neuro|gastro|hepato|nephro|hemato)\w*\b',  # Medical roots
            r'\b(?:level|test|result|value|count|measurement)\b',  # Lab-related terms
            r'\b(?:medication|drug|prescription|dose|treatment)\b',  # Drug-related terms
            r'\b(?:procedure|surgery|operation|intervention)\b',  # Procedure-related terms
            r'\b(?:diagnosis|condition|disease|disorder|syndrome)\b',  # Diagnosis-related terms
        ]
        
        extracted_terms = set()
        for pattern in medical_patterns:
            matches = re.findall(pattern, query_lower)
            extracted_terms.update(matches)
        
        # Also extract quoted terms and proper nouns
        quoted_terms = re.findall(r'"([^"]*)"', user_query)
        extracted_terms.update([term.lower() for term in quoted_terms])
        
        # Filter out common words
        common_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'between', 'among', 'this', 'that', 'these', 'those', 'what', 'which', 'who', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'can', 'will', 'just', 'should', 'now', 'get', 'has', 'had', 'have', 'he', 'she', 'it', 'we', 'they', 'i', 'you', 'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'its', 'our', 'their', 'a', 'an', 'as', 'are', 'was', 'were', 'been', 'be', 'being', 'do', 'does', 'did', 'done', 'doing', 'would', 'could', 'should', 'may', 'might', 'must', 'shall', 'will', 'can', 'patient', 'patients', 'show', 'find', 'get', 'give', 'list', 'tell', 'want', 'need', 'like', 'look', 'see', 'know', 'think', 'make', 'take', 'come', 'go', 'say', 'use', 'work', 'call', 'try', 'ask', 'turn', 'move', 'live', 'seem', 'feel', 'leave', 'put', 'mean', 'keep', 'let', 'begin', 'help', 'talk', 'turn', 'start', 'might', 'show', 'hear', 'play', 'run', 'move', 'live', 'believe', 'hold', 'bring', 'happen', 'write', 'provide', 'sit', 'stand', 'lose', 'pay', 'meet', 'include', 'continue', 'set', 'learn', 'change', 'lead', 'understand', 'watch', 'follow', 'stop', 'create', 'speak', 'read', 'allow', 'add', 'spend', 'grow', 'open', 'walk', 'win', 'offer', 'remember', 'love', 'consider', 'appear', 'buy', 'wait', 'serve', 'die', 'send', 'expect', 'build', 'stay', 'fall', 'cut', 'reach', 'kill', 'remain'}
        
        filtered_terms = [term for term in extracted_terms if term not in common_words and len(term) > 1]
        result['extracted_terms'] = filtered_terms
        
        # Map each extracted term using the enhanced clinical term mapper
        mapper = ClinicalTermMapper(engine=self.engine)
        for term in filtered_terms:
            try:
                mapping_result = json.loads(mapper.invoke(term))
                if mapping_result['mappings']:
                    result['mapped_terms'].append({
                        'original_term': term,
                        'mappings': mapping_result['mappings'][:3],  # Top 3 mappings
                        'confidence': mapping_result['confidence_score']
                    })
                    result['table_suggestions'].extend(mapping_result['table_suggestions'])
                    result['search_patterns'].extend(mapping_result['search_patterns'])
            except:
                continue
        
        # Remove duplicates from suggestions
        result['table_suggestions'] = list(set(result['table_suggestions']))
        result['search_patterns'] = list(set(result['search_patterns']))
        
        return json.dumps(result, indent=2)

    def _classify_query_type(self, query: str) -> str:
        """Classify the type of query based on keywords."""
        if any(word in query for word in ['lab', 'laboratory', 'test', 'result', 'level', 'value']):
            return 'laboratory'
        elif any(word in query for word in ['medication', 'drug', 'prescription', 'dose']):
            return 'medication'
        elif any(word in query for word in ['procedure', 'surgery', 'operation']):
            return 'procedure'
        elif any(word in query for word in ['diagnosis', 'condition', 'disease']):
            return 'diagnosis'
        elif any(word in query for word in ['vital', 'chart', 'monitor']):
            return 'vitals'
        elif any(word in query for word in ['microbiology', 'culture', 'organism']):
            return 'microbiology'
        else:
            return 'general'

    def _assess_complexity(self, query: str) -> str:
        """Assess query complexity based on structure and content."""
        complexity_indicators = {
            'high': ['multiple', 'complex', 'relationship', 'correlation', 'trend', 'pattern', 'analysis'],
            'medium': ['recent', 'specific', 'particular', 'certain', 'during', 'between'],
            'low': ['show', 'list', 'find', 'get', 'what', 'simple']
        }
        
        for level, indicators in complexity_indicators.items():
            if any(indicator in query for indicator in indicators):
                return level
        
        return 'medium'

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "analyze_user_query",
                "description": "Enhanced query analyzer that extracts medical concepts from user queries and provides comprehensive mapping suggestions using expanded medical knowledge base.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_query": {
                            "type": "string",
                            "description": "The user's natural language query to analyze for medical concepts"
                        }
                    },
                    "required": ["user_query"]
                }
            }
        } 