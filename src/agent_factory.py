from typing import List, Dict, Any, Optional
from src.agents.base import Agent

def get_agent(
    tools_info: List[Dict[str, Any]],
    model: str,
    agent_strategy: str = "tool-calling",
    temperature: float = 0.0,
    rule: str = "",
    max_steps: int = 5,
) -> Agent:
    if agent_strategy == "tool-calling":
        from src.agents.tool_calling_agent import ToolCallingAgent
        return ToolCallingAgent(
            tools_info=tools_info,
            model=model,
            temperature=temperature,
            rule=rule,
        )
    elif agent_strategy == "dspy":
        from src.agents.dspy_agent import DSPyAgent
        return DSPyAgent(
            tools_info=tools_info,
            model=model,
            temperature=temperature,
            rule=rule,
            max_steps=max_steps,
        )
    else:
        # TODO: implement your own agent and return it here
        raise ValueError(f"Agent strategy {agent_strategy} not implemented. Erase this line after implementing your own agent.")
        from src.agents.TODO_implement_agent import TodoImplementAgent
        return TodoImplementAgent(
            model=model,
            temperature=temperature,
        )
        