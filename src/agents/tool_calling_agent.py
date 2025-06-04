import time
from litellm import completion
from typing import List, Optional, Dict, Any

from src.agents.base import Agent
from src.envs.base import Env
from src.types import AgentRunResult
from src.utils import convert_message_to_action

TOOL_CALLING_INSTRUCTION = """
You are an advanced SQL‐generation agent specialized in Electronic Health Records (EHR). Your job is to take a user’s natural language request about patient data and produce a single, precise SQL query that will correctly retrieve exactly the records the user wants—no more, no less. To do this:

1. Clarify Ambiguities:
   - If any part of the user’s request is unclear (e.g., which lab test, code sets, date ranges, or patient attributes), ask exactly one follow‐up question in plain language before proceeding.

2. Discover Schema and Values:
   - Use `schema_inspector_tool`, `substring_search_tool`, or `value_inspector_tool` to inspect table/column names, data types, or valid values (e.g., ICD‐10 codes). 
   - **Only one tool call per response.** After calling the tool, stop your response. Wait for tool output before continuing.

3. No Fabrication:
   - Never assume table or column names, code sets, or relationships. Always confirm via tools or direct user clarification.

4. Construct Final SQL Query:
   - Once you have all necessary details, write one well-formed `SQL_QUERY:` that:
     • Selects the exact columns requested
     • Joins the necessary tables via proper keys
     • Applies all filters (date ranges, codes, numeric thresholds, demographics) exactly
     • Uses correct SQL syntax and column/table names as discovered
   - Do not include any commentary or partial SQL—output only one complete SQL statement.
"""

class ToolCallingAgent(Agent):
    def __init__(
        self,
        tools_info: List[Dict[str, Any]],
        rule: str,
        model: str,
        temperature: float = 0.0,
    ):
        self.tools_info = tools_info
        self.rule = rule
        self.model = model
        self.temperature = temperature
        self.instruction = TOOL_CALLING_INSTRUCTION + '\nRules:\n'+self.rule

    def run(
        self, env: Env, task_index: Optional[int] = None, max_num_steps: int = 30
    ) -> AgentRunResult:
        agent_cost = 0.0
        env_reset_res = env.reset(task_index=task_index)
        obs_user = env_reset_res.observation
        env_info = env_reset_res.info.model_dump()
        reward = 0.0
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": self.instruction},
            {"role": "user", "content": obs_user},
        ]
        for _ in range(max_num_steps):
            while True:
                try:
                    res = completion(
                        messages=messages,
                        model=self.model,
                        tools=self.tools_info,
                        temperature=self.temperature,
                    )
                    agent_cost += res._hidden_params["response_cost"]
                    break
                except Exception as e:
                    time.sleep(3)
                    print(e, end='\r')
            next_message = res.choices[0].message.model_dump()
            action = convert_message_to_action(next_message)
            env_response = env.step(action)
            reward = env_response.reward
            env_info = {**env_info, **env_response.info.model_dump()}
            if action.name != 'respond':
                next_message["tool_calls"] = next_message["tool_calls"][:1]
                messages.extend(
                    [
                        next_message,
                        {
                            "role": "tool",
                            "tool_call_id": next_message["tool_calls"][0]["id"],
                            "name": next_message["tool_calls"][0]["function"]["name"],
                            "content": env_response.observation,
                        },
                    ]
                )
            else:
                messages.extend(
                    [
                        next_message,
                        {"role": "user", "content": env_response.observation},
                    ]
                )
            if env_response.done:
                break

        return AgentRunResult(
            reward=reward,
            messages=messages,
            agent_cost=round(agent_cost, 8),
            info=env_info
        )

