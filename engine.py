"""
Golden-Hour inference engine.

The knowledge (rules) lives in knowledge_base/rules.json.
This file only contains the reasoning machinery, so rules can be changed
without touching the code (knowledge base and inference engine are separate).

Three stages:
  1. needs   - forward chaining over patient and road facts
  2. filter  - every hospital is checked against the filter rules
  3. decide  - alerts for the dispatcher after ranking
"""
import json
import math
from pathlib import Path

BASE = Path(__file__).parent
ROAD_FACTOR = 1.4  # roads are longer than the straight-line distance


def load_rules(path=BASE / "knowledge_base" / "rules.json"):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_facility_names(path=BASE / "knowledge_base" / "facilities.json"):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ---------- condition checking ----------

def check(cond, facts):
    """Return True if one condition of a rule holds for the given facts."""
    value = facts.get(cond["fact"])
    op = cond["op"]
    target = facts.get(cond["value_fact"]) if "value_fact" in cond else cond.get("value")

    if op == "is_true":
        return value is True
    if op == "is_false":
        return value is False
    if op == "==":
        return value == target
    if op == "!=":
        return value != target
    if value is None:
        return False
    if op == ">":
        return value > target
    if op == "<":
        return value < target
    if op == ">=":
        return value >= target
    if op == "<=":
        return value <= target
    if op == "contains":
        return target in value
    if op == "not_empty":
        return len(value) > 0
    if op == "not_between":
        return not (target[0] <= value <= target[1])
    raise ValueError(f"Unknown operator {op}")


def rule_matches(rule, facts):
    return all(check(c, facts) for c in rule["if"])


def describe_rule(rule):
    """Readable IF ... THEN ... text for a rule."""
    parts = []
    for c in rule["if"]:
        op = c["op"]
        if op == "is_true":
            parts.append(f"{c['fact']} is yes")
        elif op == "is_false":
            parts.append(f"{c['fact']} is no")
        elif op == "not_empty":
            parts.append(f"{c['fact']} is not empty")
        elif op == "not_between":
            parts.append(f"{c['fact']} not between {c['value'][0]} and {c['value'][1]}")
        else:
            right = c.get("value_fact", c.get("value"))
            parts.append(f"{c['fact']} {op} {right}")
    acts = []
    for a in rule["then"]:
        if a["action"] == "add":
            acts.append(f"add {', '.join(a['value'])} to {a['fact']}")
        elif a["action"] == "set":
            acts.append(f"set {a['fact']} = {a['value']}")
        elif a["action"] == "reject":
            acts.append(f"reject hospital ({a['reason']})")
        elif a["action"] == "alert":
            acts.append(f"alert dispatcher")
    return "IF " + " AND ".join(parts) + " THEN " + " AND ".join(acts)


# ---------- stage 1: forward chaining ----------

def initial_facts(case):
    facts = {
        "needs": {"ER"},
        "severity": "Non-critical",
        "time_limit": 60,
        "speed_kmph": 25,
        "speed_factor": 1.0,
        "night": False,
    }
    facts.update(case)
    return facts


def forward_chain(facts, rules):
    """Fire rules until nothing new can be concluded.

    Conflict resolution: among all rules that match (the conflict set),
    the one with the highest priority fires first. Each rule fires only
    once (refraction), which also stops infinite loops.
    """
    stage_rules = [r for r in rules if r["stage"] == "needs"]
    fired, trace, cycle = set(), [], 0
    while True:
        conflict_set = [r for r in stage_rules if r["id"] not in fired and rule_matches(r, facts)]
        if not conflict_set:
            break
        conflict_set.sort(key=lambda r: (-r["priority"], r["id"]))
        rule = conflict_set[0]
        cycle += 1
        changes = []
        for a in rule["then"]:
            if a["action"] == "add":
                new = [v for v in a["value"] if v not in facts[a["fact"]]]
                facts[a["fact"]] |= set(a["value"])
                if new:
                    changes.append(f"{a['fact']} += {', '.join(new)}")
            elif a["action"] == "set":
                facts[a["fact"]] = a["value"]
                changes.append(f"{a['fact']} = {a['value']}")
        fired.add(rule["id"])
        trace.append({
            "cycle": cycle,
            "conflict_set": [r["id"] for r in conflict_set],
            "fired": rule["id"],
            "description": rule["description"],
            "changes": "; ".join(changes) if changes else "(no new fact)",
        })
    return facts, trace


# ---------- stage 2: hospital filtering and ranking ----------

def distance_km(lat1, lon1, lat2, lon2):
    """Straight-line (haversine) distance multiplied by a road factor."""
    r = 6371
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a)) * ROAD_FACTOR


def evaluate_hospitals(facts, hospitals, rules, incident_lat, incident_lon, names):
    filter_rules = sorted([r for r in rules if r["stage"] == "filter"], key=lambda r: -r["priority"])
    speed = facts["speed_kmph"] * facts["speed_factor"]
    results = []
    for h in hospitals:
        fac = set(h["facilities"].split(";"))
        missing = sorted(facts["needs"] - fac)
        ctx = dict(facts)
        ctx.update({
            "missing": missing,
            "icu_beds": int(h["icu_beds"]),
            "general_beds": int(h["general_beds"]),
            "open_24x7": bool(h["open_24x7"]),
            "on_diversion": bool(h["on_diversion"]),
        })
        reasons, fired = [], []
        for r in filter_rules:
            if rule_matches(r, ctx):
                for a in r["then"]:
                    if a["action"] == "reject":
                        reasons.append(a["reason"].format(missing=", ".join(names.get(m, m) for m in missing)))
                fired.append(r["id"])
        dist = distance_km(incident_lat, incident_lon, float(h["lat"]), float(h["lon"]))
        travel = dist / speed * 60
        total = travel + float(h["avg_wait_min"])
        results.append({
            "id": h["id"], "name": h["name"], "area": h["area"],
            "lat": float(h["lat"]), "lon": float(h["lon"]),
            "distance_km": round(dist, 1), "travel_min": round(travel), "wait_min": int(h["avg_wait_min"]),
            "total_min": round(total), "accepted": not reasons,
            "reasons": reasons, "rules_fired": fired, "icu_beds": int(h["icu_beds"]),
            "has_er": "ER" in fac, "has_icu": "ICU" in fac and int(h["icu_beds"]) > 0,
        })
    results.sort(key=lambda x: (not x["accepted"], x["total_min"]))
    return results


# ---------- stage 3: decision alerts ----------

def decide(facts, results, rules):
    accepted = [r for r in results if r["accepted"]]
    by_distance = sorted(results, key=lambda r: r["distance_km"])
    nearest_er = next((r["name"] for r in by_distance if r["has_er"]), "none")
    nearest_icu = next((r["name"] for r in by_distance if r["has_icu"]), "none")
    best = accepted[0] if accepted else None
    ctx = dict(facts)
    ctx.update({
        "accepted_count": len(accepted),
        "best_time": best["total_min"] if best else None,
        "best_name": best["name"] if best else None,
        "best_icu_beds": best["icu_beds"] if best else None,
        "nearest_er": nearest_er,
        "nearest_icu": nearest_icu,
    })
    alerts = []
    for r in sorted([r for r in rules if r["stage"] == "decide"], key=lambda r: -r["priority"]):
        if rule_matches(r, ctx):
            for a in r["then"]:
                alerts.append({"rule": r["id"], "level": a["level"], "message": a["message"].format(**ctx)})
    return best, alerts


def nearest_hospital(results):
    """Baseline method: just send the patient to the closest hospital."""
    return min(results, key=lambda r: r["distance_km"])


def run(case, hospitals, rules, incident_lat, incident_lon):
    """Full pipeline. Returns everything the app needs to show."""
    names = load_facility_names()
    facts, trace = forward_chain(initial_facts(case), rules)
    results = evaluate_hospitals(facts, hospitals, rules, incident_lat, incident_lon, names)
    best, alerts = decide(facts, results, rules)
    return {"facts": facts, "trace": trace, "results": results, "best": best,
            "alerts": alerts, "baseline": nearest_hospital(results)}
