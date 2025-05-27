import os
import json
from src.types import Task
from src.envs.base import Env
from src.envs.mimic_iv.tools.sql_db_list_tables import SqlDbListTables
from src.envs.mimic_iv.tools.sql_db_schema import SqlDbSchema
from src.envs.mimic_iv.tools.sql_db_query import SqlDbQuery
from src.envs.mimic_iv.tools.value_substring_search import ValueSubstringSearch
# Version 5: Consolidated tools for optimal performance
from src.envs.mimic_iv.tools.clinical_term_mapper import ClinicalTermMapper, QueryAnalyzer
from src.envs.mimic_iv.tools.smart_schema_assistant import SmartSchemaAssistant, QueryValidator
from src.envs.mimic_iv.tools.enhanced_query_optimizer import EnhancedQueryOptimizer, EnhancedExecutionHelper
from sqlalchemy import create_engine

FOLDER_PATH = os.path.dirname(__file__)

class MimicIVEnvV5(Env):
    """
    Version 5 of MIMIC-IV Environment with consolidated tools for optimal performance.
    Reduces tool complexity while maintaining all functionality.
    """
    def __init__(
        self,
        eval_mode: str,
        user_strategy: str,
        user_model: str,
        task_index: int,
        db_path: str = "src/envs/mimic_iv/mimic_iv.sqlite",
    ):
        assert os.path.exists(db_path), f"Database file does not exist: {db_path}"
        with open(os.path.join(FOLDER_PATH, f"{eval_mode}_data.json"), "r") as f:
            tasks = [Task(**kwargs) for kwargs in json.load(f)]
        with open(os.path.join(FOLDER_PATH, "rules.txt"), "r") as f:
            rule = f.read()
        engine = create_engine(f"sqlite:///{db_path}")
        
        # Core database tools
        sql_db_list_tables = SqlDbListTables(engine=engine)
        sql_db_schema = SqlDbSchema(engine=engine)
        sql_db_query = SqlDbQuery(engine=engine)
        value_substring_search = ValueSubstringSearch(engine=engine)
        
        # Version 5: Consolidated enhanced tools (6 total instead of 8)
        clinical_term_mapper = ClinicalTermMapper(engine=engine)
        query_analyzer = QueryAnalyzer(engine=engine)
        smart_schema_assistant = SmartSchemaAssistant(engine=engine)
        query_validator = QueryValidator(engine=engine)
        enhanced_query_optimizer = EnhancedQueryOptimizer(engine=engine)  # Replaces both query_optimizer and advanced_query_fixer
        enhanced_execution_helper = EnhancedExecutionHelper(engine=engine)  # Replaces both execution_helper and query_complexity_analyzer

        super().__init__(
            tools=[
                sql_db_list_tables,
                sql_db_schema,
                value_substring_search,
                sql_db_query,
                # Version 5: 6 optimized tools (down from 8)
                clinical_term_mapper,
                query_analyzer,
                smart_schema_assistant,
                query_validator,
                enhanced_query_optimizer,  # Consolidated: basic + advanced query optimization
                enhanced_execution_helper,  # Consolidated: execution strategies + complexity analysis
            ],
            tasks=tasks,
            user_strategy=user_strategy,
            user_model=user_model,
            db_path=db_path,
            task_index=task_index,
            rule=rule,
        ) 