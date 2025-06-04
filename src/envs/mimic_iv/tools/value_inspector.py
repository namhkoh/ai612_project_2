import json
from typing import Dict, Any, List, Optional
from sqlalchemy import text
from sqlalchemy.engine import Engine
from pydantic import BaseModel, Field

class ValueInspector(BaseModel):
    engine: Engine = Field(..., description="The engine to inspect values from.")

    class Config:
        arbitrary_types_allowed = True

    def invoke(self, table: str, column: str, analysis_type: str = "summary") -> str:
        """
        Analyze values in a specific column.
        
        Args:
            table: The table name
            column: The column name
            analysis_type: Type of analysis - "summary", "distinct", "range", or "patterns"
        """
        try:
            with self.engine.connect() as connection:
                if analysis_type == "summary":
                    return self._get_summary_analysis(connection, table, column)
                elif analysis_type == "distinct":
                    return self._get_distinct_values(connection, table, column)
                elif analysis_type == "range":
                    return self._get_range_analysis(connection, table, column)
                elif analysis_type == "patterns":
                    return self._get_pattern_analysis(connection, table, column)
                else:
                    return f"Unknown analysis_type: {analysis_type}. Use 'summary', 'distinct', 'range', or 'patterns'."
                    
        except Exception as e:
            return f"Error analyzing {table}.{column}: {str(e)}"

    def _get_summary_analysis(self, connection, table: str, column: str) -> str:
        """Get overall summary statistics for a column."""
        try:
            # Basic counts
            count_query = text(f"SELECT COUNT(*) as total, COUNT({column}) as non_null, COUNT(DISTINCT {column}) as distinct_count FROM {table}")
            counts = connection.execute(count_query).fetchone()
            total, non_null, distinct_count = counts
            
            null_count = total - non_null
            null_percentage = (null_count / total * 100) if total > 0 else 0
            
            result = [
                f"Column {table}.{column} summary:",
                f"  Total rows: {total}",
                f"  Non-null values: {non_null}",
                f"  Null values: {null_count} ({null_percentage:.1f}%)",
                f"  Distinct values: {distinct_count}"
            ]
            
            # Try to determine if numeric
            try:
                numeric_query = text(f"SELECT MIN(CAST({column} AS REAL)), MAX(CAST({column} AS REAL)), AVG(CAST({column} AS REAL)) FROM {table} WHERE {column} IS NOT NULL AND {column} != ''")
                numeric_stats = connection.execute(numeric_query).fetchone()
                if numeric_stats and numeric_stats[0] is not None:
                    min_val, max_val, avg_val = numeric_stats
                    result.extend([
                        f"  Numeric range: {min_val} to {max_val}",
                        f"  Average: {avg_val:.2f}" if avg_val else ""
                    ])
            except:
                # Not numeric, show common values instead
                common_query = text(f"SELECT {column}, COUNT(*) as count FROM {table} WHERE {column} IS NOT NULL GROUP BY {column} ORDER BY count DESC LIMIT 5")
                common_values = connection.execute(common_query).fetchall()
                if common_values:
                    result.append("  Most common values:")
                    for value, count in common_values:
                        percentage = (count / non_null * 100) if non_null > 0 else 0
                        result.append(f"    '{value}': {count} ({percentage:.1f}%)")
            
            return "\n".join(result)
            
        except Exception as e:
            return f"Error in summary analysis: {str(e)}"

    def _get_distinct_values(self, connection, table: str, column: str) -> str:
        """Get all distinct values for a column (limited to reasonable number)."""
        try:
            # First check how many distinct values there are
            count_query = text(f"SELECT COUNT(DISTINCT {column}) FROM {table} WHERE {column} IS NOT NULL")
            distinct_count = connection.execute(count_query).scalar()
            
            if distinct_count > 100:
                return f"Column {table}.{column} has {distinct_count} distinct values (too many to display). Use 'summary' or 'range' analysis instead."
            
            # Get distinct values with their counts
            query = text(f"SELECT {column}, COUNT(*) as count FROM {table} WHERE {column} IS NOT NULL GROUP BY {column} ORDER BY count DESC")
            values = connection.execute(query).fetchall()
            
            result = [f"All distinct values in {table}.{column} ({distinct_count} total):"]
            for value, count in values:
                result.append(f"  '{value}': {count} occurrences")
            
            return "\n".join(result)
            
        except Exception as e:
            return f"Error getting distinct values: {str(e)}"

    def _get_range_analysis(self, connection, table: str, column: str) -> str:
        """Get range analysis for numeric or date columns."""
        try:
            # Try numeric analysis first
            try:
                numeric_query = text(f"""
                    SELECT 
                        MIN(CAST({column} AS REAL)) as min_val,
                        MAX(CAST({column} AS REAL)) as max_val,
                        AVG(CAST({column} AS REAL)) as avg_val,
                        COUNT(*) as count
                    FROM {table} 
                    WHERE {column} IS NOT NULL AND {column} != ''
                """)
                stats = connection.execute(numeric_query).fetchone()
                if stats and stats[0] is not None:
                    min_val, max_val, avg_val, count = stats
                    return f"Numeric range analysis for {table}.{column}:\n  Range: {min_val} to {max_val}\n  Average: {avg_val:.2f}\n  Valid numeric values: {count}"
            except:
                pass
            
            # Try date analysis
            try:
                date_query = text(f"""
                    SELECT 
                        MIN({column}) as min_date,
                        MAX({column}) as max_date,
                        COUNT(*) as count
                    FROM {table} 
                    WHERE {column} IS NOT NULL AND {column} != ''
                """)
                stats = connection.execute(date_query).fetchone()
                if stats and stats[0]:
                    min_date, max_date, count = stats
                    return f"Date range analysis for {table}.{column}:\n  Range: {min_date} to {max_date}\n  Valid date values: {count}"
            except:
                pass
            
            # If neither numeric nor date, show string length analysis
            length_query = text(f"""
                SELECT 
                    MIN(LENGTH({column})) as min_len,
                    MAX(LENGTH({column})) as max_len,
                    AVG(LENGTH({column})) as avg_len,
                    COUNT(*) as count
                FROM {table} 
                WHERE {column} IS NOT NULL AND {column} != ''
            """)
            stats = connection.execute(length_query).fetchone()
            if stats:
                min_len, max_len, avg_len, count = stats
                return f"String length analysis for {table}.{column}:\n  Length range: {min_len} to {max_len} characters\n  Average length: {avg_len:.1f} characters\n  Non-empty values: {count}"
            
            return f"Could not perform range analysis on {table}.{column}"
            
        except Exception as e:
            return f"Error in range analysis: {str(e)}"

    def _get_pattern_analysis(self, connection, table: str, column: str) -> str:
        """Analyze patterns in the data (useful for codes, IDs, etc.)."""
        try:
            # Sample some values to analyze patterns
            sample_query = text(f"SELECT DISTINCT {column} FROM {table} WHERE {column} IS NOT NULL AND {column} != '' LIMIT 20")
            samples = [row[0] for row in connection.execute(sample_query).fetchall()]
            
            if not samples:
                return f"No non-null values found in {table}.{column}"
            
            patterns = {
                "all_numeric": all(str(s).replace('.', '').replace('-', '').isdigit() for s in samples if s),
                "all_alpha": all(str(s).isalpha() for s in samples if s),
                "has_dates": any(self._looks_like_date(str(s)) for s in samples if s),
                "has_codes": any(self._looks_like_code(str(s)) for s in samples if s),
                "length_consistent": len(set(len(str(s)) for s in samples if s)) <= 2
            }
            
            # Length distribution
            lengths = [len(str(s)) for s in samples if s]
            min_len, max_len = min(lengths), max(lengths)
            
            result = [f"Pattern analysis for {table}.{column} (based on {len(samples)} samples):"]
            
            if patterns["all_numeric"]:
                result.append("  Pattern: All numeric values")
            elif patterns["all_alpha"]:
                result.append("  Pattern: All alphabetic values")
            elif patterns["has_dates"]:
                result.append("  Pattern: Contains date-like values")
            elif patterns["has_codes"]:
                result.append("  Pattern: Contains code-like values (alphanumeric with separators)")
            else:
                result.append("  Pattern: Mixed content")
            
            if patterns["length_consistent"]:
                result.append(f"  Length: Consistent ({min_len}-{max_len} characters)")
            else:
                result.append(f"  Length: Variable ({min_len}-{max_len} characters)")
            
            # Fix the problematic f-string by separating the logic
            sample_values_str = ', '.join([f"'{s}'" for s in samples[:5]])
            result.append(f"  Sample values: {sample_values_str}")
            
            return "\n".join(result)
            
        except Exception as e:
            return f"Error in pattern analysis: {str(e)}"

    def _looks_like_date(self, value: str) -> bool:
        """Check if a value looks like a date."""
        import re
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
            r'\d{2}/\d{2}/\d{4}',  # MM/DD/YYYY
            r'\d{4}/\d{2}/\d{2}',  # YYYY/MM/DD
            r'\d{2}-\d{2}-\d{4}',  # MM-DD-YYYY
        ]
        return any(re.match(pattern, value) for pattern in date_patterns)

    def _looks_like_code(self, value: str) -> bool:
        """Check if a value looks like a medical/administrative code."""
        import re
        # Common medical code patterns
        code_patterns = [
            r'^[A-Z]\d{2}',  # ICD-10 pattern (letter + 2 digits)
            r'^\d{5}$',      # 5-digit codes
            r'^[A-Z]{1,3}\d+', # Letter prefix + numbers
            r'^\d+-\d+',     # Number-dash-number
        ]
        return any(re.match(pattern, value) for pattern in code_patterns)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "value_inspector_tool",
                "description": "Analyze values in a specific column to understand data patterns, ranges, and distributions. Essential for understanding EHR data before writing SQL queries.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "table": {
                            "type": "string", 
                            "description": "The table name to analyze."
                        },
                        "column": {
                            "type": "string", 
                            "description": "The column name to analyze."
                        },
                        "analysis_type": {
                            "type": "string",
                            "enum": ["summary", "distinct", "range", "patterns"],
                            "description": "Type of analysis: 'summary' for overview statistics, 'distinct' for all unique values, 'range' for numeric/date ranges, 'patterns' for data format analysis."
                        }
                    },
                    "required": ["table", "column"]
                }
            }
        } 