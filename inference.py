import asyncio
import json
import os
import textwrap
from typing import List, Optional

import requests
from openai import OpenAI

HF_TOKEN = os.getenv("HF_TOKEN")
API_KEY = HF_TOKEN or os.getenv("API_KEY")
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
ENV_BASE_URL = os.getenv("ENV_BASE_URL", "http://localhost:8000")
TASK_NAME = os.getenv("COMPLIANCE_TASK", "compliance-analysis")
BENCHMARK = os.getenv("COMPLIANCE_BENCHMARK", "compliance_env")
MAX_STEPS = 8
TEMPERATURE = 0.2
MAX_TOKENS = 1024
SUCCESS_SCORE_THRESHOLD = 0.1

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    action_safe = action.replace("\n", " ").replace("\r", " ")[:120]
    print(f"[STEP] step={step} action={action_safe} reward={reward:.2f} done={done_val} error={error_val}", flush=True)

def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)

SYSTEM_PROMPT = textwrap.dedent("""
    You are a regulatory compliance analysis agent.
    Complete the analysis in exactly 3 steps.

    STEP 1 — extract_clauses:
    Identify which clause IDs apply to this company based on size and listed status.
    Ignore clauses with applicable_to values that don't match the company.
    Respond with ONLY: {"action_type": "extract_clauses", "content": "CLAUSE-1, CLAUSE-2"}

    STEP 2 — analyse_gap:
    Compare each applicable clause to company's current policies.
    IMPORTANT: Your gap_description MUST use words like: not, missing, no, fail, incorrect, delay.
    Example: "Company does not comply", "Policy is missing", "Fails to meet requirement"
    Respond with ONLY: {"action_type": "analyse_gap", "content": "[{\"clause_id\": \"X\", \"current_state\": \"...\", \"required_state\": \"...\", \"gap_description\": \"Company does not meet requirement because...\"}]"}

    STEP 3 — produce_checklist:
    Produce prioritised remediation checklist covering ALL extracted clauses.
    Every item must have a valid clause_reference matching an extracted clause ID.
    Mark urgent gaps as high priority.
    Respond with ONLY: {"action_type": "produce_checklist", "content": "[{\"action\": \"...\", \"priority\": \"high|medium|low\", \"clause_reference\": \"...\"}]"}

    Always respond with valid JSON only. No explanation, no preamble, no markdown.
""").strip()

def env_reset():
    r = requests.post(f"{ENV_BASE_URL}/reset", timeout=30)
    r.raise_for_status()
    return r.json()

def env_step(action_type: str, content: str):
    r = requests.post(f"{ENV_BASE_URL}/step", json={
        "action": {"action_type": action_type, "content": content}
    }, timeout=30)
    r.raise_for_status()
    return r.json()

def get_model_action(client: OpenAI, obs: dict, history: List[str]) -> dict:
    regulation = obs.get("regulation_document") or ""
    company = obs.get("company_profile") or {}
    message_text = obs.get("message", "")
    history_block = "\n".join(history[-4:]) if history else "None"

    user_prompt = textwrap.dedent(f"""
        REGULATION:
        {regulation}

        COMPANY PROFILE:
        {json.dumps(company, indent=2)}

        ENVIRONMENT MESSAGE: {message_text}

        PREVIOUS STEPS:
        {history_block}

        Respond with the next action JSON only.
    """).strip()

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            stream=False,
        )
        text = (completion.choices[0].message.content or "").strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text.strip())
    except Exception as exc:
        print(f"[DEBUG] Model request failed: {exc}", flush=True)
        return {"action_type": "extract_clauses", "content": ""}

TASKS = [
    {"name": "easy-compliance", "difficulty": "easy"},
    {"name": "medium-compliance", "difficulty": "medium"},
    {"name": "hard-compliance", "difficulty": "hard"},
]

def env_reset_with_difficulty(difficulty: str):
    r = requests.post(
        f"{ENV_BASE_URL}/reset",
        json={"difficulty": difficulty},
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    r.raise_for_status()
    return r.json()

async def run_episode(client: OpenAI, task: dict) -> float:
    difficulty = task["difficulty"]
    task_name = task["name"]
    max_steps = {"easy": 8, "medium": 6, "hard": 5}[difficulty]

    history: List[str] = []
    rewards: List[float] = []
    steps_taken = 0
    score = 0.0
    success = False

    log_start(task=task_name, env=BENCHMARK, model=MODEL_NAME)

    try:
        result = env_reset_with_difficulty(difficulty)
        obs = result["observation"]
        done = result.get("done", False)

        for step in range(1, max_steps + 1):
            if done:
                break

            action_dict = get_model_action(client, obs, history)
            action_type = action_dict.get("action_type", "extract_clauses")
            content = action_dict.get("content", "")

            try:
                result = env_step(action_type, content)
                obs = result["observation"]
                reward = float(result.get("reward", 0.0))
                done = result.get("done", False)
                error = None
            except Exception as e:
                reward = 0.0
                done = True
                error = str(e)

            rewards.append(reward)
            steps_taken = step
            log_step(step=step, action=f"{action_type}:{content[:80]}", reward=reward, done=done, error=error)
            history.append(f"Step {step}: {action_type} -> reward {reward:+.2f}")

            if done:
                break

        score = max(rewards) if rewards else 0.0
        score = min(max(score, 0.0), 1.0)
        success = score >= SUCCESS_SCORE_THRESHOLD

    finally:
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

    return score

async def main() -> None:
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    all_scores = []

    for task in TASKS:
        score = await run_episode(client, task)
        all_scores.append(score)

    print(f"\n=== FINAL RESULTS ===", flush=True)
    for task, score in zip(TASKS, all_scores):
        print(f"{task['name']}: {score:.3f}", flush=True)
    print(f"Average: {sum(all_scores)/len(all_scores):.3f}", flush=True)

if __name__ == "__main__":
    asyncio.run(main())