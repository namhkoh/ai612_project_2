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