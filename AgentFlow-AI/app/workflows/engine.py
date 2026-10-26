import time
from datetime import datetime, timezone
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from app.agents.data_agent import run_data_analysis_agent
from app.agents.email_agent import run_email_agent
from app.agents.general_agent import run_general_agent
from app.agents.research_agent import run_research_agent
from app.agents.supervisor import create_plan
from app.agents.text_analysis_agent import run_text_analysis_agent
from app.agents.weather_agent import run_weather_agent


class WorkflowState(TypedDict, total=False):
    user_goal: str
    plan: dict[str, Any]
    current_step: int
    results: list[dict[str, Any]]
    status: str
    error: str
    start_time: float
    duration_seconds: float
    approved_step_id: int | None


def plan_node(state: WorkflowState) -> dict:
    """Create a validated execution plan from the user's goal."""
    start_t = state.get("start_time") or time.time()
    plan = create_plan(state["user_goal"])

    return {
        "plan": plan,
        "current_step": 0,
        "results": [],
        "status": "planned",
        "start_time": start_t,
    }


def execute_step_node(state: WorkflowState) -> dict:
    """Execute one supported agent step and update workflow state."""
    plan = state["plan"]
    step_index = state.get("current_step", 0)
    steps = plan.get("steps", [])

    if step_index >= len(steps):
        duration = round(time.time() - state.get("start_time", time.time()), 3)
        return {
            "status": "completed",
            "duration_seconds": duration,
        }

    step = steps[step_index]
    step_id = step.get("step_id", step_index + 1)
    agent = step.get("agent")
    parameters = step.get("parameters", {})
    description = step.get("description", "")
    approved_step_id = state.get("approved_step_id")

    step_start = time.time()

    # If this step is email_agent and hasn't been approved yet:
    if agent == "email_agent" and approved_step_id != step_id:
        # Generate safe preview and transition to awaiting_approval
        preview_res = run_email_agent(parameters, approved=False)
        step_duration = round(time.time() - step_start, 3)

        step_result = {
            "step_id": step_id,
            "agent": agent,
            "description": description,
            "status": "awaiting_approval",
            "parameters": {
                "recipient": parameters.get("recipient", ""),
                "subject": parameters.get("subject", ""),
                "body_length": len(parameters.get("body", "")),
            },
            "result": preview_res,
            "duration_seconds": step_duration,
        }

        updated_results = state.get("results", []) + [step_result]
        total_duration = round(time.time() - state.get("start_time", time.time()), 3)

        return {
            "current_step": step_index,
            "results": updated_results,
            "status": "awaiting_approval",
            "duration_seconds": total_duration,
        }

    # Execute agent
    try:
        if agent == "weather_agent":
            result = run_weather_agent(parameters)
        elif agent == "text_analysis_agent":
            result = run_text_analysis_agent(parameters)
        elif agent == "general_agent":
            result = run_general_agent(parameters, context=state.get("results", []))
        elif agent == "email_agent":
            # Approved execution
            result = run_email_agent(parameters, approved=True)
        elif agent == "research_agent":
            result = run_research_agent(parameters)
        elif agent == "data_analysis_agent":
            result = run_data_analysis_agent(parameters)
        else:
            raise ValueError(f"Agent '{agent}' is not registered or supported.")

        step_duration = round(time.time() - step_start, 3)
        step_result = {
            "step_id": step_id,
            "agent": agent,
            "description": description,
            "status": "completed",
            "parameters": parameters,
            "result": result,
            "duration_seconds": step_duration,
        }

    except Exception as exc:
        step_duration = round(time.time() - step_start, 3)
        step_result = {
            "step_id": step_id,
            "agent": agent,
            "description": description,
            "status": "failed",
            "parameters": parameters,
            "result": {"error": str(exc)},
            "duration_seconds": step_duration,
        }
        updated_results = state.get("results", []) + [step_result]
        total_duration = round(time.time() - state.get("start_time", time.time()), 3)
        return {
            "current_step": step_index + 1,
            "results": updated_results,
            "status": "failed",
            "error": f"Step {step_id} ({agent}) failed: {exc}",
            "duration_seconds": total_duration,
        }

    updated_results = state.get("results", []) + [step_result]
    next_step = step_index + 1
    is_finished = next_step >= len(steps)
    total_duration = round(time.time() - state.get("start_time", time.time()), 3)

    return {
        "current_step": next_step,
        "results": updated_results,
        "status": "completed" if is_finished else "running",
        "duration_seconds": total_duration,
    }


def route_after_planning(state: WorkflowState) -> str:
    """Route after initial planning."""
    steps = state.get("plan", {}).get("steps", [])
    if not steps:
        return "finished"
    return "execute"


def route_after_execution(state: WorkflowState) -> str:
    """Check whether workflow should continue, stop for approval, or finish."""
    status = state.get("status")
    if status in ("awaiting_approval", "failed"):
        return "finished"

    steps = state.get("plan", {}).get("steps", [])
    if state.get("current_step", 0) >= len(steps):
        return "finished"

    return "execute"


def build_workflow():
    """Build and compile the LangGraph workflow."""
    graph = StateGraph(WorkflowState)

    graph.add_node("plan", plan_node)
    graph.add_node("execute", execute_step_node)

    graph.add_edge(START, "plan")

    graph.add_conditional_edges(
        "plan",
        route_after_planning,
        {
            "execute": "execute",
            "finished": END,
        },
    )

    graph.add_conditional_edges(
        "execute",
        route_after_execution,
        {
            "execute": "execute",
            "finished": END,
        },
    )

    return graph.compile()


workflow = build_workflow()


def run_workflow(
    user_goal: str,
    pre_plan: dict[str, Any] | None = None,
    approved_step_id: int | None = None,
    current_results: list[dict[str, Any]] | None = None,
    start_step_index: int = 0,
) -> dict[str, Any]:
    """Execute a workflow end-to-end or resume execution after approval."""
    if not isinstance(user_goal, str) or not user_goal.strip():
        raise ValueError("User goal cannot be empty.")

    start_time = time.time()

    initial_state: WorkflowState = {
        "user_goal": user_goal.strip(),
        "current_step": start_step_index,
        "results": current_results or [],
        "status": "starting",
        "start_time": start_time,
        "approved_step_id": approved_step_id,
    }

    if pre_plan:
        initial_state["plan"] = pre_plan

    # If plan is provided and we are resuming from an execution step
    if pre_plan and start_step_index > 0:
        # Run step execution loop directly
        current_state = initial_state
        while current_state.get("current_step", 0) < len(pre_plan.get("steps", [])):
            step_output = execute_step_node(current_state)
            current_state.update(step_output)
            if current_state.get("status") in ("awaiting_approval", "failed"):
                break
        final_state = current_state
    else:
        final_state = workflow.invoke(initial_state)

    plan = final_state.get("plan", pre_plan or {})
    total_duration = round(time.time() - start_time, 3)

    return {
        "goal": plan.get("goal", user_goal),
        "status": final_state.get("status", "unknown"),
        "plan": plan,
        "results": final_state.get("results", []),
        "duration_seconds": total_duration,
        "message": final_state.get("error", "Workflow execution completed."),
    }
