import json, re

FIELDS = ["test_case_id","requirement","title","preconditions","steps","test_data","expected_result","test_type","priority","status"]

def _clean_json(text):
    text = re.sub(r"^```(?:json)?\s*", "", text.strip())
    text = re.sub(r"\s*```$", "", text)
    start, end = text.find("["), text.rfind("]")
    if start >= 0 and end > start:
        text = text[start:end+1]
    return text

def generate_test_cases(requirements, count, types, api_key, model_name):
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)
    prompt = f"""
You are a senior software QA engineer. Generate exactly {count} distinct, actionable test cases
based only on the supplied requirements. Include these test types where applicable: {types}.
Cover positive, negative, boundary, validation, error handling, and security cases when relevant.
Do not invent product behavior; label uncertain assumptions in preconditions.
Return ONLY a valid JSON array. Every object must contain these string fields:
{FIELDS}
For steps, use numbered steps in a single string. Use priority Critical, High, Medium, or Low.
Use status "Not Run". Make requirement traceability explicit in the requirement field.
Requirements:
{requirements[:18000]}
"""
    response = model.generate_content(prompt, generation_config={"temperature": 0.2})
    data = json.loads(_clean_json(response.text))
    if not isinstance(data, list):
        raise ValueError("Model did not return a JSON array")
    normalized = []
    for i, item in enumerate(data[:count], 1):
        row = {k: str(item.get(k, "")) for k in FIELDS}
        row["test_case_id"] = row["test_case_id"] or f"TC-{i:03d}"
        row["status"] = row["status"] or "Not Run"
        row["test_type"] = row["test_type"] or "Functional"
        row["priority"] = row["priority"] if row["priority"] in ["Critical","High","Medium","Low"] else "Medium"
        normalized.append(row)
    if not normalized:
        raise ValueError("No test cases returned")
    return normalized

def demo_test_cases(requirements, count, types):
    # Deterministic fallback for demos without external API calls.
    snippets = [s.strip(" -*\t") for s in re.split(r"[\n.;]+", requirements) if len(s.strip()) > 12]
    base = snippets or ["Application requirement"]
    scenarios = [
        ("Positive", "Verify valid input is accepted", "Provide valid input and submit", "The application accepts the valid input and displays the expected outcome.", "High"),
        ("Negative", "Verify invalid input is handled", "Provide invalid input and submit", "The application rejects the input with a clear validation message and no unintended change.", "High"),
        ("Boundary", "Verify minimum and maximum boundaries", "Test values at, below, and above documented limits", "Boundary values follow the documented business rules.", "Medium"),
        ("Functional", "Verify the main business flow", "Complete the documented user flow", "The flow completes according to the requirement.", "Critical"),
        ("Regression", "Verify existing behavior remains intact", "Repeat the main flow after a change", "Previously working behavior remains unchanged.", "Medium"),
        ("Security", "Verify unauthorized access is blocked", "Attempt the action without required authorization", "Access is denied and no protected data is exposed.", "Critical"),
        ("Usability", "Verify validation guidance is understandable", "Trigger a validation error", "The message explains the issue and next step clearly.", "Low"),
    ]
    selected = [s for s in scenarios if not types or s[0] in types]
    if not selected: selected = scenarios[:]
    cases = []
    for i in range(count):
        req = base[i % len(base)]
        typ, title, steps, expected, priority = selected[i % len(selected)]
        cases.append({
            "test_case_id": f"TC-{i+1:03d}", "requirement": req[:240],
            "title": title, "preconditions": "Test environment is available; use synthetic test data.",
            "steps": f"1. Review requirement: {req[:180]}\n2. {steps}.",
            "test_data": "Valid, invalid, and boundary data as applicable; do not use production PII.",
            "expected_result": expected, "test_type": typ, "priority": priority, "status": "Not Run"
        })
    return cases

def analyze_coverage(requirements, cases):
    reqs = [s.strip(" -*\t") for s in re.split(r"[\n.;]+", requirements) if len(s.strip()) > 15]
    # Ignore common stop words; match distinctive tokens to reduce false matches.
    stop = {"that","this","with","from","have","will","when","then","user","system","must","should","shall","into","only","also","they","their","and","for","the","are","can","not","all"}
    def tokens(text):
        return {w.lower() for w in re.findall(r"[A-Za-z0-9_]{3,}", str(text)) if w.lower() not in stop}
    case_texts = [tokens(" ".join(str(v) for v in c.values())) for c in cases]
    covered, gaps = 0, []
    for req in reqs:
        rt = tokens(req)
        if not rt:
            continue
        best = max((len(rt & ct) / len(rt) for ct in case_texts), default=0)
        if best >= 0.25:
            covered += 1
        else:
            gaps.append(f"Possible gap: {req[:220]}")
    score = round(100 * covered / max(1, len(reqs)))
    titles = [(str(c.get("test_case_id","")), str(c.get("title","")).lower().strip()) for c in cases]
    dupes = []
    for i in range(len(titles)):
        for j in range(i+1, len(titles)):
            a, b = set(titles[i][1].split()), set(titles[j][1].split())
            sim = len(a & b) / max(1, len(a | b))
            if sim >= 0.65 and titles[i][1] and titles[j][1]:
                dupes.append((titles[i][0], titles[j][0], f"title similarity {sim:.0%}"))
    return {"coverage_score": score, "coverage_gaps": gaps[:20], "duplicate_pairs": dupes[:30]}
