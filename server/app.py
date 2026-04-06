try:
    from openenv.core.env_server.http_server import create_app
except Exception as e:
    raise ImportError(
        "openenv is required. Install with: pip install openenv-core"
    ) from e

from fastapi import Request
from fastapi.responses import JSONResponse
from uuid import uuid4
import json

from models import ComplianceAction, ComplianceObservation
from compliance_env_environment import ComplianceEnvironment, _GLOBAL_STATE, generate_scenario

app = create_app(
    ComplianceEnvironment,
    ComplianceAction,
    ComplianceObservation,
    env_name="compliance_env",
    max_concurrent_envs=1,
)

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/reset", include_in_schema=False)
async def reset_with_difficulty(request: Request):
    try:
        body = await request.json()
        difficulty = body.get("difficulty", None)
    except Exception:
        difficulty = None

    scenario = generate_scenario(difficulty)
    _GLOBAL_STATE["episode_id"] = str(uuid4())
    _GLOBAL_STATE["step_count"] = 0
    _GLOBAL_STATE["scenario"] = scenario
    _GLOBAL_STATE["extracted_clause_ids"] = []
    _GLOBAL_STATE["gap_items"] = []
    _GLOBAL_STATE["checklist"] = []
    _GLOBAL_STATE["max_steps"] = scenario["max_steps"]

    obs = ComplianceObservation(
        step=0,
        max_steps=scenario["max_steps"],
        message=f"[{scenario['difficulty'].upper()} TASK] New episode started. Read the regulation and company profile carefully. Start by extracting applicable clause IDs. {scenario['company_for_episode']['difficulty_hint']}",
        regulation_document=json.dumps(scenario["regulation"], indent=2),
        company_profile=scenario["company_for_episode"],
        episode_id=_GLOBAL_STATE["episode_id"],
        difficulty=scenario["difficulty"],
        extracted_clauses_so_far=[],
        gaps_found_so_far=[],
        partial_score=0.0,
        steps_remaining=scenario["max_steps"],
        done=False,
        reward=0.0,
    )
    return JSONResponse(content={
        "observation": obs.model_dump(),
        "reward": 0.0,
        "done": False
    })


def main(host: str = "0.0.0.0", port: int = 8000) -> None:
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()