import os
import json
from src.types import Task
from src.envs.base import Env
from src.envs.mimic_iv.tools.sql_db_list_tables import SqlDbListTables
from src.envs.mimic_iv.tools.sql_db_schema import SqlDbSchema
from src.envs.mimic_iv.tools.sql_db_query import SqlDbQuery
from src.envs.mimic_iv.tools.value_substring_search import ValueSubstringSearch
# Enhanced tools for better EHR SQL generation
from src.envs.mimic_iv.tools.schema_inspector import SchemaInspector
from src.envs.mimic_iv.tools.value_inspector import ValueInspector
from src.envs.mimic_iv.tools.relationship_discovery import RelationshipDiscovery
from src.envs.mimic_iv.tools.user_interrogator import UserInterrogator
from sqlalchemy import create_engine

FOLDER_PATH = os.path.dirname(__file__)

class MimicIVEnv(Env):
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
        
        # Initialize existing tools
        sql_db_list_tables = SqlDbListTables(engine=engine)
        sql_db_schema = SqlDbSchema(engine=engine)
        sql_db_query = SqlDbQuery(engine=engine)
        value_substring_search = ValueSubstringSearch(engine=engine)
        
        # Initialize enhanced tools
        schema_inspector = SchemaInspector(engine=engine)
        value_inspector = ValueInspector(engine=engine)
        relationship_discovery = RelationshipDiscovery(engine=engine)
        user_interrogator = UserInterrogator()

        super().__init__(
            tools=[
                sql_db_list_tables,
                sql_db_schema,
                value_substring_search,
                sql_db_query,
                # Enhanced tools for better EHR SQL generation
                schema_inspector,
                value_inspector,
                relationship_discovery,
                user_interrogator,
            ],
            tasks=tasks,
            user_strategy=user_strategy,
            user_model=user_model,
            db_path=db_path,
            task_index=task_index,
            rule=rule,
        )
