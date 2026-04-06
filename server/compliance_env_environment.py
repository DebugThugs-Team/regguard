from uuid import uuid4
import json
import random

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

from models import ComplianceAction, ComplianceObservation


REGULATIONS = [
    {
        "name": "GST Amendment Circular 2024",
        "clauses": [
            {"clause_id": "GST-4(2)(a)", "text": "Every registered taxpayer must file GSTR-1 monthly if turnover exceeds 5 crore.", "applicable_to": ["large", "medium"]},
            {"clause_id": "GST-4(2)(b)", "text": "Quarterly filing permitted for businesses with turnover below 5 crore.", "applicable_to": ["small"]},
            {"clause_id": "GST-9(1)", "text": "Annual return must be filed by 31st December of the following financial year.", "applicable_to": ["large", "medium", "small"]},
            {"clause_id": "GST-16(4)", "text": "Input tax credit must be reconciled within 30 days of invoice date.", "applicable_to": ["large", "medium"]},
            {"clause_id": "GST-IRRELEVANT-1", "text": "Export businesses must file LUT before making zero-rated supplies.", "applicable_to": ["export_only"]},
        ]
    },
    {
        "name": "SEBI LODR Amendment 2024",
        "clauses": [
            {"clause_id": "LODR-27(2)", "text": "Listed entities must submit quarterly compliance report within 21 days of quarter end.", "applicable_to": ["listed"]},
            {"clause_id": "LODR-33(3)", "text": "Financial results must be submitted within 45 days of quarter end.", "applicable_to": ["listed"]},
            {"clause_id": "LODR-46(2)", "text": "Website must contain updated contact details of grievance redressal officer.", "applicable_to": ["listed"]},
            {"clause_id": "LODR-IRRELEVANT-1", "text": "SME listed entities follow a separate compliance calendar.", "applicable_to": ["sme_listed"]},
        ]
    },
    {
        "name": "RBI KYC Master Direction 2024",
        "clauses": [
            {"clause_id": "KYC-8(1)", "text": "Customer identity must be verified before onboarding using OVDs.", "applicable_to": ["large", "medium", "small"]},
            {"clause_id": "KYC-11(2)", "text": "Periodic KYC update must be done every 2 years for high-risk customers.", "applicable_to": ["large", "medium"]},
            {"clause_id": "KYC-16(1)", "text": "Suspicious transaction reports must be filed within 7 days of detection.", "applicable_to": ["large", "medium", "small"]},
            {"clause_id": "KYC-IRRELEVANT-1", "text": "Foreign portfolio investors follow separate KYC norms under SEBI.", "applicable_to": ["fpi_only"]},
        ]
    },
    {
        "name": "POSH Act Compliance 2024",
        "clauses": [
            {"clause_id": "POSH-4(1)", "text": "Every organisation with 10 or more employees must constitute an Internal Complaints Committee.", "applicable_to": ["large", "medium"]},
            {"clause_id": "POSH-19(a)", "text": "Annual report on ICC activities must be submitted to district officer.", "applicable_to": ["large", "medium"]},
            {"clause_id": "POSH-19(b)", "text": "Awareness programs on POSH must be conducted at least once a year.", "applicable_to": ["large", "medium", "small"]},
            {"clause_id": "POSH-IRRELEVANT-1", "text": "Domestic workers are covered under local complaints committee only.", "applicable_to": ["domestic_only"]},
        ]
    }
]

COMPANIES = [
    {
        "name": "Sharma Enterprises Pvt Ltd",
        "sector": "Manufacturing",
        "size": "medium",
        "listed": False,
        "turnover_crore": 12,
        "current_policies": {
            "GST-4(2)(a)": "Files GSTR-1 quarterly, not monthly",
            "GST-9(1)": "Files annual return on time",
            "GST-16(4)": "Reconciles ITC within 45 days",
            "KYC-8(1)": "Verifies identity using OVDs before onboarding",
            "KYC-11(2)": "No periodic KYC update process in place",
            "KYC-16(1)": "Files STR within 7 days",
            "POSH-4(1)": "ICC constituted with 5 members",
            "POSH-19(a)": "Annual report not submitted to district officer",
            "POSH-19(b)": "No annual awareness program conducted",
        }
    },
    {
        "name": "Veritas Technologies Ltd",
        "sector": "IT Services",
        "size": "large",
        "listed": True,
        "turnover_crore": 850,
        "current_policies": {
            "LODR-27(2)": "Submits compliance report within 30 days",
            "LODR-33(3)": "Submits financial results within 45 days",
            "LODR-46(2)": "Website does not have grievance officer details updated",
            "GST-4(2)(a)": "Files GSTR-1 monthly",
            "GST-9(1)": "Files annual return on time",
            "GST-16(4)": "Reconciles ITC within 30 days",
            "KYC-8(1)": "Verifies identity using OVDs before onboarding",
            "KYC-11(2)": "Periodic KYC update done every 3 years",
            "KYC-16(1)": "Files STR within 7 days",
            "POSH-4(1)": "ICC constituted with 5 members",
            "POSH-19(a)": "Annual report submitted on time",
            "POSH-19(b)": "Annual awareness program conducted",
        }
    },
    {
        "name": "BlueSky Retail Pvt Ltd",
        "sector": "Retail",
        "size": "small",
        "listed": False,
        "turnover_crore": 3,
        "current_policies": {
            "GST-4(2)(b)": "Files GSTR-1 quarterly",
            "GST-9(1)": "Annual return filed late by 2 months",
            "KYC-8(1)": "Customer identity verified informally, no OVD process",
            "KYC-16(1)": "No STR filing process in place",
            "POSH-19(b)": "No awareness program conducted",
        }
    },
    {
        "name": "Indus Financial Services Ltd",
        "sector": "NBFC",
        "size": "large",
        "listed": True,
        "turnover_crore": 1200,
        "current_policies": {
            "LODR-27(2)": "Submits compliance report within 21 days",
            "LODR-33(3)": "Submits financial results within 45 days",
            "LODR-46(2)": "Website has updated grievance officer details",
            "GST-4(2)(a)": "Files GSTR-1 monthly",
            "GST-9(1)": "Files annual return on time",
            "GST-16(4)": "Reconciles ITC within 30 days",
            "KYC-8(1)": "Verifies identity using OVDs before onboarding",
            "KYC-11(2)": "No periodic KYC update for high-risk customers",
            "KYC-16(1)": "Files STR within 10 days",
            "POSH-4(1)": "ICC constituted with 5 members",
            "POSH-19(a)": "Annual report not submitted to district officer",
            "POSH-19(b)": "Annual awareness program conducted",
        }
    },
    {
        "name": "GreenLeaf Agro Pvt Ltd",
        "sector": "Agriculture",
        "size": "medium",
        "listed": False,
        "turnover_crore": 28,
        "current_policies": {
            "GST-4(2)(a)": "Files GSTR-1 monthly",
            "GST-9(1)": "Files annual return on time",
            "GST-16(4)": "Reconciles ITC within 30 days",
            "KYC-8(1)": "Verifies identity using OVDs before onboarding",
            "KYC-11(2)": "Periodic KYC update done every 2 years",
            "KYC-16(1)": "Files STR within 7 days",
            "POSH-4(1)": "No ICC constituted",
            "POSH-19(a)": "No annual report submitted",
            "POSH-19(b)": "No awareness program conducted",
        }
    }
]


def generate_scenario(difficulty: str = None):
    if difficulty is None:
        difficulty = random.choice(["easy", "medium", "hard"])

    max_attempts = 10
    for _ in range(max_attempts):
        regulation = random.choice(REGULATIONS)
        company = random.choice(COMPANIES)

        applicable_ids = []
        for clause in regulation["clauses"]:
            if company["size"] in clause["applicable_to"] or \
               (company.get("listed") and "listed" in clause["applicable_to"]):
                applicable_ids.append(clause["clause_id"])

        if not applicable_ids:
            continue

        ground_truth_gaps = []
        for cid in applicable_ids:
            current = company["current_policies"].get(cid, "No existing policy found")
            clause_text = next(c["text"] for c in regulation["clauses"] if c["clause_id"] == cid)
            ground_truth_gaps.append({
                "clause_id": cid,
                "current_state": current,
                "required_state": clause_text,
                "is_gap": current != clause_text
            })

        if difficulty == "easy":
            visible_policies = company["current_policies"]
            hint = "Hint: Focus only on the first applicable clause you find."
            max_steps = 8
        elif difficulty == "medium":
            visible_policies = {k: "Policy exists but details not disclosed" for k in company["current_policies"]}
            hint = "Current policy details are partially redacted. Infer gaps from context."
            max_steps = 6
        else:
            visible_policies = {}
            hint = "No existing policy information available. Assume no policies exist unless stated."
            max_steps = 5

        company_for_episode = dict(company)
        company_for_episode["current_policies"] = visible_policies
        company_for_episode["difficulty_hint"] = hint

        return {
            "id": str(uuid4()),
            "regulation": regulation,
            "company": company,
            "company_for_episode": company_for_episode,
            "applicable_clause_ids": applicable_ids,
            "ground_truth_gaps": ground_truth_gaps,
            "difficulty": difficulty,
            "max_steps": max_steps,
        }

    return generate_scenario(difficulty)


_GLOBAL_STATE = {
    "episode_id": None,
    "step_count": 0,
    "max_steps": 8,
    "scenario": None,
    "extracted_clause_ids": [],
    "gap_items": [],
    "checklist": [],
}


class ComplianceEnvironment(Environment):
    SUPPORTS_CONCURRENT_SESSIONS: bool = False

    def __init__(self):
        pass

    def reset(self, difficulty: str = None) -> ComplianceObservation:
        scenario = generate_scenario(difficulty)
        _GLOBAL_STATE["episode_id"] = str(uuid4())
        _GLOBAL_STATE["step_count"] = 0
        _GLOBAL_STATE["scenario"] = scenario
        _GLOBAL_STATE["extracted_clause_ids"] = []
        _GLOBAL_STATE["gap_items"] = []
        _GLOBAL_STATE["checklist"] = []
        _GLOBAL_STATE["max_steps"] = scenario["max_steps"]

        return ComplianceObservation(
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

    def step(self, action: ComplianceAction) -> ComplianceObservation:
        if _GLOBAL_STATE["step_count"] >= _GLOBAL_STATE.get("max_steps", 8):
            reward = self._compute_reward()
            return ComplianceObservation(
                step=_GLOBAL_STATE["step_count"],
                max_steps=_GLOBAL_STATE.get("max_steps", 8),
                message=f"Max steps reached. Final reward: {reward:.3f}",
                done=True,
                reward=reward,
            )

        _GLOBAL_STATE["step_count"] += 1
        step = _GLOBAL_STATE["step_count"]

        if action.action_type == "extract_clauses":
            extracted = [c.strip() for c in action.content.split(",") if c.strip()]
            _GLOBAL_STATE["extracted_clause_ids"] = extracted

            ground_truth_ids = _GLOBAL_STATE["scenario"]["applicable_clause_ids"]
            correct = [cid for cid in extracted if cid in ground_truth_ids]
            false_positives = [cid for cid in extracted if cid not in ground_truth_ids]
            recall = len(correct) / max(len(ground_truth_ids), 1)
            partial_reward = round(max(0.0, 0.4 * recall - 0.02 * len(false_positives)), 4)

            return ComplianceObservation(
                step=step,
                max_steps=_GLOBAL_STATE.get("max_steps", 8),
                message=f"Clauses recorded: {extracted}. Partial reward: {partial_reward:.3f}. Now analyse the gaps between current company policy and what the regulation requires. Respond with a JSON array.",
                difficulty=_GLOBAL_STATE["scenario"]["difficulty"],
                extracted_clauses_so_far=extracted,
                gaps_found_so_far=[],
                partial_score=partial_reward,
                steps_remaining=_GLOBAL_STATE.get("max_steps", 8) - step,
                done=False,
                reward=partial_reward,
            )

        elif action.action_type == "analyse_gap":
            if not _GLOBAL_STATE["extracted_clause_ids"]:
                return ComplianceObservation(
                    step=step,
                    max_steps=_GLOBAL_STATE.get("max_steps", 8),
                    message="You must extract clauses first before analysing gaps. Use extract_clauses action.",
                    done=False,
                    reward=-0.05,
                )
            try:
                gaps = json.loads(action.content)
                _GLOBAL_STATE["gap_items"] = gaps

                ground_truth_gaps = _GLOBAL_STATE["scenario"]["ground_truth_gaps"]
                matched = 0
                for gap in gaps:
                    cid = gap.get("clause_id", "")
                    desc = gap.get("gap_description", "").lower()
                    gt = next((g for g in ground_truth_gaps if g["clause_id"] == cid), None)
                    if gt and gt["is_gap"]:
                        keywords = ["not", "missing", "no", "fail", "delay", "incorrect"]
                        if any(k in desc for k in keywords):
                            matched += 1
                gap_partial = round(0.4 * matched / max(len(ground_truth_gaps), 1), 4)

                return ComplianceObservation(
                    step=step,
                    max_steps=_GLOBAL_STATE.get("max_steps", 8),
                    message=f"Gap analysis recorded. Partial reward: {gap_partial:.3f}. Now produce a prioritised compliance checklist as a JSON array with fields: action, priority (high/medium/low), clause_reference.",
                    difficulty=_GLOBAL_STATE["scenario"]["difficulty"],
                    extracted_clauses_so_far=_GLOBAL_STATE["extracted_clause_ids"],
                    gaps_found_so_far=gaps,
                    partial_score=gap_partial,
                    steps_remaining=_GLOBAL_STATE.get("max_steps", 8) - step,
                    done=False,
                    reward=gap_partial,
                )
            except Exception as e:
                return ComplianceObservation(
                    step=step,
                    max_steps=_GLOBAL_STATE.get("max_steps", 8),
                    message=f"Gap analysis JSON invalid: {str(e)}. Try again with valid JSON array.",
                    done=False,
                    reward=-0.05,
                )

        elif action.action_type == "produce_checklist":
            if not _GLOBAL_STATE["gap_items"]:
                return ComplianceObservation(
                    step=step,
                    max_steps=_GLOBAL_STATE.get("max_steps", 8),
                    message="You must analyse gaps before producing a checklist. Use analyse_gap action.",
                    done=False,
                    reward=-0.05,
                )
            try:
                checklist = json.loads(action.content)
                _GLOBAL_STATE["checklist"] = checklist
            except Exception as e:
                return ComplianceObservation(
                    step=step,
                    max_steps=_GLOBAL_STATE.get("max_steps", 8),
                    message=f"Checklist JSON invalid: {str(e)}",
                    done=True,
                    reward=0.0,
                )

            reward = self._compute_reward()
            return ComplianceObservation(
                step=step,
                max_steps=_GLOBAL_STATE.get("max_steps", 8),
                message=f"Episode complete. Final reward: {reward:.3f}",
                difficulty=_GLOBAL_STATE["scenario"]["difficulty"],
                extracted_clauses_so_far=_GLOBAL_STATE["extracted_clause_ids"],
                gaps_found_so_far=_GLOBAL_STATE["gap_items"],
                partial_score=reward,
                steps_remaining=0,
                done=True,
                reward=reward,
            )

        return ComplianceObservation(
            step=step,
            max_steps=_GLOBAL_STATE.get("max_steps", 8),
            message=f"Unknown action type: {action.action_type}. Valid types: extract_clauses, analyse_gap, produce_checklist.",
            done=False,
            reward=-0.05,
        )

    def _compute_reward(self) -> float:
        scenario = _GLOBAL_STATE["scenario"]
        if not scenario:
            return 0.0

        ground_truth_ids = scenario["applicable_clause_ids"]
        ground_truth_gaps = scenario["ground_truth_gaps"]
        extracted = _GLOBAL_STATE["extracted_clause_ids"]
        gap_items = _GLOBAL_STATE["gap_items"]
        checklist = _GLOBAL_STATE["checklist"]
        step_count = _GLOBAL_STATE["step_count"]

        correct = [cid for cid in extracted if cid in ground_truth_ids]
        false_positives = [cid for cid in extracted if cid not in ground_truth_ids]
        recall = len(correct) / max(len(ground_truth_ids), 1)
        clause_score = max(0.0, recall - 0.05 * len(false_positives))

        gap_score = 0.0
        if gap_items:
            matched = 0
            for gap in gap_items:
                cid = gap.get("clause_id", "")
                desc = gap.get("gap_description", "").lower()
                gt = next((g for g in ground_truth_gaps if g["clause_id"] == cid), None)
                if gt and gt["is_gap"]:
                    keywords = ["not", "missing", "no", "fail", "delay", "incorrect"]
                    if any(k in desc for k in keywords):
                        matched += 1
            gap_score = matched / max(len(ground_truth_gaps), 1)

        checklist_score = 0.0
        if checklist:
            high_priority = [i for i in checklist if i.get("priority") == "high"]
            has_refs = all(i.get("clause_reference") for i in checklist)
            covered = set(i.get("clause_reference") for i in checklist if i.get("clause_reference"))
            coverage_score = len(covered) / max(len(ground_truth_ids), 1)
            checklist_score = 0.5 * coverage_score
            if has_refs:
                checklist_score += 0.2
            if len(high_priority) > 0:
                checklist_score += 0.3
            checklist_score = min(1.0, checklist_score)

        bonus = 0.05 if step_count <= 3 else (0.02 if step_count <= 5 else 0.0)

        reward = (0.4 * clause_score) + (0.4 * gap_score) + (0.2 * checklist_score) + bonus
        return round(max(0.0, min(1.0, reward)), 4)

    @property
    def state(self) -> State:
        return State(episode_id=_GLOBAL_STATE["episode_id"], step_count=_GLOBAL_STATE["step_count"])