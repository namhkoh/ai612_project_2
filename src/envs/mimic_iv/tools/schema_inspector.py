import json
from typing import Dict, Any, List
from sqlalchemy import text, inspect
from sqlalchemy.engine import Engine
from pydantic import BaseModel, Field

class SchemaInspector(BaseModel):
    engine: Engine = Field(..., description="The engine to inspect schema from.")

    class Config:
        arbitrary_types_allowed = True

    def invoke(self, search_in: str, keyword: str) -> str:
        """
        Search for tables or columns containing a keyword.
        
        Args:
            search_in: Either "table_names", "column_names", or "both"
            keyword: The keyword to search for (case-insensitive)
        """
        try:
            inspector = inspect(self.engine)
            keyword_lower = keyword.lower()
            results = {"tables": [], "columns": []}
            
            if search_in in ["table_names", "both"]:
                # Search in table names
                tables = inspector.get_table_names()
                matching_tables = [table for table in tables if keyword_lower in table.lower()]
                results["tables"] = matching_tables
            
            if search_in in ["column_names", "both"]:
                # Search in column names across all tables
                tables = inspector.get_table_names()
                for table in tables:
                    try:
                        columns = inspector.get_columns(table)
                        matching_columns = [
                            {"table": table, "column": col["name"], "type": str(col["type"])}
                            for col in columns 
                            if keyword_lower in col["name"].lower()
                        ]
                        results["columns"].extend(matching_columns)
                    except Exception:
                        continue
            
            # Format response
            response_parts = []
            
            if results["tables"]:
                response_parts.append(f"Tables containing '{keyword}': {', '.join(results['tables'])}")
            
            if results["columns"]:
                col_info = []
                for col in results["columns"]:
                    col_info.append(f"{col['table']}.{col['column']} ({col['type']})")
                response_parts.append(f"Columns containing '{keyword}': {', '.join(col_info)}")
            
            if not results["tables"] and not results["columns"]:
                return f"No tables or columns found containing '{keyword}'."
            
            return "\n".join(response_parts)
            
        except Exception as e:
            return f"Error inspecting schema: {str(e)}"

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "schema_inspector_tool",
                "description": "Search for table names and column names containing a specific keyword. Useful for discovering relevant tables and columns when you don't know the exact schema structure.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "search_in": {
                            "type": "string", 
                            "enum": ["table_names", "column_names", "both"],
                            "description": "Where to search: 'table_names' for table names only, 'column_names' for column names only, or 'both' for both tables and columns."
                        },
                        "keyword": {
                            "type": "string", 
                            "description": "The keyword to search for in table/column names (case-insensitive)."
                        }
                    },
                    "required": ["search_in", "keyword"]
                }
            }
        } 