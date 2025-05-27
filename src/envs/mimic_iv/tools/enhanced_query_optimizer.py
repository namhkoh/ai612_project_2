import re
import json
from typing import Dict, List, Any, Optional
from sqlalchemy import text
from sqlalchemy.engine import Engine
from pydantic import BaseModel, Field

class EnhancedQueryOptimizer(BaseModel):
    """
    Enhanced query optimizer that combines basic and advanced error handling.
    Provides comprehensive query fixing, optimization, and error recovery.
    """
    engine: Engine = Field(..., description="The engine to access database schema.")

    class Config:
        arbitrary_types_allowed = True

    def invoke(self, failed_query: str, error_message: str, context: str = "") -> str:
        """
        Comprehensive query optimization and error fixing.
        
        Args:
            failed_query: The SQL query that failed
            error_message: The error message from the database
            context: Additional context about what the query is trying to achieve
            
        Returns:
            JSON string with comprehensive fix suggestions and auto-corrected queries
        """
        fix_result = {
            'original_query': failed_query,
            'error_analysis': self._analyze_error_comprehensively(error_message, failed_query),
            'quick_fixes': [],
            'advanced_fixes': [],
            'auto_corrected_query': None,
            'confidence_score': 0.0,
            'explanation': '',
            'alternative_approaches': []
        }
        
        error_lower = error_message.lower()
        query_lower = failed_query.lower()
        
        # Handle SQLite-specific syntax issues (Advanced)
        if self._is_sqlite_syntax_issue(error_message, failed_query):
            fix_result.update(self._fix_sqlite_syntax_comprehensive(failed_query, error_message))
        
        # Handle ambiguous column names (Basic + Advanced)
        elif 'ambiguous column name' in error_lower:
            fix_result.update(self._fix_ambiguous_column_enhanced(failed_query, error_message))
        
        # Handle missing columns (Basic + Advanced)
        elif 'no such column' in error_lower:
            fix_result.update(self._fix_missing_column_enhanced(failed_query, error_message))
        
        # Handle missing tables (Basic + Advanced)
        elif 'no such table' in error_lower:
            fix_result.update(self._fix_missing_table_enhanced(failed_query, error_message))
        
        # Handle syntax errors (Basic + Advanced)
        elif 'syntax error' in error_lower:
            fix_result.update(self._fix_syntax_error_enhanced(failed_query, error_message))
        
        # Handle foreign key constraint errors
        elif 'foreign key constraint' in error_lower:
            fix_result.update(self._fix_foreign_key_error(failed_query, error_message))
        
        # Generic fixes for other errors
        else:
            fix_result.update(self._generic_fixes_enhanced(failed_query, error_message))
        
        return json.dumps(fix_result, indent=2)

    def _analyze_error_comprehensively(self, error_message: str, query: str) -> Dict[str, Any]:
        """Perform comprehensive error analysis."""
        analysis = {
            'error_category': self._classify_error(error_message),
            'severity': self._assess_severity(error_message, query),
            'likely_cause': self._determine_cause(error_message, query),
            'query_complexity': self._assess_query_complexity(query),
            'sqlite_specific': self._is_sqlite_specific(error_message, query)
        }
        return analysis

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
        elif 'near "from"' in error_lower:
            return 'sqlite_syntax'
        else:
            return 'other'

    def _assess_severity(self, error_message: str, query: str) -> str:
        """Assess error severity."""
        if 'near "from"' in error_message.lower() or 'extract(' in query.lower():
            return 'high'
        elif 'ambiguous' in error_message.lower() or 'no such' in error_message.lower():
            return 'medium'
        else:
            return 'low'

    def _determine_cause(self, error_message: str, query: str) -> str:
        """Determine the likely cause of the error."""
        error_lower = error_message.lower()
        
        if 'extract(' in query.lower() and 'syntax error' in error_lower:
            return 'EXTRACT function not supported in SQLite, need STRFTIME'
        elif 'procedures_icd.chartdate' in error_message:
            return 'procedures_icd table does not have chartdate column'
        elif 'icd9_code' in error_message:
            return 'Column should be icd_code, not icd9_code'
        elif 'near "from"' in error_lower:
            return 'SQLite-specific syntax issue with complex subqueries'
        else:
            return 'Standard SQL error'

    def _assess_query_complexity(self, query: str) -> str:
        """Assess the complexity of the query."""
        join_count = query.lower().count('join')
        subquery_count = query.lower().count('select') - 1
        
        if join_count >= 3 or subquery_count >= 2:
            return 'high'
        elif join_count >= 1 or subquery_count >= 1:
            return 'medium'
        else:
            return 'low'

    def _is_sqlite_specific(self, error_message: str, query: str) -> bool:
        """Check if this is a SQLite-specific issue."""
        return (
            'near "from"' in error_message.lower() or
            ('extract(' in query.lower() and 'syntax error' in error_message.lower())
        )

    def _is_sqlite_syntax_issue(self, error_message: str, query: str) -> bool:
        """Check if this is a SQLite-specific syntax issue."""
        return self._is_sqlite_specific(error_message, query)

    def _fix_sqlite_syntax_comprehensive(self, query: str, error_message: str) -> Dict[str, Any]:
        """Comprehensive SQLite syntax fixing."""
        corrected_query = query
        quick_fixes = []
        advanced_fixes = []
        
        # Fix EXTRACT function to STRFTIME
        if 'extract(' in query.lower():
            # EXTRACT(YEAR FROM column) -> STRFTIME('%Y', column)
            corrected_query = re.sub(
                r'EXTRACT\s*\(\s*YEAR\s+FROM\s+([^)]+)\)',
                r"STRFTIME('%Y', \1)",
                corrected_query,
                flags=re.IGNORECASE
            )
            # EXTRACT(MONTH FROM column) -> STRFTIME('%m', column)
            corrected_query = re.sub(
                r'EXTRACT\s*\(\s*MONTH\s+FROM\s+([^)]+)\)',
                r"STRFTIME('%m', \1)",
                corrected_query,
                flags=re.IGNORECASE
            )
            quick_fixes.append("Converted EXTRACT functions to SQLite-compatible STRFTIME")
            advanced_fixes.append("Auto-converted date functions for SQLite compatibility")
        
        # Fix other date functions
        date_function_map = {
            r'YEAR\s*\(\s*([^)]+)\)': r"STRFTIME('%Y', \1)",
            r'MONTH\s*\(\s*([^)]+)\)': r"STRFTIME('%m', \1)",
            r'DAY\s*\(\s*([^)]+)\)': r"STRFTIME('%d', \1)"
        }
        
        for pattern, replacement in date_function_map.items():
            if re.search(pattern, corrected_query, re.IGNORECASE):
                corrected_query = re.sub(pattern, replacement, corrected_query, flags=re.IGNORECASE)
                advanced_fixes.append(f"Converted date function to SQLite STRFTIME format")
        
        # Fix complex subquery syntax issues
        if 'near "from"' in error_message.lower():
            quick_fixes.append("Restructure subquery to avoid SQLite parsing issues")
            advanced_fixes.append("Consider breaking complex query into simpler parts")
            advanced_fixes.append("Use explicit table aliases and avoid nested subqueries")
        
        return {
            'quick_fixes': quick_fixes,
            'advanced_fixes': advanced_fixes,
            'auto_corrected_query': corrected_query if corrected_query != query else None,
            'confidence_score': 0.9 if corrected_query != query else 0.4,
            'explanation': 'SQLite has specific syntax requirements that differ from other SQL databases'
        }

    def _fix_ambiguous_column_enhanced(self, query: str, error_message: str) -> Dict[str, Any]:
        """Enhanced ambiguous column fixing."""
        # Extract the ambiguous column name from error message
        match = re.search(r'ambiguous column name: (\w+)', error_message.lower())
        if not match:
            return {'quick_fixes': ['Add table prefixes to all column names']}
        
        ambiguous_col = match.group(1)
        
        # Enhanced ambiguous columns mapping
        enhanced_fixes = {
            'starttime': {
                'prescriptions.starttime': 'for medication start times',
                'inputevents.starttime': 'for input event times',
                'admissions.admittime': 'for admission times (note: different column name)',
                'chartevents.charttime': 'for chart event times (note: different column name)'
            },
            'subject_id': {
                'patients.subject_id': 'for patient identifiers',
                'admissions.subject_id': 'for admission patient links',
                'labevents.subject_id': 'for lab event patient links',
                'prescriptions.subject_id': 'for prescription patient links'
            },
            'hadm_id': {
                'admissions.hadm_id': 'for admission identifiers',
                'labevents.hadm_id': 'for lab event admission links',
                'prescriptions.hadm_id': 'for prescription admission links',
                'procedures_icd.hadm_id': 'for procedure admission links'
            }
        }
        
        quick_fixes = []
        advanced_fixes = []
        corrected_query = query
        
        if ambiguous_col in enhanced_fixes:
            for prefixed_col, description in enhanced_fixes[ambiguous_col].items():
                quick_fixes.append(f"Use {prefixed_col} {description}")
            
            # Enhanced auto-correction logic
            if 'starttime' in ambiguous_col.lower():
                if 'prescription' in query.lower() or 'drug' in query.lower():
                    corrected_query = re.sub(r'\bstarttime\b', 'prescriptions.starttime', query, flags=re.IGNORECASE)
                    advanced_fixes.append("Auto-corrected to prescriptions.starttime based on context")
                elif 'input' in query.lower():
                    corrected_query = re.sub(r'\bstarttime\b', 'inputevents.starttime', query, flags=re.IGNORECASE)
                    advanced_fixes.append("Auto-corrected to inputevents.starttime based on context")
        else:
            quick_fixes.append(f"Add table prefix to '{ambiguous_col}' column (e.g., table_name.{ambiguous_col})")
            advanced_fixes.append("Use table aliases to clarify column references")
        
        return {
            'quick_fixes': quick_fixes,
            'advanced_fixes': advanced_fixes,
            'auto_corrected_query': corrected_query if corrected_query != query else None,
            'confidence_score': 0.8 if corrected_query != query else 0.6,
            'explanation': f"Column '{ambiguous_col}' exists in multiple tables. Add table prefixes to disambiguate."
        }

    def _fix_missing_column_enhanced(self, query: str, error_message: str) -> Dict[str, Any]:
        """Enhanced missing column fixing."""
        # Extract the missing column name
        match = re.search(r'no such column: ([\w.]+)', error_message.lower())
        if not match:
            return {'quick_fixes': ['Check column name spelling and table schema']}
        
        missing_col = match.group(1)
        
        # Enhanced column corrections mapping
        enhanced_column_corrections = {
            'labevents.label': {
                'correction': 'd_labitems.label',
                'join': 'labevents.itemid = d_labitems.itemid',
                'explanation': 'Lab test labels are in d_labitems table'
            },
            'procedures_icd.long_title': {
                'correction': 'd_icd_procedures.long_title',
                'join': 'procedures_icd.icd_code = d_icd_procedures.icd_code',
                'explanation': 'Procedure descriptions are in d_icd_procedures table'
            },
            'chartevents.label': {
                'correction': 'd_items.label',
                'join': 'chartevents.itemid = d_items.itemid',
                'explanation': 'Chart event labels are in d_items table'
            },
            'diagnoses_icd.long_title': {
                'correction': 'd_icd_diagnoses.long_title',
                'join': 'diagnoses_icd.icd_code = d_icd_diagnoses.icd_code',
                'explanation': 'Diagnosis descriptions are in d_icd_diagnoses table'
            },
            'procedures_icd.chartdate': {
                'correction': 'admissions.admittime',
                'join': 'procedures_icd.hadm_id = admissions.hadm_id',
                'explanation': 'procedures_icd has no date columns, use admission dates'
            },
            'admission_time': {
                'correction': 'admissions.admittime',
                'join': None,
                'explanation': 'Standard column name is admittime'
            },
            'discharge_time': {
                'correction': 'admissions.dischtime',
                'join': None,
                'explanation': 'Standard column name is dischtime'
            }
        }
        
        quick_fixes = []
        advanced_fixes = []
        corrected_query = query
        
        if missing_col in enhanced_column_corrections:
            correction_info = enhanced_column_corrections[missing_col]
            correction = correction_info['correction']
            join_info = correction_info['join']
            explanation = correction_info['explanation']
            
            if join_info:
                quick_fixes.append(f"Replace '{missing_col}' with {correction}")
                quick_fixes.append(f"Add join: {join_info}")
                advanced_fixes.append(f"Full solution: Use {correction} with join on {join_info}")
            else:
                quick_fixes.append(f"Replace '{missing_col}' with {correction}")
                corrected_query = query.replace(missing_col, correction)
                advanced_fixes.append(f"Auto-corrected column name: {explanation}")
        else:
            quick_fixes.append(f"Column '{missing_col}' does not exist. Check table schema or use correct column name.")
            advanced_fixes.append("Verify column exists in the target table")
            advanced_fixes.append("Check if column is in a related table that needs to be joined")
        
        return {
            'quick_fixes': quick_fixes,
            'advanced_fixes': advanced_fixes,
            'auto_corrected_query': corrected_query if corrected_query != query else None,
            'confidence_score': 0.8 if corrected_query != query else 0.5,
            'explanation': f"Column '{missing_col}' does not exist in the specified table."
        }

    def _fix_missing_table_enhanced(self, query: str, error_message: str) -> Dict[str, Any]:
        """Enhanced missing table fixing."""
        match = re.search(r'no such table: (\w+)', error_message.lower())
        if not match:
            return {'quick_fixes': ['Check table name spelling']}
        
        missing_table = match.group(1)
        
        # Enhanced table corrections
        enhanced_table_corrections = {
            'procedures': {
                'correction': 'procedures_icd',
                'explanation': 'Procedure data is in procedures_icd table'
            },
            'diagnoses': {
                'correction': 'diagnoses_icd',
                'explanation': 'Diagnosis data is in diagnoses_icd table'
            },
            'labs': {
                'correction': 'labevents',
                'explanation': 'Laboratory data is in labevents table'
            },
            'medications': {
                'correction': 'prescriptions',
                'explanation': 'Medication data is in prescriptions table'
            },
            'vitals': {
                'correction': 'chartevents',
                'explanation': 'Vital signs are in chartevents table'
            },
            'microbiological_tests': {
                'correction': 'microbiologyevents',
                'explanation': 'Microbiology data is in microbiologyevents table'
            }
        }
        
        quick_fixes = []
        advanced_fixes = []
        corrected_query = query
        
        if missing_table in enhanced_table_corrections:
            correction_info = enhanced_table_corrections[missing_table]
            correct_table = correction_info['correction']
            explanation = correction_info['explanation']
            
            quick_fixes.append(f"Replace '{missing_table}' with '{correct_table}'")
            corrected_query = re.sub(rf'\b{missing_table}\b', correct_table, query, flags=re.IGNORECASE)
            advanced_fixes.append(f"Auto-corrected table name: {explanation}")
        else:
            quick_fixes.append(f"Table '{missing_table}' does not exist. Check available tables.")
            advanced_fixes.append("Use sql_db_list_tables to see available tables")
        
        return {
            'quick_fixes': quick_fixes,
            'advanced_fixes': advanced_fixes,
            'auto_corrected_query': corrected_query if corrected_query != query else None,
            'confidence_score': 0.9 if corrected_query != query else 0.3,
            'explanation': f"Table '{missing_table}' does not exist in the database."
        }

    def _fix_syntax_error_enhanced(self, query: str, error_message: str) -> Dict[str, Any]:
        """Enhanced syntax error fixing."""
        quick_fixes = []
        advanced_fixes = []
        
        # Enhanced syntax analysis
        if 'near "' in error_message.lower():
            quick_fixes.append("Check for missing commas, parentheses, or quotes")
            advanced_fixes.append("Verify SQL keyword spelling and order")
            advanced_fixes.append("Check for SQLite-specific syntax requirements")
        
        # Enhanced syntax checks
        if query.count('(') != query.count(')'):
            quick_fixes.append("Unmatched parentheses - check opening and closing parentheses")
            advanced_fixes.append("Balance all parentheses in subqueries and function calls")
        
        if query.count("'") % 2 != 0:
            quick_fixes.append("Unmatched quotes - check string literals")
            advanced_fixes.append("Ensure all string literals are properly quoted")
        
        # Check for common SQLite syntax issues
        if 'limit' in query.lower() and 'offset' in query.lower():
            advanced_fixes.append("SQLite LIMIT OFFSET syntax: use LIMIT count OFFSET start")
        
        return {
            'quick_fixes': quick_fixes,
            'advanced_fixes': advanced_fixes,
            'auto_corrected_query': None,  # Syntax errors are harder to auto-fix
            'confidence_score': 0.4,
            'explanation': "SQL syntax error detected. Check query structure and SQLite compatibility."
        }

    def _fix_foreign_key_error(self, query: str, error_message: str) -> Dict[str, Any]:
        """Fix foreign key constraint errors."""
        return {
            'quick_fixes': [
                "Check that referenced IDs exist in the parent table",
                "Verify join conditions are correct",
                "Use LEFT JOIN if some records may not have matches"
            ],
            'advanced_fixes': [
                "Validate foreign key relationships in MIMIC-IV schema",
                "Consider using EXISTS subqueries for complex relationships"
            ],
            'confidence_score': 0.5,
            'explanation': "Foreign key constraint violation. Referenced record may not exist."
        }

    def _generic_fixes_enhanced(self, query: str, error_message: str) -> Dict[str, Any]:
        """Enhanced generic fixes for other errors."""
        return {
            'quick_fixes': [
                "Check table and column names for typos",
                "Verify data types in WHERE conditions",
                "Ensure proper JOIN syntax",
                "Check for NULL values in comparisons"
            ],
            'advanced_fixes': [
                "Review MIMIC-IV schema documentation",
                "Use sql_db_schema to verify table structure",
                "Consider using value_substring_search for data exploration",
                "Break complex queries into simpler parts for debugging"
            ],
            'confidence_score': 0.3,
            'explanation': "General database error. Review query structure and MIMIC-IV schema."
        }

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "enhanced_query_optimizer",
                "description": "Enhanced query optimizer that combines basic and advanced error handling. Provides comprehensive query fixing, optimization, and error recovery with high confidence auto-correction.",
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
                        },
                        "context": {
                            "type": "string",
                            "description": "Additional context about what the query is trying to achieve (optional)"
                        }
                    },
                    "required": ["failed_query", "error_message"]
                }
            }
        }


class EnhancedExecutionHelper(BaseModel):
    """
    Enhanced execution helper that combines execution strategies with complexity analysis.
    """
    engine: Engine = Field(..., description="The engine to access database schema.")

    class Config:
        arbitrary_types_allowed = True

    def invoke(self, query_goal: str, current_approach: str = "") -> str:
        """
        Enhanced execution strategy with complexity analysis.
        
        Args:
            query_goal: Description of what the query should accomplish
            current_approach: Current query approach being used (optional)
            
        Returns:
            JSON string with execution strategies and complexity analysis
        """
        strategies = {
            'complexity_assessment': self._assess_goal_complexity(query_goal),
            'recommended_approach': '',
            'step_by_step_approach': [],
            'efficiency_tips': [],
            'common_pitfalls': [],
            'example_pattern': '',
            'alternative_strategies': []
        }
        
        goal_lower = query_goal.lower()
        
        # Enhanced goal analysis
        if any(word in goal_lower for word in ['microbiological', 'microbiology', 'culture']):
            strategies.update(self._get_microbiology_strategy())
        elif any(word in goal_lower for word in ['procedure', 'surgery', 'operation']):
            strategies.update(self._get_procedure_strategy())
        elif any(word in goal_lower for word in ['diagnosis', 'disease', 'condition']):
            strategies.update(self._get_diagnosis_strategy())
        elif any(word in goal_lower for word in ['lab', 'laboratory', 'test']):
            strategies.update(self._get_lab_strategy())
        elif any(word in goal_lower for word in ['recent', 'latest', 'last']):
            strategies.update(self._get_recent_data_strategy())
        elif any(word in goal_lower for word in ['count', 'number', 'how many']):
            strategies.update(self._get_counting_strategy())
        elif any(word in goal_lower for word in ['join', 'link', 'combine']):
            strategies.update(self._get_joining_strategy())
        elif any(word in goal_lower for word in ['group', 'aggregate', 'sum', 'average']):
            strategies.update(self._get_aggregation_strategy())
        else:
            strategies.update(self._get_general_strategy())
        
        return json.dumps(strategies, indent=2)

    def _assess_goal_complexity(self, goal: str) -> Dict[str, Any]:
        """Enhanced complexity assessment."""
        complexity_indicators = {
            'high': ['multiple tables', 'complex join', 'subquery', 'aggregate', 'group by', 'microbiological'],
            'medium': ['join', 'filter', 'specific patient', 'date range', 'procedure', 'diagnosis'],
            'low': ['simple select', 'count', 'list', 'single table']
        }
        
        goal_lower = goal.lower()
        complexity = 'low'
        
        for level, indicators in complexity_indicators.items():
            if any(indicator in goal_lower for indicator in indicators):
                complexity = level
                break
        
        return {
            'level': complexity,
            'estimated_tables': self._estimate_tables_needed(goal),
            'estimated_joins': self._estimate_joins_needed(goal),
            'recommended_approach': self._recommend_approach_by_complexity(complexity)
        }

    def _estimate_tables_needed(self, goal: str) -> List[str]:
        """Enhanced table estimation."""
        tables = []
        goal_lower = goal.lower()
        
        if any(word in goal_lower for word in ['patient', 'admission']):
            tables.extend(['patients', 'admissions'])
        if any(word in goal_lower for word in ['lab', 'laboratory']):
            tables.extend(['labevents', 'd_labitems'])
        if any(word in goal_lower for word in ['procedure', 'surgery']):
            tables.extend(['procedures_icd', 'd_icd_procedures'])
        if any(word in goal_lower for word in ['diagnosis', 'disease']):
            tables.extend(['diagnoses_icd', 'd_icd_diagnoses'])
        if any(word in goal_lower for word in ['microbiology', 'culture']):
            tables.append('microbiologyevents')
        if any(word in goal_lower for word in ['medication', 'drug', 'prescription']):
            tables.append('prescriptions')
        if any(word in goal_lower for word in ['vital', 'chart']):
            tables.extend(['chartevents', 'd_items'])
        
        return list(set(tables))

    def _estimate_joins_needed(self, goal: str) -> int:
        """Enhanced join estimation."""
        tables = self._estimate_tables_needed(goal)
        return max(0, len(tables) - 1)

    def _recommend_approach_by_complexity(self, complexity: str) -> str:
        """Recommend approach based on complexity."""
        if complexity == 'high':
            return 'Break into multiple simpler queries, then combine results'
        elif complexity == 'medium':
            return 'Use step-by-step joins with intermediate validation'
        else:
            return 'Direct query with proper filtering'

    def _get_microbiology_strategy(self) -> Dict[str, Any]:
        """Enhanced microbiology strategy."""
        return {
            'recommended_approach': 'Start with microbiologyevents table and join to admissions for patient context',
            'step_by_step_approach': [
                '1. Query microbiologyevents for basic test information',
                '2. Join with admissions via hadm_id for patient and timing context',
                '3. Filter by date ranges using chartdate',
                '4. Group by test_name or organism for aggregation',
                '5. Use spec_itemid and spec_typeid for specimen details'
            ],
            'efficiency_tips': [
                'Use chartdate for time filtering instead of complex date logic',
                'Filter by specific test types using test_name column',
                'Consider using LIMIT for large result sets'
            ],
            'alternative_strategies': [
                'Query microbiologyevents directly without complex joins',
                'Use two-step approach: find relevant hadm_ids first, then get test details'
            ],
            'example_pattern': 'SELECT test_name, COUNT(*) FROM microbiologyevents WHERE chartdate >= "2100-01-01" GROUP BY test_name'
        }

    def _get_procedure_strategy(self) -> Dict[str, Any]:
        """Enhanced procedure strategy."""
        return {
            'recommended_approach': 'Use procedures_icd with d_icd_procedures for procedure details',
            'step_by_step_approach': [
                '1. Search d_icd_procedures first to find relevant icd_codes',
                '2. Use those codes to filter procedures_icd',
                '3. Join with admissions for timing (admittime, dischtime)',
                '4. Filter by procedure type using long_title or short_title'
            ],
            'efficiency_tips': [
                'Search procedure descriptions first to identify relevant codes',
                'Use icd_code for exact matches, long_title for text searches',
                'Join with admissions only when date filtering is needed'
            ],
            'alternative_strategies': [
                'Two-step approach: find codes first, then get procedure instances',
                'Use LIKE operator for flexible procedure name matching'
            ]
        }

    def _get_diagnosis_strategy(self) -> Dict[str, Any]:
        """Enhanced diagnosis strategy."""
        return {
            'recommended_approach': 'Use diagnoses_icd with d_icd_diagnoses for diagnosis details',
            'step_by_step_approach': [
                '1. Search d_icd_diagnoses first for relevant diagnosis codes',
                '2. Use seq_num in diagnoses_icd to focus on primary diagnoses',
                '3. Join with admissions for patient and timing context',
                '4. Filter by diagnosis type using long_title'
            ],
            'efficiency_tips': [
                'Use seq_num = 1 for primary diagnoses only',
                'Filter by icd_version if specific ICD version is needed',
                'Consider using short_title for broader matches'
            ]
        }

    def _get_lab_strategy(self) -> Dict[str, Any]:
        """Enhanced lab strategy."""
        return {
            'recommended_approach': 'Use labevents with d_labitems for lab test details',
            'step_by_step_approach': [
                '1. Search d_labitems first to find relevant itemids',
                '2. Query labevents with specific itemids',
                '3. Use charttime for timing',
                '4. Filter by value, valuenum for result ranges'
            ],
            'efficiency_tips': [
                'Use valuenum for numeric comparisons, value for text results',
                'Filter by flag for abnormal results',
                'Use charttime for temporal analysis'
            ]
        }

    def _get_recent_data_strategy(self) -> Dict[str, Any]:
        """Enhanced recent data strategy."""
        return {
            'recommended_approach': 'Use ORDER BY with time column DESC and LIMIT',
            'step_by_step_approach': [
                '1. Identify the appropriate time column (charttime, admittime, etc.)',
                '2. Add WHERE clause for date range if needed',
                '3. ORDER BY time column DESC',
                '4. Use LIMIT to get only the number of records needed'
            ],
            'efficiency_tips': [
                'Use the most specific time column available',
                'Consider using date ranges instead of ordering large datasets',
                'Use LIMIT to prevent large result sets'
            ],
            'example_pattern': 'SELECT * FROM table WHERE charttime >= "2100-01-01" ORDER BY charttime DESC LIMIT 10'
        }

    def _get_counting_strategy(self) -> Dict[str, Any]:
        """Enhanced counting strategy."""
        return {
            'recommended_approach': 'Use COUNT() with appropriate WHERE conditions',
            'efficiency_tips': [
                'Use COUNT(*) for total records',
                'Use COUNT(column) to exclude NULLs',
                'Add WHERE clauses to filter before counting',
                'Use DISTINCT when counting unique values'
            ],
            'example_pattern': 'SELECT COUNT(*) FROM table WHERE condition'
        }

    def _get_joining_strategy(self) -> Dict[str, Any]:
        """Enhanced joining strategy."""
        return {
            'recommended_approach': 'Use appropriate JOIN types with clear ON conditions',
            'efficiency_tips': [
                'Use INNER JOIN when you need matching records only',
                'Use LEFT JOIN when you want all records from the left table',
                'Join on indexed columns when possible (subject_id, hadm_id)',
                'Use table aliases for clarity'
            ],
            'example_pattern': 'SELECT * FROM table1 t1 JOIN table2 t2 ON t1.id = t2.id'
        }

    def _get_aggregation_strategy(self) -> Dict[str, Any]:
        """Enhanced aggregation strategy."""
        return {
            'recommended_approach': 'Use GROUP BY with aggregate functions',
            'efficiency_tips': [
                'Group by the least granular level needed',
                'Use HAVING for filtering aggregated results',
                'Consider using window functions for complex aggregations',
                'Order results by aggregate values for insights'
            ],
            'example_pattern': 'SELECT column, COUNT(*) FROM table GROUP BY column HAVING COUNT(*) > 1'
        }

    def _get_general_strategy(self) -> Dict[str, Any]:
        """Enhanced general strategy."""
        return {
            'recommended_approach': 'Start simple and build complexity gradually',
            'step_by_step_approach': [
                '1. Identify the main table for your data',
                '2. Add filters to reduce data size',
                '3. Add joins one at a time',
                '4. Test each step before adding complexity',
                '5. Use LIMIT during development'
            ],
            'efficiency_tips': [
                'Use WHERE clauses early to filter data',
                'Test queries with LIMIT first',
                'Use table aliases for readability',
                'Break complex logic into multiple queries if needed'
            ]
        }

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "enhanced_execution_helper",
                "description": "Enhanced execution helper that combines execution strategies with complexity analysis. Provides comprehensive guidance for query planning and optimization.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query_goal": {
                            "type": "string",
                            "description": "Description of what the query should accomplish"
                        },
                        "current_approach": {
                            "type": "string",
                            "description": "Current query approach being used (optional)"
                        }
                    },
                    "required": ["query_goal"]
                }
            }
        } 