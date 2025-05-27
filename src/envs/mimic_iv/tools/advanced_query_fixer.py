import re
import json
from typing import Dict, List, Any, Optional
from sqlalchemy import text
from sqlalchemy.engine import Engine
from pydantic import BaseModel, Field

class AdvancedQueryFixer(BaseModel):
    """
    Advanced query fixer that handles complex error patterns and provides sophisticated auto-correction.
    Addresses SQLite-specific issues, complex joins, and advanced syntax problems.
    """
    engine: Engine = Field(..., description="The engine to access database schema.")

    class Config:
        arbitrary_types_allowed = True

    def invoke(self, failed_query: str, error_message: str, context: str = "") -> str:
        """
        Advanced fixing of complex SQL query issues with sophisticated pattern recognition.
        
        Args:
            failed_query: The SQL query that failed
            error_message: The error message from the database
            context: Additional context about what the query is trying to achieve
            
        Returns:
            JSON string with advanced fix suggestions and auto-corrected queries
        """
        fix_result = {
            'original_query': failed_query,
            'error_analysis': self._analyze_error_deeply(error_message, failed_query),
            'advanced_fixes': [],
            'auto_corrected_query': None,
            'confidence_score': 0.0,
            'explanation': '',
            'alternative_approaches': []
        }
        
        # Handle SQLite-specific syntax issues
        if self._is_sqlite_syntax_issue(error_message, failed_query):
            fix_result.update(self._fix_sqlite_syntax(failed_query, error_message))
        
        # Handle complex join issues
        elif self._is_complex_join_issue(error_message, failed_query):
            fix_result.update(self._fix_complex_joins(failed_query, error_message))
        
        # Handle column reference issues in subqueries
        elif self._is_subquery_column_issue(error_message, failed_query):
            fix_result.update(self._fix_subquery_columns(failed_query, error_message))
        
        # Handle date/time function issues
        elif self._is_datetime_function_issue(error_message, failed_query):
            fix_result.update(self._fix_datetime_functions(failed_query, error_message))
        
        # Handle table alias and reference issues
        elif self._is_table_reference_issue(error_message, failed_query):
            fix_result.update(self._fix_table_references(failed_query, error_message))
        
        # Handle advanced column mapping issues
        else:
            fix_result.update(self._advanced_column_mapping(failed_query, error_message))
        
        return json.dumps(fix_result, indent=2)

    def _analyze_error_deeply(self, error_message: str, query: str) -> Dict[str, Any]:
        """Perform deep analysis of the error."""
        analysis = {
            'error_category': 'unknown',
            'severity': 'medium',
            'likely_cause': '',
            'query_complexity': self._assess_query_complexity(query)
        }
        
        error_lower = error_message.lower()
        
        if 'near "from"' in error_lower:
            analysis.update({
                'error_category': 'sqlite_syntax',
                'severity': 'high',
                'likely_cause': 'SQLite-specific syntax issue, possibly with subqueries or CTEs'
            })
        elif 'extract(' in query.lower() and 'syntax error' in error_lower:
            analysis.update({
                'error_category': 'datetime_function',
                'severity': 'high',
                'likely_cause': 'EXTRACT function not supported in SQLite, need STRFTIME'
            })
        elif 'procedures_icd.chartdate' in error_message:
            analysis.update({
                'error_category': 'wrong_column',
                'severity': 'medium',
                'likely_cause': 'procedures_icd table does not have chartdate column'
            })
        elif 'icd9_code' in error_message:
            analysis.update({
                'error_category': 'wrong_column',
                'severity': 'medium',
                'likely_cause': 'Column should be icd_code, not icd9_code'
            })
        
        return analysis

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

    def _is_sqlite_syntax_issue(self, error_message: str, query: str) -> bool:
        """Check if this is a SQLite-specific syntax issue."""
        sqlite_indicators = [
            'near "from"' in error_message.lower(),
            'extract(' in query.lower() and 'syntax error' in error_message.lower(),
            'limit' in query.lower() and 'offset' in query.lower() and 'syntax error' in error_message.lower()
        ]
        return any(sqlite_indicators)

    def _fix_sqlite_syntax(self, query: str, error_message: str) -> Dict[str, Any]:
        """Fix SQLite-specific syntax issues."""
        corrected_query = query
        fixes = []
        
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
            fixes.append("Converted EXTRACT functions to SQLite-compatible STRFTIME")
        
        # Fix complex subquery syntax issues
        if 'near "from"' in error_message.lower():
            # This often happens with complex WHERE clauses in subqueries
            fixes.append("Restructure subquery to avoid SQLite parsing issues")
            fixes.append("Consider breaking complex query into simpler parts")
        
        return {
            'advanced_fixes': fixes,
            'auto_corrected_query': corrected_query if corrected_query != query else None,
            'confidence_score': 0.8 if corrected_query != query else 0.3,
            'explanation': 'SQLite has specific syntax requirements that differ from other SQL databases'
        }

    def _is_complex_join_issue(self, error_message: str, query: str) -> bool:
        """Check if this is a complex join issue."""
        return (
            query.lower().count('join') >= 2 and
            ('ambiguous' in error_message.lower() or 'no such column' in error_message.lower())
        )

    def _fix_complex_joins(self, query: str, error_message: str) -> Dict[str, Any]:
        """Fix complex join issues."""
        fixes = []
        corrected_query = query
        
        # Add table aliases if missing
        if not re.search(r'\w+\s+AS\s+\w+|\w+\s+\w+(?=\s+(?:JOIN|WHERE|GROUP|ORDER))', query, re.IGNORECASE):
            fixes.append("Add table aliases to clarify column references")
            fixes.append("Example: FROM table1 t1 JOIN table2 t2 ON t1.id = t2.id")
        
        # Suggest specific join patterns for MIMIC-IV
        if 'procedures_icd' in query.lower() and 'd_icd_procedures' in query.lower():
            fixes.append("Use: procedures_icd.icd_code = d_icd_procedures.icd_code")
        
        if 'labevents' in query.lower() and 'd_labitems' in query.lower():
            fixes.append("Use: labevents.itemid = d_labitems.itemid")
        
        if 'microbiologyevents' in query.lower():
            fixes.append("Link microbiologyevents via hadm_id to other tables")
            fixes.append("Use spec_itemid and spec_typeid for specimen information")
        
        return {
            'advanced_fixes': fixes,
            'confidence_score': 0.6,
            'explanation': 'Complex joins require careful table aliasing and proper foreign key relationships'
        }

    def _is_subquery_column_issue(self, error_message: str, query: str) -> bool:
        """Check if this is a subquery column reference issue."""
        return (
            'no such column' in error_message.lower() and
            query.lower().count('select') > 1
        )

    def _fix_subquery_columns(self, query: str, error_message: str) -> Dict[str, Any]:
        """Fix subquery column reference issues."""
        fixes = []
        
        # Extract the problematic column from error message
        match = re.search(r'no such column: ([\w.]+)', error_message.lower())
        if match:
            problematic_col = match.group(1)
            fixes.append(f"Column '{problematic_col}' not accessible in this scope")
            fixes.append("Ensure column exists in the table being queried")
            fixes.append("Check if column should be in outer query instead of subquery")
        
        return {
            'advanced_fixes': fixes,
            'confidence_score': 0.4,
            'explanation': 'Subquery column references must be properly scoped'
        }

    def _is_datetime_function_issue(self, error_message: str, query: str) -> bool:
        """Check if this is a datetime function issue."""
        return (
            'extract(' in query.lower() or
            'year(' in query.lower() or
            'month(' in query.lower()
        ) and 'syntax error' in error_message.lower()

    def _fix_datetime_functions(self, query: str, error_message: str) -> Dict[str, Any]:
        """Fix datetime function issues."""
        corrected_query = query
        fixes = []
        
        # Convert various date functions to SQLite STRFTIME
        date_function_map = {
            r'YEAR\s*\(\s*([^)]+)\)': r"STRFTIME('%Y', \1)",
            r'MONTH\s*\(\s*([^)]+)\)': r"STRFTIME('%m', \1)",
            r'DAY\s*\(\s*([^)]+)\)': r"STRFTIME('%d', \1)",
            r'EXTRACT\s*\(\s*YEAR\s+FROM\s+([^)]+)\)': r"STRFTIME('%Y', \1)",
            r'EXTRACT\s*\(\s*MONTH\s+FROM\s+([^)]+)\)': r"STRFTIME('%m', \1)"
        }
        
        for pattern, replacement in date_function_map.items():
            if re.search(pattern, corrected_query, re.IGNORECASE):
                corrected_query = re.sub(pattern, replacement, corrected_query, flags=re.IGNORECASE)
                fixes.append(f"Converted date function to SQLite STRFTIME format")
        
        return {
            'advanced_fixes': fixes,
            'auto_corrected_query': corrected_query if corrected_query != query else None,
            'confidence_score': 0.9,
            'explanation': 'SQLite uses STRFTIME for date/time operations instead of EXTRACT or other functions'
        }

    def _is_table_reference_issue(self, error_message: str, query: str) -> bool:
        """Check if this is a table reference issue."""
        return 'no such column' in error_message.lower() and any(
            table in error_message.lower() for table in 
            ['procedures_icd', 'diagnoses_icd', 'labevents', 'microbiologyevents']
        )

    def _fix_table_references(self, query: str, error_message: str) -> Dict[str, Any]:
        """Fix table reference issues."""
        fixes = []
        corrected_query = query
        
        # Common MIMIC-IV column corrections
        column_fixes = {
            'procedures_icd.chartdate': 'procedures_icd does not have chartdate - use admissions.admittime',
            'procedures_icd.patient_id': 'Use procedures_icd.subject_id instead',
            'procedures_icd.procedure_id': 'Use procedures_icd.icd_code instead',
            'diagnoses_icd.diagnosis_id': 'Use diagnoses_icd.icd_code instead',
            'p.icd9_code': 'Use p.icd_code instead (column name is icd_code, not icd9_code)',
            'd_icd_procedures.icd9_code': 'Use d_icd_procedures.icd_code instead'
        }
        
        for wrong_col, correction in column_fixes.items():
            if wrong_col in error_message.lower():
                fixes.append(correction)
                # Auto-correct some simple cases
                if 'icd9_code' in wrong_col:
                    corrected_query = corrected_query.replace('icd9_code', 'icd_code')
                elif 'patient_id' in wrong_col:
                    corrected_query = corrected_query.replace('patient_id', 'subject_id')
        
        return {
            'advanced_fixes': fixes,
            'auto_corrected_query': corrected_query if corrected_query != query else None,
            'confidence_score': 0.7,
            'explanation': 'MIMIC-IV has specific column names that differ from common expectations'
        }

    def _advanced_column_mapping(self, query: str, error_message: str) -> Dict[str, Any]:
        """Advanced column mapping for complex cases."""
        fixes = []
        
        # Suggest alternative query structures
        if 'microbiologyevents' in query.lower():
            fixes.append("For microbiological tests, join microbiologyevents with admissions via hadm_id")
            fixes.append("Use spec_itemid to link to specimen information")
            fixes.append("Consider using chartdate for timing instead of starttime")
        
        if 'procedures_icd' in query.lower() and 'year' in query.lower():
            fixes.append("For procedure dates, join with admissions table to get admittime")
            fixes.append("procedures_icd table doesn't have direct date columns")
        
        return {
            'advanced_fixes': fixes,
            'confidence_score': 0.5,
            'explanation': 'Complex queries may require restructuring with proper table relationships'
        }

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "advanced_query_fixer",
                "description": "Advanced query fixer for complex SQL issues including SQLite-specific syntax, complex joins, and sophisticated auto-correction. Handles edge cases that basic query optimization misses.",
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


class QueryComplexityAnalyzer(BaseModel):
    """
    Analyzes query complexity and suggests simpler alternative approaches.
    """
    engine: Engine = Field(..., description="The engine to access database schema.")

    class Config:
        arbitrary_types_allowed = True

    def invoke(self, query_goal: str, current_approach: str = "") -> str:
        """
        Analyze query complexity and suggest simpler approaches.
        
        Args:
            query_goal: What the user is trying to achieve
            current_approach: Current query approach being used (optional)
            
        Returns:
            JSON string with complexity analysis and alternative approaches
        """
        analysis = {
            'complexity_assessment': self._assess_goal_complexity(query_goal),
            'recommended_strategy': '',
            'step_by_step_approach': [],
            'simpler_alternatives': [],
            'common_pitfalls': [],
            'example_queries': []
        }
        
        goal_lower = query_goal.lower()
        
        # Analyze specific goal types
        if any(word in goal_lower for word in ['microbiological', 'microbiology', 'culture']):
            analysis.update(self._microbiology_strategy())
        elif any(word in goal_lower for word in ['procedure', 'surgery', 'operation']):
            analysis.update(self._procedure_strategy())
        elif any(word in goal_lower for word in ['diagnosis', 'disease', 'condition']):
            analysis.update(self._diagnosis_strategy())
        elif any(word in goal_lower for word in ['lab', 'laboratory', 'test']):
            analysis.update(self._lab_strategy())
        else:
            analysis.update(self._general_strategy())
        
        return json.dumps(analysis, indent=2)

    def _assess_goal_complexity(self, goal: str) -> Dict[str, Any]:
        """Assess the complexity of the query goal."""
        complexity_indicators = {
            'high': ['multiple tables', 'complex join', 'subquery', 'aggregate', 'group by'],
            'medium': ['join', 'filter', 'specific patient', 'date range'],
            'low': ['simple select', 'count', 'list']
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
            'estimated_joins': self._estimate_joins_needed(goal)
        }

    def _estimate_tables_needed(self, goal: str) -> List[str]:
        """Estimate which tables are needed for the goal."""
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
        
        return list(set(tables))

    def _estimate_joins_needed(self, goal: str) -> int:
        """Estimate number of joins needed."""
        tables = self._estimate_tables_needed(goal)
        return max(0, len(tables) - 1)

    def _microbiology_strategy(self) -> Dict[str, Any]:
        """Strategy for microbiology-related queries."""
        return {
            'recommended_strategy': 'Start with microbiologyevents table and join to admissions for patient context',
            'step_by_step_approach': [
                '1. Query microbiologyevents for basic test information',
                '2. Join with admissions via hadm_id for patient and timing context',
                '3. Filter by date ranges using chartdate',
                '4. Group by test_name or organism for aggregation'
            ],
            'simpler_alternatives': [
                'Query microbiologyevents directly without complex joins',
                'Use chartdate for time filtering instead of complex date logic',
                'Filter by specific test types using test_name column'
            ],
            'example_queries': [
                'SELECT test_name, COUNT(*) FROM microbiologyevents WHERE chartdate >= "2100-01-01" GROUP BY test_name'
            ]
        }

    def _procedure_strategy(self) -> Dict[str, Any]:
        """Strategy for procedure-related queries."""
        return {
            'recommended_strategy': 'Use procedures_icd with d_icd_procedures for procedure details',
            'step_by_step_approach': [
                '1. Start with procedures_icd table',
                '2. Join with d_icd_procedures on icd_code for procedure names',
                '3. Join with admissions for timing (admittime, dischtime)',
                '4. Filter by procedure type using long_title or short_title'
            ],
            'simpler_alternatives': [
                'Search d_icd_procedures first to find relevant icd_codes',
                'Use those codes to filter procedures_icd directly',
                'Join with admissions only when date filtering is needed'
            ],
            'example_queries': [
                'SELECT icd_code FROM d_icd_procedures WHERE long_title LIKE "%drainage%"',
                'SELECT * FROM procedures_icd WHERE icd_code IN (SELECT icd_code FROM d_icd_procedures WHERE long_title LIKE "%drainage%")'
            ]
        }

    def _diagnosis_strategy(self) -> Dict[str, Any]:
        """Strategy for diagnosis-related queries."""
        return {
            'recommended_strategy': 'Use diagnoses_icd with d_icd_diagnoses for diagnosis details',
            'step_by_step_approach': [
                '1. Start with diagnoses_icd table',
                '2. Join with d_icd_diagnoses on icd_code for diagnosis names',
                '3. Join with admissions for patient and timing context',
                '4. Filter by diagnosis type using long_title'
            ],
            'simpler_alternatives': [
                'Search d_icd_diagnoses first for relevant diagnosis codes',
                'Use seq_num in diagnoses_icd to focus on primary diagnoses',
                'Filter by icd_version if specific ICD version is needed'
            ]
        }

    def _lab_strategy(self) -> Dict[str, Any]:
        """Strategy for lab-related queries."""
        return {
            'recommended_strategy': 'Use labevents with d_labitems for lab test details',
            'step_by_step_approach': [
                '1. Start with labevents table',
                '2. Join with d_labitems on itemid for test names and details',
                '3. Use charttime for timing',
                '4. Filter by value, valuenum for result ranges'
            ],
            'simpler_alternatives': [
                'Search d_labitems first to find relevant itemids',
                'Query labevents with specific itemids',
                'Use valuenum for numeric comparisons, value for text results'
            ]
        }

    def _general_strategy(self) -> Dict[str, Any]:
        """General strategy for other queries."""
        return {
            'recommended_strategy': 'Start simple and build complexity gradually',
            'step_by_step_approach': [
                '1. Identify the main table for your data',
                '2. Add joins one at a time',
                '3. Test each step before adding complexity',
                '4. Use WHERE clauses to filter early'
            ],
            'simpler_alternatives': [
                'Break complex queries into multiple simpler queries',
                'Use temporary results to build up to final answer',
                'Focus on one aspect at a time'
            ]
        }

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "query_complexity_analyzer",
                "description": "Analyzes query complexity and suggests simpler alternative approaches. Helps break down complex goals into manageable steps.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query_goal": {
                            "type": "string",
                            "description": "Description of what the user is trying to achieve with their query"
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