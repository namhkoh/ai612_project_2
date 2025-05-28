import re
import json
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy import text
from sqlalchemy.engine import Engine
from pydantic import BaseModel, Field

class SmartSchemaAssistant(BaseModel):
    """
    A tool to provide intelligent schema guidance and query validation for MIMIC-IV database.
    Helps agents understand table relationships and avoid common schema mistakes.
    """
    engine: Engine = Field(..., description="The engine to access database schema.")

    class Config:
        arbitrary_types_allowed = True

    def invoke(self, query_intent: str) -> str:
        """
        Provide intelligent schema guidance based on query intent.
        
        Args:
            query_intent: Description of what the user wants to query
            
        Returns:
            JSON string with schema guidance and recommendations
        """
        guidance = {
            'recommended_tables': [],
            'required_joins': [],
            'common_mistakes': [],
            'example_patterns': [],
            'column_mappings': {}
        }
        
        intent_lower = query_intent.lower()
        
        # Analyze intent and provide specific guidance
        if any(word in intent_lower for word in ['lab', 'laboratory', 'test', 'result']):
            guidance.update(self._get_lab_guidance())
        
        if any(word in intent_lower for word in ['medication', 'drug', 'prescription', 'med']):
            guidance.update(self._get_medication_guidance())
            
        if any(word in intent_lower for word in ['procedure', 'surgery', 'operation']):
            guidance.update(self._get_procedure_guidance())
            
        if any(word in intent_lower for word in ['diagnosis', 'condition', 'disease']):
            guidance.update(self._get_diagnosis_guidance())
            
        if any(word in intent_lower for word in ['admission', 'admit', 'hospital', 'stay']):
            guidance.update(self._get_admission_guidance())
            
        if any(word in intent_lower for word in ['vital', 'chart', 'monitor']):
            guidance.update(self._get_vitals_guidance())
            
        # Add general schema tips
        guidance['general_tips'] = self._get_general_tips()
        
        return json.dumps(guidance, indent=2)

    def _get_lab_guidance(self) -> Dict[str, Any]:
        """Provide enhanced guidance for lab-related queries."""
        return {
            'recommended_tables': ['labevents', 'd_labitems', 'admissions'],
            'required_joins': [
                'labevents.itemid = d_labitems.itemid (CRITICAL: to get lab names)',
                'labevents.hadm_id = admissions.hadm_id (to link to admissions)'
            ],
            'common_mistakes': [
                'Using labevents.label (does not exist) - use d_labitems.label instead',
                'Forgetting to join with d_labitems to get readable lab names',
                'Using wrong time column - use labevents.charttime',
                'Not filtering NULL values: WHERE labevents.valuenum IS NOT NULL'
            ],
            'example_patterns': [
                'SELECT d_labitems.label, labevents.valuenum, labevents.charttime FROM labevents JOIN d_labitems ON labevents.itemid = d_labitems.itemid',
                'WHERE d_labitems.label LIKE \'%hemoglobin%\' AND labevents.valuenum IS NOT NULL',
                'ORDER BY labevents.charttime DESC LIMIT 10 -- for most recent results'
            ],
            'column_mappings': {
                'lab_name': 'd_labitems.label',
                'lab_value': 'labevents.valuenum',
                'lab_time': 'labevents.charttime',
                'lab_units': 'labevents.valueuom',
                'patient_id': 'labevents.subject_id',
                'admission_id': 'labevents.hadm_id'
            },
            'optimization_tips': [
                'Use specific lab names in WHERE clause for better performance',
                'Always include time constraints to limit result size',
                'Filter NULL values early in the query'
            ]
        }

    def _get_medication_guidance(self) -> Dict[str, Any]:
        """Provide enhanced guidance for medication-related queries."""
        return {
            'recommended_tables': ['prescriptions', 'admissions'],
            'required_joins': [
                'prescriptions.hadm_id = admissions.hadm_id (to link to admissions)'
            ],
            'common_mistakes': [
                'Using wrong time column - use prescriptions.starttime or endtime',
                'Not handling drug name variations - use LIKE with wildcards',
                'Forgetting that drug names can have multiple formats',
                'Not considering dose information - use dose_val_rx and dose_unit_rx'
            ],
            'example_patterns': [
                'SELECT drug, starttime, endtime, dose_val_rx, dose_unit_rx FROM prescriptions',
                'WHERE drug LIKE \'%insulin%\' AND starttime IS NOT NULL',
                'ORDER BY starttime DESC -- for most recent prescriptions'
            ],
            'column_mappings': {
                'drug_name': 'prescriptions.drug',
                'start_time': 'prescriptions.starttime',
                'end_time': 'prescriptions.endtime',
                'dose_value': 'prescriptions.dose_val_rx',
                'dose_unit': 'prescriptions.dose_unit_rx',
                'route': 'prescriptions.route',
                'patient_id': 'prescriptions.subject_id',
                'admission_id': 'prescriptions.hadm_id'
            },
            'optimization_tips': [
                'Use UPPER() or LOWER() for case-insensitive drug name matching',
                'Include time constraints to focus on relevant periods',
                'Consider grouping by patient for medication histories'
            ]
        }

    def _get_procedure_guidance(self) -> Dict[str, Any]:
        """Provide enhanced guidance for procedure-related queries."""
        return {
            'recommended_tables': ['procedures_icd', 'd_icd_procedures', 'admissions'],
            'required_joins': [
                'procedures_icd.icd_code = d_icd_procedures.icd_code (CRITICAL: to get procedure names)',
                'procedures_icd.hadm_id = admissions.hadm_id (to link to admissions)'
            ],
            'common_mistakes': [
                'Using procedures_icd.long_title (does not exist) - use d_icd_procedures.long_title',
                'Forgetting to join with d_icd_procedures to get readable procedure names',
                'Using wrong time column - use procedures_icd.charttime',
                'Not considering seq_num for procedure ordering'
            ],
            'example_patterns': [
                'SELECT d_icd_procedures.long_title, procedures_icd.charttime, procedures_icd.seq_num',
                'FROM procedures_icd JOIN d_icd_procedures ON procedures_icd.icd_code = d_icd_procedures.icd_code',
                'WHERE d_icd_procedures.long_title LIKE \'%catheter%\' ORDER BY procedures_icd.charttime'
            ],
            'column_mappings': {
                'procedure_name': 'd_icd_procedures.long_title',
                'procedure_time': 'procedures_icd.charttime',
                'icd_code': 'procedures_icd.icd_code',
                'sequence_number': 'procedures_icd.seq_num',
                'patient_id': 'procedures_icd.subject_id',
                'admission_id': 'procedures_icd.hadm_id'
            },
            'optimization_tips': [
                'Use seq_num = 1 for primary procedures',
                'Include admission context for procedure timing',
                'Consider procedure categories for broader searches'
            ]
        }

    def _get_diagnosis_guidance(self) -> Dict[str, Any]:
        """Provide enhanced guidance for diagnosis-related queries."""
        return {
            'recommended_tables': ['diagnoses_icd', 'd_icd_diagnoses', 'admissions'],
            'required_joins': [
                'diagnoses_icd.icd_code = d_icd_diagnoses.icd_code (CRITICAL: to get diagnosis names)',
                'diagnoses_icd.hadm_id = admissions.hadm_id (to link to admissions)'
            ],
            'common_mistakes': [
                'Using diagnoses_icd.long_title (does not exist) - use d_icd_diagnoses.long_title',
                'Forgetting to join with d_icd_diagnoses to get readable diagnosis names',
                'Not distinguishing primary vs secondary diagnoses - use seq_num'
            ],
            'example_patterns': [
                'SELECT d_icd_diagnoses.long_title, diagnoses_icd.seq_num',
                'FROM diagnoses_icd JOIN d_icd_diagnoses ON diagnoses_icd.icd_code = d_icd_diagnoses.icd_code',
                'WHERE d_icd_diagnoses.long_title LIKE \'%diabetes%\' AND diagnoses_icd.seq_num = 1 -- primary diagnosis only'
            ],
            'column_mappings': {
                'diagnosis_name': 'd_icd_diagnoses.long_title',
                'icd_code': 'diagnoses_icd.icd_code',
                'sequence_number': 'diagnoses_icd.seq_num',
                'patient_id': 'diagnoses_icd.subject_id',
                'admission_id': 'diagnoses_icd.hadm_id'
            },
            'optimization_tips': [
                'Use seq_num = 1 for primary diagnoses only',
                'Consider ICD code patterns for related conditions',
                'Group by patient for diagnosis histories'
            ]
        }

    def _get_admission_guidance(self) -> Dict[str, Any]:
        """Provide enhanced guidance for admission-related queries."""
        return {
            'recommended_tables': ['admissions', 'patients'],
            'required_joins': [
                'admissions.subject_id = patients.subject_id (to link to patient info)'
            ],
            'common_mistakes': [
                'Using admission_time (does not exist) - use admissions.admittime',
                'Using discharge_time (does not exist) - use admissions.dischtime',
                'Confusing subject_id (patient) with hadm_id (admission)',
                'Not calculating length of stay properly'
            ],
            'example_patterns': [
                'SELECT admittime, dischtime, admission_type, ROUND((JULIANDAY(dischtime) - JULIANDAY(admittime)), 2) as length_of_stay',
                'FROM admissions WHERE admittime > \'2100-01-01\'',
                'ORDER BY admittime DESC'
            ],
            'column_mappings': {
                'admission_time': 'admissions.admittime',
                'discharge_time': 'admissions.dischtime',
                'patient_age': 'admissions.age',
                'admission_type': 'admissions.admission_type',
                'admission_location': 'admissions.admission_location',
                'discharge_location': 'admissions.discharge_location',
                'patient_id': 'admissions.subject_id',
                'admission_id': 'admissions.hadm_id'
            },
            'optimization_tips': [
                'Use JULIANDAY() for length of stay calculations',
                'Filter by admission_type for specific admission categories',
                'Include time constraints for recent admissions'
            ]
        }

    def _get_vitals_guidance(self) -> Dict[str, Any]:
        """Provide enhanced guidance for vital signs and chart events."""
        return {
            'recommended_tables': ['chartevents', 'd_items', 'icustays'],
            'required_joins': [
                'chartevents.itemid = d_items.itemid (CRITICAL: to get vital sign names)',
                'chartevents.stay_id = icustays.stay_id (to link to ICU stays)'
            ],
            'common_mistakes': [
                'Using chartevents.label (does not exist) - use d_items.label',
                'Using wrong time column - use chartevents.charttime',
                'Not filtering by relevant itemids for vital signs',
                'Not handling NULL values in chartevents.valuenum'
            ],
            'example_patterns': [
                'SELECT d_items.label, chartevents.valuenum, chartevents.charttime',
                'FROM chartevents JOIN d_items ON chartevents.itemid = d_items.itemid',
                'WHERE d_items.label LIKE \'%heart rate%\' AND chartevents.valuenum IS NOT NULL',
                'AND chartevents.charttime BETWEEN icustays.intime AND icustays.outtime'
            ],
            'column_mappings': {
                'vital_name': 'd_items.label',
                'vital_value': 'chartevents.valuenum',
                'vital_time': 'chartevents.charttime',
                'vital_units': 'chartevents.valueuom',
                'icu_stay_id': 'chartevents.stay_id',
                'patient_id': 'chartevents.subject_id'
            },
            'optimization_tips': [
                'Filter by ICU stay times for relevant measurements',
                'Use specific vital sign names for better performance',
                'Consider aggregating by time periods for trends'
            ]
        }

    def _get_general_tips(self) -> List[str]:
        """Provide enhanced general schema tips."""
        return [
            'CRITICAL: Always join event tables with their dictionary tables (d_*) to get readable names',
            'Use hadm_id to link different events for the same hospital admission',
            'Use subject_id to link events for the same patient across admissions',
            'Time columns: charttime (events), admittime/dischtime (admissions), intime/outtime (ICU)',
            'Always filter NULL values: WHERE valuenum IS NOT NULL for numeric data',
            'Use LIKE with wildcards (%) for flexible text matching: WHERE label LIKE \'%hemoglobin%\'',
            'Include time constraints to improve query performance and relevance',
            'Use ORDER BY charttime DESC LIMIT N for most recent results',
            'Consider seq_num for primary diagnoses (seq_num = 1) vs secondary',
            'Use stay_id for ICU-specific events, hadm_id for hospital-wide events',
            'PERFORMANCE: Always include WHERE clauses to limit result size',
            'ACCURACY: Double-check table joins - missing joins cause incorrect results'
        ]

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "smart_schema_assistant",
                "description": "Get intelligent schema guidance for MIMIC-IV database queries. Provides table recommendations, required joins, common mistakes to avoid, and example patterns based on query intent.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query_intent": {
                            "type": "string",
                            "description": "Description of what you want to query (e.g., 'find lab results for patients', 'get medication history', 'analyze procedures')"
                        }
                    },
                    "required": ["query_intent"]
                }
            }
        }


class QueryValidator(BaseModel):
    """
    A tool to validate SQL queries before execution and suggest corrections.
    """
    engine: Engine = Field(..., description="The engine to access database schema.")

    class Config:
        arbitrary_types_allowed = True

    def invoke(self, sql_query: str) -> str:
        """
        Validate a SQL query and suggest corrections.
        
        Args:
            sql_query: The SQL query to validate
            
        Returns:
            JSON string with validation results and suggestions
        """
        validation = {
            'is_valid': True,
            'issues': [],
            'suggestions': [],
            'corrected_query': None
        }
        
        query_lower = sql_query.lower()
        
        # Check for common column name mistakes
        issues = []
        
        # Lab events common mistakes
        if 'labevents.label' in query_lower:
            issues.append({
                'type': 'wrong_column',
                'message': 'labevents.label does not exist',
                'suggestion': 'Use d_labitems.label and join: labevents.itemid = d_labitems.itemid'
            })
        
        # Admission time mistakes
        if 'admission_time' in query_lower:
            issues.append({
                'type': 'wrong_column',
                'message': 'admission_time column does not exist',
                'suggestion': 'Use admissions.admittime instead'
            })
        
        # Procedure mistakes
        if 'procedures_icd.long_title' in query_lower:
            issues.append({
                'type': 'wrong_column',
                'message': 'procedures_icd.long_title does not exist',
                'suggestion': 'Use d_icd_procedures.long_title and join: procedures_icd.icd_code = d_icd_procedures.icd_code'
            })
        
        # Chart events mistakes
        if 'chartevents.label' in query_lower:
            issues.append({
                'type': 'wrong_column',
                'message': 'chartevents.label does not exist',
                'suggestion': 'Use d_items.label and join: chartevents.itemid = d_items.itemid'
            })
        
        # Input events time mistakes
        if 'inputevents.eventtime' in query_lower:
            issues.append({
                'type': 'wrong_column',
                'message': 'inputevents.eventtime does not exist',
                'suggestion': 'Use inputevents.starttime instead'
            })
        
        # Check for missing joins
        if 'labevents' in query_lower and 'd_labitems' not in query_lower and 'label' in query_lower:
            issues.append({
                'type': 'missing_join',
                'message': 'Query references lab labels but missing d_labitems join',
                'suggestion': 'Add: JOIN d_labitems ON labevents.itemid = d_labitems.itemid'
            })
        
        if 'procedures_icd' in query_lower and 'd_icd_procedures' not in query_lower and ('title' in query_lower or 'name' in query_lower):
            issues.append({
                'type': 'missing_join',
                'message': 'Query references procedure names but missing d_icd_procedures join',
                'suggestion': 'Add: JOIN d_icd_procedures ON procedures_icd.icd_code = d_icd_procedures.icd_code'
            })
        
        validation['issues'] = issues
        validation['is_valid'] = len(issues) == 0
        
        if issues:
            validation['suggestions'] = [issue['suggestion'] for issue in issues]
        
        return json.dumps(validation, indent=2)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "query_validator",
                "description": "Validate SQL queries before execution and suggest corrections for common MIMIC-IV schema mistakes.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sql_query": {
                            "type": "string",
                            "description": "The SQL query to validate for common schema mistakes"
                        }
                    },
                    "required": ["sql_query"]
                }
            }
        } 