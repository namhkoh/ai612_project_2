import re
import json
from typing import Dict, List, Any, Optional
from sqlalchemy import text
from sqlalchemy.engine import Engine
from pydantic import BaseModel, Field

class QueryOptimizer(BaseModel):
    """
    A tool to quickly fix common SQL query issues and prevent infinite retry loops.
    Provides immediate solutions for ambiguous columns, missing columns, and other common errors.
    """
    engine: Engine = Field(..., description="The engine to access database schema.")

    class Config:
        arbitrary_types_allowed = True

    def invoke(self, failed_query: str, error_message: str) -> str:
        """
        Quickly fix a failed SQL query based on the error message.
        
        Args:
            failed_query: The SQL query that failed
            error_message: The error message from the database
            
        Returns:
            JSON string with quick fix suggestions
        """
        fix_result = {
            'original_query': failed_query,
            'error_type': self._classify_error(error_message),
            'quick_fixes': [],
            'corrected_query': None,
            'explanation': ''
        }
        
        error_lower = error_message.lower()
        query_lower = failed_query.lower()
        
        # Handle ambiguous column names
        if 'ambiguous column name' in error_lower:
            fix_result.update(self._fix_ambiguous_column(failed_query, error_message))
        
        # Handle missing columns
        elif 'no such column' in error_lower:
            fix_result.update(self._fix_missing_column(failed_query, error_message))
        
        # Handle missing tables
        elif 'no such table' in error_lower:
            fix_result.update(self._fix_missing_table(failed_query, error_message))
        
        # Handle syntax errors
        elif 'syntax error' in error_lower:
            fix_result.update(self._fix_syntax_error(failed_query, error_message))
        
        # Handle foreign key constraint errors
        elif 'foreign key constraint' in error_lower:
            fix_result.update(self._fix_foreign_key_error(failed_query, error_message))
        
        # Generic fixes for other errors
        else:
            fix_result.update(self._generic_fixes(failed_query, error_message))
        
        return json.dumps(fix_result, indent=2)

    def _classify_error(self, error_message: str) -> str:
        """Classify the type of error."""
        error_lower = error_message.lower()
        
        if 'ambiguous column name' in error_lower:
            return 'ambiguous_column'
        elif 'no such column' in error_lower:
            return 'missing_column'
        elif 'no such table' in error_lower:
            return 'missing_table'
        elif 'syntax error' in error_lower:
            return 'syntax_error'
        elif 'foreign key constraint' in error_lower:
            return 'foreign_key_error'
        else:
            return 'other'

    def _fix_ambiguous_column(self, query: str, error_message: str) -> Dict[str, Any]:
        """Fix ambiguous column name errors."""
        # Extract the ambiguous column name from error message
        match = re.search(r'ambiguous column name: (\w+)', error_message.lower())
        if not match:
            return {'quick_fixes': ['Add table prefixes to all column names']}
        
        ambiguous_col = match.group(1)
        
        # Common ambiguous columns and their likely table prefixes
        common_fixes = {
            'starttime': {
                'prescriptions.starttime': 'for medication start times',
                'inputevents.starttime': 'for input event times',
                'admissions.admittime': 'for admission times (note: different column name)'
            },
            'subject_id': {
                'patients.subject_id': 'for patient identifiers',
                'admissions.subject_id': 'for admission patient links',
                'labevents.subject_id': 'for lab event patient links'
            },
            'hadm_id': {
                'admissions.hadm_id': 'for admission identifiers',
                'labevents.hadm_id': 'for lab event admission links',
                'prescriptions.hadm_id': 'for prescription admission links'
            }
        }
        
        fixes = []
        corrected_query = query
        
        if ambiguous_col in common_fixes:
            for prefixed_col, description in common_fixes[ambiguous_col].items():
                fixes.append(f"Use {prefixed_col} {description}")
            
            # Try to auto-correct the query
            # Simple heuristic: if it's a time-related query, prefer the most common time column
            if 'starttime' in ambiguous_col.lower():
                if 'prescription' in query.lower() or 'drug' in query.lower():
                    corrected_query = re.sub(r'\bstarttime\b', 'prescriptions.starttime', query, flags=re.IGNORECASE)
                elif 'input' in query.lower():
                    corrected_query = re.sub(r'\bstarttime\b', 'inputevents.starttime', query, flags=re.IGNORECASE)
        else:
            fixes.append(f"Add table prefix to '{ambiguous_col}' column (e.g., table_name.{ambiguous_col})")
        
        return {
            'quick_fixes': fixes,
            'corrected_query': corrected_query if corrected_query != query else None,
            'explanation': f"Column '{ambiguous_col}' exists in multiple tables. Add table prefixes to disambiguate."
        }

    def _fix_missing_column(self, query: str, error_message: str) -> Dict[str, Any]:
        """Fix missing column errors."""
        # Extract the missing column name
        match = re.search(r'no such column: ([\w.]+)', error_message.lower())
        if not match:
            return {'quick_fixes': ['Check column name spelling and table schema']}
        
        missing_col = match.group(1)
        
        # Common column name mistakes and their corrections
        column_corrections = {
            'labevents.label': 'd_labitems.label (join: labevents.itemid = d_labitems.itemid)',
            'procedures_icd.long_title': 'd_icd_procedures.long_title (join: procedures_icd.icd_code = d_icd_procedures.icd_code)',
            'chartevents.label': 'd_items.label (join: chartevents.itemid = d_items.itemid)',
            'diagnoses_icd.long_title': 'd_icd_diagnoses.long_title (join: diagnoses_icd.icd_code = d_icd_diagnoses.icd_code)',
            'admission_time': 'admissions.admittime',
            'discharge_time': 'admissions.dischtime',
            'inputevents.eventtime': 'inputevents.starttime',
            'procedure_id': 'procedures_icd.icd_code',
            'diagnosis_id': 'diagnoses_icd.icd_code'
        }
        
        fixes = []
        corrected_query = query
        
        if missing_col in column_corrections:
            correction = column_corrections[missing_col]
            fixes.append(f"Replace '{missing_col}' with {correction}")
            
            # Auto-correct simple cases
            if ' (join:' not in correction:  # Simple column rename
                new_col = correction
                corrected_query = query.replace(missing_col, new_col)
        else:
            fixes.append(f"Column '{missing_col}' does not exist. Check table schema or use correct column name.")
        
        return {
            'quick_fixes': fixes,
            'corrected_query': corrected_query if corrected_query != query else None,
            'explanation': f"Column '{missing_col}' does not exist in the specified table."
        }

    def _fix_missing_table(self, query: str, error_message: str) -> Dict[str, Any]:
        """Fix missing table errors."""
        match = re.search(r'no such table: (\w+)', error_message.lower())
        if not match:
            return {'quick_fixes': ['Check table name spelling']}
        
        missing_table = match.group(1)
        
        # Common table name mistakes
        table_corrections = {
            'procedures': 'procedures_icd',
            'diagnoses': 'diagnoses_icd',
            'labs': 'labevents',
            'medications': 'prescriptions',
            'vitals': 'chartevents'
        }
        
        fixes = []
        corrected_query = query
        
        if missing_table in table_corrections:
            correct_table = table_corrections[missing_table]
            fixes.append(f"Replace '{missing_table}' with '{correct_table}'")
            corrected_query = re.sub(rf'\b{missing_table}\b', correct_table, query, flags=re.IGNORECASE)
        else:
            fixes.append(f"Table '{missing_table}' does not exist. Check available tables.")
        
        return {
            'quick_fixes': fixes,
            'corrected_query': corrected_query if corrected_query != query else None,
            'explanation': f"Table '{missing_table}' does not exist in the database."
        }

    def _fix_syntax_error(self, query: str, error_message: str) -> Dict[str, Any]:
        """Fix common SQL syntax errors."""
        fixes = []
        corrected_query = query
        
        # Common syntax fixes
        if 'near "' in error_message.lower():
            fixes.append("Check for missing commas, parentheses, or quotes")
            fixes.append("Verify SQL keyword spelling and order")
        
        # Fix common syntax issues
        if query.count('(') != query.count(')'):
            fixes.append("Unmatched parentheses - check opening and closing parentheses")
        
        if query.count("'") % 2 != 0:
            fixes.append("Unmatched quotes - check string literals")
        
        return {
            'quick_fixes': fixes,
            'corrected_query': None,  # Syntax errors are harder to auto-fix
            'explanation': "SQL syntax error detected. Check query structure."
        }

    def _fix_foreign_key_error(self, query: str, error_message: str) -> Dict[str, Any]:
        """Fix foreign key constraint errors."""
        return {
            'quick_fixes': [
                "Check that referenced IDs exist in the parent table",
                "Verify join conditions are correct",
                "Use LEFT JOIN if some records may not have matches"
            ],
            'explanation': "Foreign key constraint violation. Referenced record may not exist."
        }

    def _generic_fixes(self, query: str, error_message: str) -> Dict[str, Any]:
        """Provide generic fixes for other errors."""
        return {
            'quick_fixes': [
                "Check table and column names for typos",
                "Verify data types in WHERE conditions",
                "Ensure proper JOIN syntax",
                "Check for NULL values in comparisons"
            ],
            'explanation': "General database error. Review query structure and data."
        }

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "query_optimizer",
                "description": "Quickly fix failed SQL queries and prevent infinite retry loops. Provides immediate solutions for ambiguous columns, missing columns, and other common database errors.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "failed_query": {
                            "type": "string",
                            "description": "The SQL query that failed to execute"
                        },
                        "error_message": {
                            "type": "string",
                            "description": "The error message returned by the database"
                        }
                    },
                    "required": ["failed_query", "error_message"]
                }
            }
        }


class ExecutionHelper(BaseModel):
    """
    A tool to suggest efficient query execution strategies and prevent common pitfalls.
    """
    engine: Engine = Field(..., description="The engine to access database schema.")

    class Config:
        arbitrary_types_allowed = True

    def invoke(self, query_goal: str) -> str:
        """
        Suggest efficient execution strategies for a query goal.
        
        Args:
            query_goal: Description of what the query should accomplish
            
        Returns:
            JSON string with execution strategies
        """
        strategies = {
            'recommended_approach': '',
            'efficiency_tips': [],
            'common_pitfalls': [],
            'example_pattern': ''
        }
        
        goal_lower = query_goal.lower()
        
        # Analyze goal and provide specific strategies
        if any(word in goal_lower for word in ['recent', 'latest', 'last']):
            strategies.update(self._get_recent_data_strategy())
        
        if any(word in goal_lower for word in ['count', 'number', 'how many']):
            strategies.update(self._get_counting_strategy())
        
        if any(word in goal_lower for word in ['join', 'link', 'combine']):
            strategies.update(self._get_joining_strategy())
        
        if any(word in goal_lower for word in ['group', 'aggregate', 'sum', 'average']):
            strategies.update(self._get_aggregation_strategy())
        
        # Add general efficiency tips
        strategies['general_tips'] = [
            'Use LIMIT to restrict result size for testing',
            'Add WHERE clauses early to filter data',
            'Use indexes on commonly queried columns',
            'Avoid SELECT * in production queries'
        ]
        
        return json.dumps(strategies, indent=2)

    def _get_recent_data_strategy(self) -> Dict[str, Any]:
        """Strategy for getting recent data."""
        return {
            'recommended_approach': 'Use ORDER BY with time column DESC and LIMIT',
            'efficiency_tips': [
                'Order by the most specific time column (charttime, starttime, admittime)',
                'Use LIMIT to get only the number of records needed',
                'Consider using date ranges instead of ordering large datasets'
            ],
            'common_pitfalls': [
                'Forgetting LIMIT can return huge datasets',
                'Using wrong time column for the data type',
                'Not handling NULL time values'
            ],
            'example_pattern': 'SELECT * FROM table ORDER BY charttime DESC LIMIT 10'
        }

    def _get_counting_strategy(self) -> Dict[str, Any]:
        """Strategy for counting records."""
        return {
            'recommended_approach': 'Use COUNT() with appropriate WHERE conditions',
            'efficiency_tips': [
                'Use COUNT(*) for total records',
                'Use COUNT(column) to exclude NULLs',
                'Add WHERE clauses to filter before counting'
            ],
            'common_pitfalls': [
                'Counting without filtering can be slow on large tables',
                'Not accounting for NULL values',
                'Forgetting to group when counting categories'
            ],
            'example_pattern': 'SELECT COUNT(*) FROM table WHERE condition'
        }

    def _get_joining_strategy(self) -> Dict[str, Any]:
        """Strategy for joining tables."""
        return {
            'recommended_approach': 'Use appropriate JOIN types with clear ON conditions',
            'efficiency_tips': [
                'Use INNER JOIN when you need matching records only',
                'Use LEFT JOIN when you want all records from the left table',
                'Join on indexed columns when possible (subject_id, hadm_id)'
            ],
            'common_pitfalls': [
                'Cartesian products from missing JOIN conditions',
                'Using wrong JOIN type for the use case',
                'Ambiguous column names in multi-table joins'
            ],
            'example_pattern': 'SELECT * FROM table1 t1 JOIN table2 t2 ON t1.id = t2.id'
        }

    def _get_aggregation_strategy(self) -> Dict[str, Any]:
        """Strategy for aggregating data."""
        return {
            'recommended_approach': 'Use GROUP BY with aggregate functions',
            'efficiency_tips': [
                'Group by the least granular level needed',
                'Use HAVING for filtering aggregated results',
                'Consider using window functions for complex aggregations'
            ],
            'common_pitfalls': [
                'Selecting non-grouped columns without aggregation',
                'Using WHERE instead of HAVING for aggregate conditions',
                'Grouping by too many columns unnecessarily'
            ],
            'example_pattern': 'SELECT column, COUNT(*) FROM table GROUP BY column HAVING COUNT(*) > 1'
        }

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "execution_helper",
                "description": "Suggest efficient query execution strategies and prevent common pitfalls. Helps plan the best approach before writing complex queries.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query_goal": {
                            "type": "string",
                            "description": "Description of what the query should accomplish (e.g., 'find recent lab results', 'count patients by diagnosis')"
                        }
                    },
                    "required": ["query_goal"]
                }
            }
        }

    def _analyze_query_errors(self, query: str, error_message: str) -> Dict[str, Any]:
        """Enhanced analysis of query errors with sophisticated pattern matching."""
        error_lower = error_message.lower()
        query_lower = query.lower()
        
        # Enhanced error pattern matching with confidence scoring
        error_patterns = {
            # CRITICAL: Ambiguous column errors (high frequency)
            'ambiguous_column': {
                'patterns': ['ambiguous column name', 'ambiguous column'],
                'confidence': 0.95,
                'category': 'column_ambiguity',
                'priority': 'HIGH'
            },
            
            # CRITICAL: Missing column errors (high frequency)
            'missing_column': {
                'patterns': ['no such column', 'has no column named', 'unknown column'],
                'confidence': 0.95,
                'category': 'missing_column',
                'priority': 'HIGH'
            },
            
            # CRITICAL: Missing table errors (high frequency)
            'missing_table': {
                'patterns': ['no such table', 'table or view does not exist', 'unknown table'],
                'confidence': 0.95,
                'category': 'missing_table',
                'priority': 'HIGH'
            },
            
            # CRITICAL: Join errors (medium frequency, high impact)
            'join_error': {
                'patterns': ['cannot join', 'join condition', 'foreign key constraint'],
                'confidence': 0.85,
                'category': 'join_issue',
                'priority': 'HIGH'
            },
            
            # CRITICAL: SQLite syntax errors (medium frequency)
            'sqlite_syntax': {
                'patterns': ['extract', 'date_part', 'interval', 'postgresql', 'mysql'],
                'confidence': 0.90,
                'category': 'syntax_incompatibility',
                'priority': 'MEDIUM'
            },
            
            # Data type errors
            'data_type': {
                'patterns': ['type mismatch', 'cannot convert', 'invalid type'],
                'confidence': 0.80,
                'category': 'data_type',
                'priority': 'MEDIUM'
            },
            
            # Performance issues
            'performance': {
                'patterns': ['timeout', 'too many rows', 'memory'],
                'confidence': 0.75,
                'category': 'performance',
                'priority': 'LOW'
            }
        }
        
        detected_errors = []
        for error_type, config in error_patterns.items():
            for pattern in config['patterns']:
                if pattern in error_lower:
                    detected_errors.append({
                        'type': error_type,
                        'confidence': config['confidence'],
                        'category': config['category'],
                        'priority': config['priority'],
                        'pattern_matched': pattern
                    })
                    break
        
        # Enhanced specific error analysis
        specific_analysis = self._get_specific_error_analysis(query, error_message)
        
        return {
            'detected_errors': detected_errors,
            'specific_analysis': specific_analysis,
            'query_complexity': self._assess_query_complexity(query),
            'recommended_fixes': self._generate_enhanced_fixes(query, error_message, detected_errors)
        }

    def _get_specific_error_analysis(self, query: str, error_message: str) -> Dict[str, Any]:
        """Enhanced specific error analysis with detailed recommendations."""
        analysis = {
            'ambiguous_columns': [],
            'missing_columns': [],
            'missing_tables': [],
            'join_issues': [],
            'syntax_issues': []
        }
        
        # Enhanced ambiguous column detection
        if 'ambiguous column' in error_message.lower():
            # Extract column name from error message
            import re
            column_match = re.search(r'ambiguous column name:?\s*(["\']?)(\w+)\1', error_message, re.IGNORECASE)
            if column_match:
                column_name = column_match.group(2)
                analysis['ambiguous_columns'].append({
                    'column': column_name,
                    'suggested_fixes': self._get_column_disambiguation_fixes(column_name, query),
                    'confidence': 0.95
                })
        
        # Enhanced missing column detection
        if any(phrase in error_message.lower() for phrase in ['no such column', 'has no column named']):
            column_match = re.search(r'(?:no such column|has no column named):?\s*(["\']?)(\w+\.?\w*)\1', error_message, re.IGNORECASE)
            if column_match:
                column_ref = column_match.group(2)
                analysis['missing_columns'].append({
                    'column_reference': column_ref,
                    'suggested_fixes': self._get_missing_column_fixes(column_ref, query),
                    'confidence': 0.95
                })
        
        # Enhanced missing table detection
        if 'no such table' in error_message.lower():
            table_match = re.search(r'no such table:?\s*(["\']?)(\w+)\1', error_message, re.IGNORECASE)
            if table_match:
                table_name = table_match.group(2)
                analysis['missing_tables'].append({
                    'table': table_name,
                    'suggested_fixes': self._get_missing_table_fixes(table_name, query),
                    'confidence': 0.95
                })
        
        # Enhanced SQLite syntax issue detection
        sqlite_incompatible = ['extract', 'date_part', 'interval', 'postgresql', 'mysql']
        for term in sqlite_incompatible:
            if term in query.lower():
                analysis['syntax_issues'].append({
                    'incompatible_syntax': term,
                    'sqlite_alternative': self._get_sqlite_alternative(term),
                    'confidence': 0.90
                })
        
        return analysis

    def _get_column_disambiguation_fixes(self, column_name: str, query: str) -> List[Dict[str, Any]]:
        """Enhanced column disambiguation fixes with table-specific guidance."""
        fixes = []
        
        # Common ambiguous columns in MIMIC-IV with their proper table prefixes
        column_mappings = {
            'starttime': [
                {'table': 'prescriptions', 'context': 'medication start time'},
                {'table': 'inputevents', 'context': 'input start time'},
                {'table': 'outputevents', 'context': 'output start time'}
            ],
            'endtime': [
                {'table': 'prescriptions', 'context': 'medication end time'},
                {'table': 'inputevents', 'context': 'input end time'},
                {'table': 'outputevents', 'context': 'output end time'}
            ],
            'charttime': [
                {'table': 'labevents', 'context': 'lab measurement time'},
                {'table': 'chartevents', 'context': 'vital sign time'},
                {'table': 'procedures_icd', 'context': 'procedure time'}
            ],
            'subject_id': [
                {'table': 'patients', 'context': 'patient demographics'},
                {'table': 'admissions', 'context': 'admission records'},
                {'table': 'labevents', 'context': 'lab events'},
                {'table': 'prescriptions', 'context': 'medications'}
            ],
            'hadm_id': [
                {'table': 'admissions', 'context': 'admission records'},
                {'table': 'labevents', 'context': 'lab events'},
                {'table': 'prescriptions', 'context': 'medications'},
                {'table': 'diagnoses_icd', 'context': 'diagnoses'}
            ]
        }
        
        if column_name.lower() in column_mappings:
            for mapping in column_mappings[column_name.lower()]:
                fixes.append({
                    'fix_type': 'table_prefix',
                    'original': column_name,
                    'suggested': f"{mapping['table']}.{column_name}",
                    'context': mapping['context'],
                    'confidence': 0.95,
                    'explanation': f"Use {mapping['table']}.{column_name} for {mapping['context']}"
                })
        else:
            # Generic fix for unknown columns
            fixes.append({
                'fix_type': 'table_prefix_generic',
                'original': column_name,
                'suggested': f"table_name.{column_name}",
                'confidence': 0.70,
                'explanation': f"Add table prefix to disambiguate {column_name}"
            })
        
        return fixes

    def _get_missing_column_fixes(self, column_ref: str, query: str) -> List[Dict[str, Any]]:
        """Enhanced missing column fixes with common mistake corrections."""
        fixes = []
        
        # Common column name mistakes in MIMIC-IV
        column_corrections = {
            # Lab events common mistakes
            'labevents.label': {
                'correct': 'd_labitems.label',
                'explanation': 'Lab names are in d_labitems table, not labevents',
                'required_join': 'labevents.itemid = d_labitems.itemid',
                'confidence': 0.98
            },
            'labevents.name': {
                'correct': 'd_labitems.label',
                'explanation': 'Lab names are in d_labitems.label',
                'required_join': 'labevents.itemid = d_labitems.itemid',
                'confidence': 0.95
            },
            
            # Chart events common mistakes
            'chartevents.label': {
                'correct': 'd_items.label',
                'explanation': 'Chart item names are in d_items table, not chartevents',
                'required_join': 'chartevents.itemid = d_items.itemid',
                'confidence': 0.98
            },
            'chartevents.name': {
                'correct': 'd_items.label',
                'explanation': 'Chart item names are in d_items.label',
                'required_join': 'chartevents.itemid = d_items.itemid',
                'confidence': 0.95
            },
            
            # Procedures common mistakes
            'procedures_icd.long_title': {
                'correct': 'd_icd_procedures.long_title',
                'explanation': 'Procedure names are in d_icd_procedures table',
                'required_join': 'procedures_icd.icd_code = d_icd_procedures.icd_code',
                'confidence': 0.98
            },
            'procedures_icd.title': {
                'correct': 'd_icd_procedures.long_title',
                'explanation': 'Procedure names are in d_icd_procedures.long_title',
                'required_join': 'procedures_icd.icd_code = d_icd_procedures.icd_code',
                'confidence': 0.95
            },
            
            # Diagnoses common mistakes
            'diagnoses_icd.long_title': {
                'correct': 'd_icd_diagnoses.long_title',
                'explanation': 'Diagnosis names are in d_icd_diagnoses table',
                'required_join': 'diagnoses_icd.icd_code = d_icd_diagnoses.icd_code',
                'confidence': 0.98
            },
            'diagnoses_icd.title': {
                'correct': 'd_icd_diagnoses.long_title',
                'explanation': 'Diagnosis names are in d_icd_diagnoses.long_title',
                'required_join': 'diagnoses_icd.icd_code = d_icd_diagnoses.icd_code',
                'confidence': 0.95
            },
            
            # Time column mistakes
            'admission_time': {
                'correct': 'admissions.admittime',
                'explanation': 'Admission time column is named admittime',
                'confidence': 0.95
            },
            'discharge_time': {
                'correct': 'admissions.dischtime',
                'explanation': 'Discharge time column is named dischtime',
                'confidence': 0.95
            }
        }
        
        column_lower = column_ref.lower()
        for mistake, correction in column_corrections.items():
            if mistake.lower() == column_lower:
                fix = {
                    'fix_type': 'column_correction',
                    'original': column_ref,
                    'suggested': correction['correct'],
                    'explanation': correction['explanation'],
                    'confidence': correction['confidence']
                }
                if 'required_join' in correction:
                    fix['required_join'] = correction['required_join']
                fixes.append(fix)
                break
        
        # If no specific correction found, suggest general alternatives
        if not fixes:
            fixes.append({
                'fix_type': 'column_search',
                'original': column_ref,
                'suggested': 'Check table schema for correct column name',
                'confidence': 0.60,
                'explanation': f"Column {column_ref} not found - verify correct table and column name"
            })
        
        return fixes

    def _get_missing_table_fixes(self, table_name: str, query: str) -> List[Dict[str, Any]]:
        """Enhanced missing table fixes with common table name corrections."""
        fixes = []
        
        # Common table name mistakes and corrections
        table_corrections = {
            'lab_events': 'labevents',
            'chart_events': 'chartevents',
            'input_events': 'inputevents',
            'output_events': 'outputevents',
            'microbiology_events': 'microbiologyevents',
            'note_events': 'noteevents',
            'icu_stays': 'icustays',
            'procedures': 'procedures_icd',
            'diagnoses': 'diagnoses_icd',
            'lab_items': 'd_labitems',
            'chart_items': 'd_items',
            'icd_procedures': 'd_icd_procedures',
            'icd_diagnoses': 'd_icd_diagnoses'
        }
        
        table_lower = table_name.lower()
        if table_lower in table_corrections:
            fixes.append({
                'fix_type': 'table_correction',
                'original': table_name,
                'suggested': table_corrections[table_lower],
                'confidence': 0.95,
                'explanation': f"Table name should be {table_corrections[table_lower]} not {table_name}"
            })
        else:
            # Fuzzy matching for similar table names
            from difflib import get_close_matches
            available_tables = [
                'patients', 'admissions', 'labevents', 'chartevents', 'inputevents',
                'outputevents', 'prescriptions', 'procedures_icd', 'diagnoses_icd',
                'microbiologyevents', 'noteevents', 'icustays', 'transfers', 'services',
                'd_labitems', 'd_items', 'd_icd_procedures', 'd_icd_diagnoses'
            ]
            
            close_matches = get_close_matches(table_lower, available_tables, n=3, cutoff=0.6)
            for match in close_matches:
                fixes.append({
                    'fix_type': 'table_suggestion',
                    'original': table_name,
                    'suggested': match,
                    'confidence': 0.80,
                    'explanation': f"Did you mean {match}? (similar to {table_name})"
                })
        
        return fixes

    def _get_sqlite_alternative(self, incompatible_syntax: str) -> Dict[str, Any]:
        """Enhanced SQLite alternatives for incompatible syntax."""
        alternatives = {
            'extract': {
                'sqlite_function': 'strftime',
                'example': "EXTRACT(YEAR FROM date_col) → strftime('%Y', date_col)",
                'common_patterns': {
                    'EXTRACT(YEAR FROM': "strftime('%Y', ",
                    'EXTRACT(MONTH FROM': "strftime('%m', ",
                    'EXTRACT(DAY FROM': "strftime('%d', ",
                    'EXTRACT(HOUR FROM': "strftime('%H', ",
                    'EXTRACT(MINUTE FROM': "strftime('%M', "
                }
            },
            'date_part': {
                'sqlite_function': 'strftime',
                'example': "DATE_PART('year', date_col) → strftime('%Y', date_col)",
                'common_patterns': {
                    "DATE_PART('year'": "strftime('%Y'",
                    "DATE_PART('month'": "strftime('%m'",
                    "DATE_PART('day'": "strftime('%d'"
                }
            },
            'interval': {
                'sqlite_function': 'datetime/date functions',
                'example': "date_col + INTERVAL '1 day' → datetime(date_col, '+1 day')",
                'common_patterns': {
                    "+ INTERVAL '1 day'": ", '+1 day')",
                    "- INTERVAL '1 day'": ", '-1 day')",
                    "+ INTERVAL '1 hour'": ", '+1 hour')"
                }
            }
        }
        
        return alternatives.get(incompatible_syntax.lower(), {
            'sqlite_function': 'unknown',
            'example': f"No direct SQLite alternative known for {incompatible_syntax}",
            'common_patterns': {}
        })

    def _generate_enhanced_fixes(self, query: str, error_message: str, detected_errors: List[Dict]) -> List[Dict[str, Any]]:
        """Generate enhanced, prioritized fix suggestions."""
        fixes = []
        
        # Sort detected errors by priority and confidence
        sorted_errors = sorted(detected_errors, 
                             key=lambda x: (x['priority'] == 'HIGH', x['confidence']), 
                             reverse=True)
        
        for error in sorted_errors:
            if error['type'] == 'ambiguous_column':
                fixes.extend(self._generate_ambiguous_column_fixes(query, error_message))
            elif error['type'] == 'missing_column':
                fixes.extend(self._generate_missing_column_fixes(query, error_message))
            elif error['type'] == 'missing_table':
                fixes.extend(self._generate_missing_table_fixes(query, error_message))
            elif error['type'] == 'sqlite_syntax':
                fixes.extend(self._generate_sqlite_syntax_fixes(query, error_message))
        
        # Add general optimization suggestions
        fixes.extend(self._generate_general_optimization_fixes(query))
        
        return fixes[:10]  # Limit to top 10 most relevant fixes

    def _generate_ambiguous_column_fixes(self, query: str, error_message: str) -> List[Dict[str, Any]]:
        """Generate specific fixes for ambiguous column errors."""
        fixes = []
        
        # Extract column name from error
        import re
        column_match = re.search(r'ambiguous column name:?\s*(["\']?)(\w+)\1', error_message, re.IGNORECASE)
        if column_match:
            column_name = column_match.group(2)
            
            # Generate table-specific fixes
            table_suggestions = self._get_column_disambiguation_fixes(column_name, query)
            for suggestion in table_suggestions:
                fixes.append({
                    'type': 'ambiguous_column_fix',
                    'priority': 'HIGH',
                    'confidence': suggestion['confidence'],
                    'description': f"Replace '{column_name}' with '{suggestion['suggested']}'",
                    'fix_action': f"Add table prefix: {suggestion['suggested']}",
                    'explanation': suggestion['explanation']
                })
        
        return fixes

    def _generate_missing_column_fixes(self, query: str, error_message: str) -> List[Dict[str, Any]]:
        """Generate specific fixes for missing column errors."""
        fixes = []
        
        # Extract column reference from error
        import re
        column_match = re.search(r'(?:no such column|has no column named):?\s*(["\']?)(\w+\.?\w*)\1', error_message, re.IGNORECASE)
        if column_match:
            column_ref = column_match.group(2)
            
            # Generate correction fixes
            correction_suggestions = self._get_missing_column_fixes(column_ref, query)
            for suggestion in correction_suggestions:
                fixes.append({
                    'type': 'missing_column_fix',
                    'priority': 'HIGH',
                    'confidence': suggestion['confidence'],
                    'description': f"Replace '{column_ref}' with '{suggestion['suggested']}'",
                    'fix_action': f"Correct column reference: {suggestion['suggested']}",
                    'explanation': suggestion['explanation']
                })
                
                # Add join requirement if needed
                if 'required_join' in suggestion:
                    fixes.append({
                        'type': 'required_join',
                        'priority': 'HIGH',
                        'confidence': 0.95,
                        'description': f"Add required join: {suggestion['required_join']}",
                        'fix_action': f"JOIN required: {suggestion['required_join']}",
                        'explanation': 'This join is required to access the corrected column'
                    })
        
        return fixes

    def _generate_missing_table_fixes(self, query: str, error_message: str) -> List[Dict[str, Any]]:
        """Generate specific fixes for missing table errors."""
        fixes = []
        
        # Extract table name from error
        import re
        table_match = re.search(r'no such table:?\s*(["\']?)(\w+)\1', error_message, re.IGNORECASE)
        if table_match:
            table_name = table_match.group(2)
            
            # Generate table correction fixes
            table_suggestions = self._get_missing_table_fixes(table_name, query)
            for suggestion in table_suggestions:
                fixes.append({
                    'type': 'missing_table_fix',
                    'priority': 'HIGH',
                    'confidence': suggestion['confidence'],
                    'description': f"Replace table '{table_name}' with '{suggestion['suggested']}'",
                    'fix_action': f"Correct table name: {suggestion['suggested']}",
                    'explanation': suggestion['explanation']
                })
        
        return fixes

    def _generate_sqlite_syntax_fixes(self, query: str, error_message: str) -> List[Dict[str, Any]]:
        """Generate specific fixes for SQLite syntax incompatibilities."""
        fixes = []
        
        # Check for common SQLite incompatibilities
        incompatible_terms = ['extract', 'date_part', 'interval']
        for term in incompatible_terms:
            if term.upper() in query.upper():
                alternative = self._get_sqlite_alternative(term)
                fixes.append({
                    'type': 'sqlite_syntax_fix',
                    'priority': 'MEDIUM',
                    'confidence': 0.90,
                    'description': f"Replace {term.upper()} with SQLite-compatible syntax",
                    'fix_action': f"Use {alternative['sqlite_function']} instead of {term.upper()}",
                    'explanation': alternative['example']
                })
        
        return fixes

    def _generate_general_optimization_fixes(self, query: str) -> List[Dict[str, Any]]:
        """Generate general query optimization suggestions."""
        fixes = []
        
        # Check for missing WHERE clauses
        if 'WHERE' not in query.upper():
            fixes.append({
                'type': 'optimization',
                'priority': 'LOW',
                'confidence': 0.70,
                'description': 'Consider adding WHERE clause to limit results',
                'fix_action': 'Add WHERE clause with appropriate filters',
                'explanation': 'WHERE clauses improve performance and result relevance'
            })
        
        # Check for missing LIMIT
        if 'LIMIT' not in query.upper() and 'COUNT' not in query.upper():
            fixes.append({
                'type': 'optimization',
                'priority': 'LOW',
                'confidence': 0.60,
                'description': 'Consider adding LIMIT to prevent large result sets',
                'fix_action': 'Add LIMIT clause (e.g., LIMIT 100)',
                'explanation': 'LIMIT clauses prevent overwhelming result sets'
            })
        
        return fixes 