# TODO: Implement your own tool here.

import json
from typing import Dict, Any, List, Set
from sqlalchemy import text, inspect
from sqlalchemy.engine import Engine
from pydantic import BaseModel, Field

class RelationshipDiscovery(BaseModel):
    engine: Engine = Field(..., description="The engine to discover relationships from.")

    class Config:
        arbitrary_types_allowed = True

    def invoke(self, table1: str, table2: str = "", discovery_type: str = "connections") -> str:
        """
        Discover relationships between tables.
        
        Args:
            table1: Primary table to analyze
            table2: Optional second table for specific pair analysis
            discovery_type: "connections", "foreign_keys", or "common_columns"
        """
        try:
            if discovery_type == "connections":
                return self._find_table_connections(table1, table2)
            elif discovery_type == "foreign_keys":
                return self._get_foreign_key_relationships(table1)
            elif discovery_type == "common_columns":
                return self._find_common_columns(table1, table2)
            else:
                return f"Unknown discovery_type: {discovery_type}. Use 'connections', 'foreign_keys', or 'common_columns'."
                
        except Exception as e:
            return f"Error discovering relationships: {str(e)}"

    def _find_table_connections(self, table1: str, table2: str = "") -> str:
        """Find how tables can be connected via foreign keys or common columns."""
        try:
            inspector = inspect(self.engine)
            all_tables = inspector.get_table_names()
            
            if table1 not in all_tables:
                return f"Table '{table1}' not found in database."
            
            if table2 and table2 not in all_tables:
                return f"Table '{table2}' not found in database."
            
            # Get foreign key relationships for table1
            fk_relationships = []
            try:
                fks = inspector.get_foreign_keys(table1)
                for fk in fks:
                    fk_relationships.append({
                        "from_table": table1,
                        "from_column": fk['constrained_columns'][0] if fk['constrained_columns'] else 'unknown',
                        "to_table": fk['referred_table'],
                        "to_column": fk['referred_columns'][0] if fk['referred_columns'] else 'unknown',
                        "type": "foreign_key"
                    })
            except:
                pass
            
            # Find foreign keys pointing TO table1
            for table in all_tables:
                if table == table1:
                    continue
                try:
                    fks = inspector.get_foreign_keys(table)
                    for fk in fks:
                        if fk['referred_table'] == table1:
                            fk_relationships.append({
                                "from_table": table,
                                "from_column": fk['constrained_columns'][0] if fk['constrained_columns'] else 'unknown',
                                "to_table": table1,
                                "to_column": fk['referred_columns'][0] if fk['referred_columns'] else 'unknown',
                                "type": "foreign_key"
                            })
                except:
                    continue
            
            # If analyzing a specific pair, also check for common columns
            common_columns = []
            if table2:
                try:
                    cols1 = set(col['name'] for col in inspector.get_columns(table1))
                    cols2 = set(col['name'] for col in inspector.get_columns(table2))
                    common_col_names = cols1.intersection(cols2)
                    
                    for col in common_col_names:
                        common_columns.append({
                            "table1": table1,
                            "table2": table2,
                            "column": col,
                            "type": "common_column"
                        })
                except:
                    pass
            
            # Format results
            result = [f"Relationships for table '{table1}':"]
            
            if fk_relationships:
                result.append("\nForeign Key Relationships:")
                for rel in fk_relationships:
                    if rel["from_table"] == table1:
                        result.append(f"  {rel['from_table']}.{rel['from_column']} -> {rel['to_table']}.{rel['to_column']}")
                    else:
                        result.append(f"  {rel['from_table']}.{rel['from_column']} -> {rel['to_table']}.{rel['to_column']}")
            
            if common_columns:
                result.append(f"\nCommon columns with '{table2}':")
                for rel in common_columns:
                    result.append(f"  {rel['column']} (appears in both tables)")
            
            if not fk_relationships and not common_columns:
                if table2:
                    result.append(f"\nNo direct relationships found between '{table1}' and '{table2}'.")
                else:
                    result.append(f"\nNo foreign key relationships found for '{table1}'.")
                    
                # Suggest looking for common column patterns
                result.append("Try using 'common_columns' discovery_type or check for ID patterns.")
            
            return "\n".join(result)
            
        except Exception as e:
            return f"Error finding connections: {str(e)}"

    def _get_foreign_key_relationships(self, table: str) -> str:
        """Get detailed foreign key information for a table."""
        try:
            inspector = inspect(self.engine)
            
            if table not in inspector.get_table_names():
                return f"Table '{table}' not found in database."
            
            # Outgoing foreign keys
            outgoing_fks = inspector.get_foreign_keys(table)
            
            # Incoming foreign keys (tables that reference this table)
            incoming_fks = []
            for other_table in inspector.get_table_names():
                if other_table == table:
                    continue
                try:
                    fks = inspector.get_foreign_keys(other_table)
                    for fk in fks:
                        if fk['referred_table'] == table:
                            incoming_fks.append({
                                "from_table": other_table,
                                "from_columns": fk['constrained_columns'],
                                "to_columns": fk['referred_columns']
                            })
                except:
                    continue
            
            result = [f"Foreign key relationships for '{table}':"]
            
            if outgoing_fks:
                result.append(f"\nOutgoing (this table references others):")
                for fk in outgoing_fks:
                    from_cols = ', '.join(fk['constrained_columns'])
                    to_cols = ', '.join(fk['referred_columns'])
                    result.append(f"  {table}({from_cols}) -> {fk['referred_table']}({to_cols})")
            
            if incoming_fks:
                result.append(f"\nIncoming (other tables reference this table):")
                for fk in incoming_fks:
                    from_cols = ', '.join(fk['from_columns'])
                    to_cols = ', '.join(fk['to_columns'])
                    result.append(f"  {fk['from_table']}({from_cols}) -> {table}({to_cols})")
            
            if not outgoing_fks and not incoming_fks:
                result.append(f"\nNo foreign key relationships found for '{table}'.")
            
            return "\n".join(result)
            
        except Exception as e:
            return f"Error getting foreign keys: {str(e)}"

    def _find_common_columns(self, table1: str, table2: str) -> str:
        """Find columns that appear in both tables."""
        try:
            inspector = inspect(self.engine)
            
            if table1 not in inspector.get_table_names():
                return f"Table '{table1}' not found in database."
            
            if not table2:
                return "Please specify table2 for common column analysis."
            
            if table2 not in inspector.get_table_names():
                return f"Table '{table2}' not found in database."
            
            # Get columns for both tables
            cols1 = inspector.get_columns(table1)
            cols2 = inspector.get_columns(table2)
            
            cols1_info = {col['name']: str(col['type']) for col in cols1}
            cols2_info = {col['name']: str(col['type']) for col in cols2}
            
            common_names = set(cols1_info.keys()).intersection(set(cols2_info.keys()))
            
            if not common_names:
                return f"No common column names found between '{table1}' and '{table2}'."
            
            result = [f"Common columns between '{table1}' and '{table2}':"]
            
            for col_name in sorted(common_names):
                type1 = cols1_info[col_name]
                type2 = cols2_info[col_name]
                if type1 == type2:
                    result.append(f"  {col_name}: {type1} (same type)")
                else:
                    result.append(f"  {col_name}: {type1} vs {type2} (type mismatch)")
            
            # Suggest potential join conditions
            likely_join_cols = [col for col in common_names if 
                               any(keyword in col.lower() for keyword in ['id', 'key', 'patient', 'subject'])]
            
            if likely_join_cols:
                result.append(f"\nLikely join columns: {', '.join(likely_join_cols)}")
            
            return "\n".join(result)
            
        except Exception as e:
            return f"Error finding common columns: {str(e)}"

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "relationship_discovery_tool",
                "description": "Discover relationships between EHR tables through foreign keys and common columns. Essential for understanding how to JOIN tables correctly in SQL queries.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "table1": {
                            "type": "string", 
                            "description": "Primary table to analyze relationships for."
                        },
                        "table2": {
                            "type": "string", 
                            "description": "Optional second table for analyzing relationships between specific table pairs."
                        },
                        "discovery_type": {
                            "type": "string",
                            "enum": ["connections", "foreign_keys", "common_columns"],
                            "description": "Type of relationship discovery: 'connections' for general relationships, 'foreign_keys' for detailed FK analysis, 'common_columns' for shared column analysis."
                        }
                    },
                    "required": ["table1"]
                }
            }
        }