import re
import json
from typing import Dict, List, Any, ClassVar
from difflib import SequenceMatcher
from sqlalchemy import text
from sqlalchemy.engine import Engine
from pydantic import BaseModel, Field

class ClinicalTermMapper(BaseModel):
    """
    Enhanced Clinical Term Mapper with expanded medical knowledge base.
    Maps medical abbreviations, drug names, procedures, and diagnoses to database representations.
    """
    engine: Engine = Field(..., description="The engine to access database schema.")
    
    # Enhanced medical abbreviations database (160+ terms)
    MEDICAL_ABBREVIATIONS: ClassVar[Dict[str, List[str]]] = {
        # Basic vital signs and measurements
        "hb": ["hemoglobin", "haemoglobin"],
        "hgb": ["hemoglobin", "haemoglobin"],
        "wbc": ["white blood cell", "white blood count", "leukocyte"],
        "rbc": ["red blood cell", "red blood count", "erythrocyte"],
        "plt": ["platelet", "platelet count", "thrombocyte"],
        "hct": ["hematocrit", "haematocrit"],
        "mcv": ["mean corpuscular volume"],
        "mch": ["mean corpuscular hemoglobin"],
        "mchc": ["mean corpuscular hemoglobin concentration"],
        "rdw": ["red cell distribution width"],
        "mpv": ["mean platelet volume"],
        
        # Blood chemistry
        "bun": ["blood urea nitrogen", "urea nitrogen"],
        "cr": ["creatinine", "serum creatinine"],
        "gfr": ["glomerular filtration rate"],
        "na": ["sodium", "serum sodium"],
        "k": ["potassium", "serum potassium"],
        "cl": ["chloride", "serum chloride"],
        "co2": ["carbon dioxide", "bicarbonate"],
        "anion gap": ["anion gap"],
        "glucose": ["glucose", "blood glucose", "serum glucose"],
        "ca": ["calcium", "serum calcium"],
        "mg": ["magnesium", "serum magnesium"],
        "phos": ["phosphorus", "phosphate", "serum phosphorus"],
        "albumin": ["albumin", "serum albumin"],
        "protein": ["total protein", "serum protein"],
        
        # Liver function
        "alt": ["alanine aminotransferase", "alanine transaminase", "sgpt"],
        "ast": ["aspartate aminotransferase", "aspartate transaminase", "sgot"],
        "alp": ["alkaline phosphatase"],
        "tbili": ["total bilirubin", "bilirubin total"],
        "dbili": ["direct bilirubin", "conjugated bilirubin"],
        "ibili": ["indirect bilirubin", "unconjugated bilirubin"],
        "ggt": ["gamma glutamyl transferase"],
        "ldh": ["lactate dehydrogenase"],
        
        # Cardiac markers
        "ck": ["creatine kinase"],
        "ckmb": ["creatine kinase mb", "ck-mb"],
        "troponin": ["troponin", "cardiac troponin"],
        "tnt": ["troponin t", "cardiac troponin t"],
        "tni": ["troponin i", "cardiac troponin i"],
        "bnp": ["b-type natriuretic peptide", "brain natriuretic peptide"],
        "ntprobnp": ["nt-pro bnp", "n-terminal pro bnp"],
        
        # Coagulation
        "pt": ["prothrombin time"],
        "ptt": ["partial thromboplastin time", "activated partial thromboplastin time", "aptt"],
        "inr": ["international normalized ratio"],
        "fibrinogen": ["fibrinogen"],
        "d-dimer": ["d-dimer", "d dimer"],
        
        # Lipids
        "chol": ["cholesterol", "total cholesterol"],
        "hdl": ["high density lipoprotein", "hdl cholesterol"],
        "ldl": ["low density lipoprotein", "ldl cholesterol"],
        "tg": ["triglycerides", "triglyceride"],
        "vldl": ["very low density lipoprotein"],
        
        # Thyroid
        "tsh": ["thyroid stimulating hormone", "thyrotropin"],
        "t3": ["triiodothyronine", "t3 total"],
        "t4": ["thyroxine", "t4 total"],
        "ft3": ["free t3", "free triiodothyronine"],
        "ft4": ["free t4", "free thyroxine"],
        
        # Diabetes
        "hba1c": ["hemoglobin a1c", "glycated hemoglobin", "glycosylated hemoglobin"],
        "fructosamine": ["fructosamine"],
        "c-peptide": ["c-peptide", "c peptide"],
        
        # Inflammatory markers
        "esr": ["erythrocyte sedimentation rate", "sed rate"],
        "crp": ["c-reactive protein", "c reactive protein"],
        "procalcitonin": ["procalcitonin"],
        
        # Vitamins and nutrients
        "b12": ["vitamin b12", "cobalamin"],
        "folate": ["folic acid", "folate"],
        "vit d": ["vitamin d", "25-hydroxyvitamin d"],
        "iron": ["iron", "serum iron"],
        "tibc": ["total iron binding capacity"],
        "ferritin": ["ferritin"],
        "transferrin": ["transferrin"],
        
        # Hormones
        "cortisol": ["cortisol"],
        "insulin": ["insulin"],
        "growth hormone": ["growth hormone", "gh"],
        "prolactin": ["prolactin"],
        "testosterone": ["testosterone"],
        "estradiol": ["estradiol"],
        "progesterone": ["progesterone"],
        
        # Immunology
        "iga": ["immunoglobulin a"],
        "igg": ["immunoglobulin g"],
        "igm": ["immunoglobulin m"],
        "ige": ["immunoglobulin e"],
        "complement c3": ["complement c3", "c3"],
        "complement c4": ["complement c4", "c4"],
        
        # Drug names and variations
        "acetaminophen": ["acetaminophen", "paracetamol", "tylenol"],
        "aspirin": ["aspirin", "acetylsalicylic acid", "asa"],
        "ibuprofen": ["ibuprofen", "advil", "motrin"],
        "morphine": ["morphine", "ms contin"],
        "fentanyl": ["fentanyl", "sublimaze"],
        "propofol": ["propofol", "diprivan"],
        "midazolam": ["midazolam", "versed"],
        "lorazepam": ["lorazepam", "ativan"],
        "diazepam": ["diazepam", "valium"],
        "heparin": ["heparin", "unfractionated heparin"],
        "warfarin": ["warfarin", "coumadin"],
        "insulin": ["insulin", "regular insulin", "nph insulin"],
        "metformin": ["metformin", "glucophage"],
        "lisinopril": ["lisinopril", "prinivil", "zestril"],
        "metoprolol": ["metoprolol", "lopressor", "toprol"],
        "furosemide": ["furosemide", "lasix"],
        "digoxin": ["digoxin", "lanoxin"],
        "amiodarone": ["amiodarone", "cordarone"],
        "vancomycin": ["vancomycin", "vancocin"],
        "ceftriaxone": ["ceftriaxone", "rocephin"],
        "piperacillin": ["piperacillin", "zosyn", "piperacillin-tazobactam"],
        "norepinephrine": ["norepinephrine", "levophed"],
        "epinephrine": ["epinephrine", "adrenaline"],
        "dopamine": ["dopamine"],
        "dobutamine": ["dobutamine"],
        "vasopressin": ["vasopressin", "pitressin"],
        
        # Common medical conditions and diagnoses
        "mi": ["myocardial infarction", "heart attack"],
        "cabg": ["coronary artery bypass graft", "coronary bypass"],
        "copd": ["chronic obstructive pulmonary disease"],
        "uti": ["urinary tract infection"],
        "dvt": ["deep vein thrombosis", "deep venous thrombosis"],
        "pe": ["pulmonary embolism"],
        "chf": ["congestive heart failure", "heart failure"],
        "afib": ["atrial fibrillation"],
        "vtach": ["ventricular tachycardia"],
        "vfib": ["ventricular fibrillation"],
        "svt": ["supraventricular tachycardia"],
        "cad": ["coronary artery disease"],
        "pvd": ["peripheral vascular disease"],
        "dm": ["diabetes mellitus", "diabetes"],
        "t1dm": ["type 1 diabetes mellitus", "type 1 diabetes"],
        "t2dm": ["type 2 diabetes mellitus", "type 2 diabetes"],
        "htn": ["hypertension", "high blood pressure"],
        "hyperlipidemia": ["hyperlipidemia", "dyslipidemia"],
        "ckd": ["chronic kidney disease"],
        "esrd": ["end stage renal disease"],
        "arf": ["acute renal failure", "acute kidney injury"],
        "aki": ["acute kidney injury", "acute renal failure"],
        "pneumonia": ["pneumonia", "pna"],
        "sepsis": ["sepsis", "septicemia"],
        "ards": ["acute respiratory distress syndrome"],
        "copd exacerbation": ["copd exacerbation", "chronic obstructive pulmonary disease exacerbation"],
        "asthma": ["asthma", "bronchial asthma"],
        "stroke": ["stroke", "cerebrovascular accident", "cva"],
        "tia": ["transient ischemic attack"],
        "seizure": ["seizure", "epileptic seizure"],
        "delirium": ["delirium", "altered mental status"],
        "dementia": ["dementia", "alzheimer disease"],
        "depression": ["depression", "major depressive disorder"],
        "anxiety": ["anxiety", "anxiety disorder"],
        "bipolar": ["bipolar disorder", "manic depression"],
        "schizophrenia": ["schizophrenia"],
        "cancer": ["cancer", "malignancy", "neoplasm"],
        "leukemia": ["leukemia", "blood cancer"],
        "lymphoma": ["lymphoma"],
        "cirrhosis": ["cirrhosis", "liver cirrhosis"],
        "hepatitis": ["hepatitis"],
        "pancreatitis": ["pancreatitis"],
        "cholecystitis": ["cholecystitis", "gallbladder inflammation"],
        "appendicitis": ["appendicitis"],
        "diverticulitis": ["diverticulitis"],
        "ibd": ["inflammatory bowel disease"],
        "crohns": ["crohn disease", "crohns disease"],
        "uc": ["ulcerative colitis"],
        "gerd": ["gastroesophageal reflux disease", "acid reflux"],
        "pud": ["peptic ulcer disease"],
        "gi bleed": ["gastrointestinal bleeding", "gi bleeding"],
        "upper gi bleed": ["upper gastrointestinal bleeding"],
        "lower gi bleed": ["lower gastrointestinal bleeding"],
        
        # Procedures and interventions
        "intubation": ["intubation", "endotracheal intubation"],
        "extubation": ["extubation"],
        "tracheostomy": ["tracheostomy", "trach"],
        "central line": ["central venous catheter", "central line", "cvc"],
        "arterial line": ["arterial line", "a-line", "arterial catheter"],
        "foley": ["foley catheter", "urinary catheter"],
        "ng tube": ["nasogastric tube", "ng tube"],
        "chest tube": ["chest tube", "thoracostomy tube"],
        "dialysis": ["dialysis", "hemodialysis", "peritoneal dialysis"],
        "crrt": ["continuous renal replacement therapy"],
        "ecmo": ["extracorporeal membrane oxygenation"],
        "iabp": ["intra-aortic balloon pump"],
        "pci": ["percutaneous coronary intervention"],
        "ptca": ["percutaneous transluminal coronary angioplasty"],
        "stent": ["coronary stent", "stent placement"],
        "pacemaker": ["pacemaker", "permanent pacemaker"],
        "icd": ["implantable cardioverter defibrillator"],
        "crt": ["cardiac resynchronization therapy"],
        "cardioversion": ["cardioversion", "electrical cardioversion"],
        "defibrillation": ["defibrillation"],
        "cpr": ["cardiopulmonary resuscitation"],
        "acls": ["advanced cardiac life support"],
        "bls": ["basic life support"],
        "bronchoscopy": ["bronchoscopy"],
        "endoscopy": ["endoscopy", "upper endoscopy", "egd"],
        "colonoscopy": ["colonoscopy"],
        "lumbar puncture": ["lumbar puncture", "spinal tap"],
        "paracentesis": ["paracentesis", "abdominal tap"],
        "thoracentesis": ["thoracentesis", "pleural tap"],
        "biopsy": ["biopsy", "tissue biopsy"],
        "surgery": ["surgery", "surgical procedure", "operation"],
        "laparoscopy": ["laparoscopy", "laparoscopic surgery"],
        "craniotomy": ["craniotomy"],
        "laminectomy": ["laminectomy"],
        "appendectomy": ["appendectomy"],
        "cholecystectomy": ["cholecystectomy", "gallbladder removal"],
        "colectomy": ["colectomy", "colon resection"],
        "gastrectomy": ["gastrectomy", "stomach resection"],
        "nephrectomy": ["nephrectomy", "kidney removal"],
        "hysterectomy": ["hysterectomy"],
        "mastectomy": ["mastectomy"],
        "amputation": ["amputation"],
        
        # Medical specialties and departments
        "icu": ["intensive care unit", "critical care"],
        "ccu": ["coronary care unit", "cardiac care unit"],
        "micu": ["medical intensive care unit"],
        "sicu": ["surgical intensive care unit"],
        "cvicu": ["cardiovascular intensive care unit"],
        "nicu": ["neonatal intensive care unit"],
        "picu": ["pediatric intensive care unit"],
        "ed": ["emergency department", "emergency room"],
        "or": ["operating room", "operating theatre"],
        "pacu": ["post anesthesia care unit", "recovery room"],
        "step down": ["step down unit", "intermediate care"],
        "telemetry": ["telemetry unit", "cardiac monitoring"],
        "oncology": ["oncology", "cancer care"],
        "cardiology": ["cardiology", "cardiac care"],
        "pulmonology": ["pulmonology", "respiratory care"],
        "nephrology": ["nephrology", "kidney care"],
        "gastroenterology": ["gastroenterology", "gi care"],
        "neurology": ["neurology", "neurological care"],
        "psychiatry": ["psychiatry", "mental health"],
        "orthopedics": ["orthopedics", "orthopedic surgery"],
        "urology": ["urology", "urological care"],
        "gynecology": ["gynecology", "women's health"],
        "obstetrics": ["obstetrics", "pregnancy care"],
        "pediatrics": ["pediatrics", "child care"],
        "geriatrics": ["geriatrics", "elderly care"],
        "palliative": ["palliative care", "comfort care"],
        "hospice": ["hospice care", "end of life care"],
    }
    
    # Database table mappings
    TABLE_MAPPINGS: ClassVar[Dict[str, List[str]]] = {
        "patient": ["patients", "admissions"],
        "admission": ["admissions"],
        "lab": ["labevents", "d_labitems"],
        "laboratory": ["labevents", "d_labitems"],
        "medication": ["prescriptions"],
        "drug": ["prescriptions"],
        "prescription": ["prescriptions"],
        "procedure": ["procedures_icd", "d_icd_procedures"],
        "diagnosis": ["diagnoses_icd", "d_icd_diagnoses"],
        "microbiology": ["microbiologyevents"],
        "culture": ["microbiologyevents"],
        "vital": ["chartevents", "d_items"],
        "chart": ["chartevents", "d_items"],
        "input": ["inputevents"],
        "output": ["outputevents"],
        "note": ["noteevents"],
        "transfer": ["transfers"],
        "service": ["services"],
        "icu": ["icustays"],
        "stay": ["icustays"],
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