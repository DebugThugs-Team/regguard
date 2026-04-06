# Compliance Environment (OpenEnv)

A reinforcement learning environment for training agents to do **regulatory compliance analysis** on Indian corporate regulations.

This project was built for the Meta × Scalar × HuggingFace OpenEnv Hackathon (April 2026) by **Team Regguard**:
- Riddhika Sachdeva
- Hemank Aggarwal
- Chinmay Nayar

In real compliance work, professionals read regulations, figure out what applies to a company, identify policy gaps, and turn that into an actionable checklist. This environment mirrors that workflow so you can benchmark LLM agents on structured, real-world document reasoning.


## Why This Domain for RL?

- **Non-trivial reasoning**: filter irrelevant clauses, map company attributes to applicability, and reason about gaps
- **Dense signal**: reward is given step-by-step (not only at the end)
- **Curriculum**: easy → medium → hard, with increasing information hiding
- **Deterministic scoring**: a fully programmatic reward function
- **Practical stakes**: compliance failures are expensive; getting this right matters


## Environment Overview

| Property | Value |
|---|---|
| Action Space | Discrete (3 action types) |
| Max Steps per Episode | 5—8 (depends on difficulty) |
| Reward Range | 0.0 — 1.0 |
| Regulations Covered | GST, SEBI LODR, RBI KYC, POSH Act |
| Companies | 5 companies across sectors |
| Difficulty Levels | Easy, Medium, Hard |


## Action Types

| Action | Description |
|---|---|
| `extract_clauses` | Extract applicable clause IDs from the regulation |
| `analyse_gap` | Analyse gaps between current company policy and regulation |
| `produce_checklist` | Produce a prioritised compliance remediation checklist |

Actions must be performed **in order**. Skipping steps incurs a penalty of -0.05.


## Observation Space

Each observation includes:

| Field | Type | Description |
|---|---|---|
| `regulation_document` | str | Full regulation text as JSON |
| `company_profile` | dict | Company details and current policies |
| `message` | str | Environment feedback with partial reward signal |
| `extracted_clauses_so_far` | list | Clauses extracted in current episode |
| `gaps_found_so_far` | list | Gap items recorded so far |
| `partial_score` | float | Running score after each step |
| `steps_remaining` | int | Steps left in episode |
| `difficulty` | str | Current episode difficulty |


## Reward Function

| Component | Weight | Description |
|---|---|---|
| Clause Recall | 40% | How many applicable clauses were correctly identified |
| Gap Analysis | 40% | How many real gaps were correctly identified with descriptions |
| Checklist Quality | 20% | Priority labels, clause references, and coverage |
| Efficiency Bonus | +5% | Completing in 3 steps or fewer |

Partial rewards are emitted at steps 1 and 2 — reward is **non-sparse**.

Penalties of -0.05 are applied for:
- Out-of-order actions
- Invalid JSON
- Unknown action types


## Difficulty Levels

| Level | Info Available | Max Steps | Challenge |
|---|---|---|---|
| Easy | Full company policies shown | 8 | Identify applicable clauses |
| Medium | Policies redacted | 6 | Infer gaps from context |
| Hard | No policy info | 5 | Assume worst case, identify all gaps |


## Tasks

### Task 1 — Clause Extraction (Easy)
Extract the applicable clause IDs for the given company. Scored on recall, with a penalty for false positives.

### Task 2 — Gap Analysis (Medium)
Describe how the company’s current policies fall short of the requirements. Scored on matched gaps, with a lightweight keyword check to ensure real “gap language”.

### Task 3 — Checklist Generation (Hard)
Produce a prioritised remediation checklist that covers all extracted clauses, with correct clause references and priority levels.


## Scenarios

The environment randomly pairs one of **4 regulations** with one of **5 companies**:

**Regulations:**
- GST Amendment Circular 2024
- SEBI LODR Amendment 2024
- RBI KYC Master Direction 2024
- POSH Act Compliance 2024

**Companies:**
- Sharma Enterprises Pvt Ltd (Manufacturing, Medium)
- Veritas Technologies Ltd (IT Services, Large, Listed)
- BlueSky Retail Pvt Ltd (Retail, Small)
- Indus Financial Services Ltd (NBFC, Large, Listed)
- GreenLeaf Agro Pvt Ltd (Agriculture, Medium)


## Quickstart

### Run with Docker

```bash
docker build -t compliance-env .
docker run -p 8000:8000 compliance-env
```

### Run locally

```bash
pip install -e .
cd server
PYTHONPATH=/path/to/compliance_env uvicorn app:app --host 0.0.0.0 --port 8000
```

### Test the environment

Reset:

```bash
curl -X POST http://localhost:8000/reset
```

Step:

```bash
curl -X POST http://localhost:8000/step \
  -H "Content-Type: application/json" \
  -d '{"action": {"action_type": "extract_clauses", "content": "GST-4(2)(a), GST-9(1)"}}'
```

Health check:

```bash
curl http://localhost:8000/health
```

### Run the example agent

```bash
export HF_TOKEN=your_token
export API_BASE_URL=https://router.huggingface.co/v1
export MODEL_NAME=Qwen/Qwen2.5-72B-Instruct
python3 inference.py
```


## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/reset` | POST | Start a new episode |
| `/step` | POST | Execute an action |
| `/state` | GET | Get current environment state |
| `/schema` | GET | Get action/observation schemas |
| `/health` | GET | Health check |


## Baseline Scores

| Task | Difficulty | Baseline Score |
|---|---|---|
| Clause Extraction | Easy | 0.40 |
| Gap Analysis | Medium | 0.40 |
| Checklist Generation | Hard | 0.20 |
| **Average** | — | **0.68** |


## Model Benchmark

Results from running `inference.py` against the live deployed environment:

| Model | Provider | Final Score | Behaviour |
|---|---|---|---|
| Qwen 2.5 72B Instruct | Hugging Face | 1.000 | Perfect — correct clause extraction, gap analysis and checklist in 3 steps |
| Llama 3.3 70B Versatile | Groq | 0.400 | Correct clause extraction but stuck in loop at step 2 |

The variance here is intentional: the environment should separate agents that reliably follow instructions and structure from those that don’t. A perfect score requires correct clause applicability, gap descriptions that clearly signal non-compliance, and a checklist that references the extracted clauses — all in the right order.

## Built With

- [OpenEnv](https://github.com/meta-llama/openenv) — RL environment framework
- FastAPI + Uvicorn — HTTP server
- Pydantic — schema validation