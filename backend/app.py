# backend/app.py
from flask import Flask, request, jsonify, send_from_directory
from collectors.sample_collector import collect_local_samples
from extractors.entities import extract
from utils.scorer import score_entity
import os
import hashlib
from fpdf import FPDF
import pandas as pd
import math

app = Flask(__name__, static_folder='../frontend/dist', template_folder='templates')

# ----------------------------
# Config / dataset paths
# ----------------------------
BASE = os.path.dirname(__file__) or "."
DATA_DIR = os.path.join(BASE, "data")
KAGGLE_PATH = os.path.join(DATA_DIR, "Data_Breaches_EN_V2_2004_2017_20180220.csv")
PERSON_PATH = os.path.join(DATA_DIR, "person_breaches.csv")  # optional synthetic person dataset
PERSON_DUMMY_PATH = os.path.join(DATA_DIR, "dummy_person_breaches.csv")  # alternative
ACTOR_PATH = os.path.join(DATA_DIR, "dummy_actor_intelligence.csv")     # actor intelligence

# ----------------------------
# Load datasets (if available)
# ----------------------------
df_breaches = None
for path in (KAGGLE_PATH,):
    if os.path.exists(path):
        try:
            # CSV from Kaggle may use semicolon or comma; try both robustly
            try:
                df_breaches = pd.read_csv(path, sep=';', encoding='utf-8', on_bad_lines='skip')
            except Exception:
                df_breaches = pd.read_csv(path, sep=',', encoding='utf-8', on_bad_lines='skip')
            print(f"[+] Loaded breaches dataset: {len(df_breaches)} rows from {path}")
            break
        except Exception as e:
            print("[!] Failed loading breaches CSV:", e)

# Load person dataset (prefer explicit path if present)
person_df = None
for p in (PERSON_PATH, PERSON_DUMMY_PATH):
    if os.path.exists(p):
        try:
            person_df = pd.read_csv(p)
            print(f"[+] Loaded person dataset: {len(person_df)} rows from {p}")
            break
        except Exception as e:
            print("[!] Failed loading person dataset:", e)

# Load actor intelligence dataset
actor_df = None
if os.path.exists(ACTOR_PATH):
    try:
        actor_df = pd.read_csv(ACTOR_PATH)
        print(f"[+] Loaded actor intelligence dataset: {len(actor_df)} rows")
    except Exception as e:
        print("[!] Failed loading actor dataset:", e)

# ----------------------------
# Utility helpers
# ----------------------------
def safe_contains(series, q):
    """Case-insensitive containment over pandas series"""
    return series.astype(str).str.lower().str.contains(q, na=False)

def compute_threat_score_from_breaches(breach_records):
    """
    Simple heuristic: larger 'Records Lost' -> higher impact.
    Normalizes to 0-100. If Records Lost missing, fallback to count-based score.
    """
    if not breach_records:
        return 0
    records_list = []
    for r in breach_records:
        v = r.get('Records Lost') or r.get('records_lost') or 0
        try:
            vnum = int(v)
        except Exception:
            # try to parse non-numeric strings like 'Unknown' -> treat as 0
            vnum = 0
        records_list.append(max(0, vnum))
    avg = sum(records_list) / len(records_list) if records_list else 0
    # scale: every 1M records -> +10 score, clipped
    score = min(95, int((avg / 1_000_000) * 10) + min(30, 10 * len(breach_records)))
    return score

def combine_scores(breach_score, actor_hits):
    """Blend breach impact and actor risk into final threat score (0-100)."""
    actor_boost = 0
    if actor_hits:
        # map risk levels (Critical/High/Medium/Low) to numeric
        risk_map = {"Critical": 30, "High": 20, "Medium": 10, "Low": 4}
        total = 0
        for a in actor_hits:
            r = a.get('risk_level') or a.get('risk') or "Medium"
            total += risk_map.get(r, 8) * (a.get('confidence', 0.6) or 0.6)
        actor_boost = min(40, int(total / max(1, len(actor_hits))))
    # weighted blend
    final = min(100, int(0.6 * breach_score + 0.4 * actor_boost))
    return final

def make_descriptive_report(profile):
    """
    Build a multi-paragraph, slide-like descriptive report that mirrors the PPT.
    Includes: Problem, Solution, Demo Findings, Impact, Roadmap, Recommendations.
    """
    lines = []
    lines.append(f"Profiler.AI — Descriptive Intelligence Report for query '{profile.get('query')}'")
    lines.append("")
    # Problem
    lines.append("Problem:")
    lines.append(
        "Investigations are slowed by fragmented public data. Analysts must manually correlate leaks, forum mentions, "
        "and platform activity across dozens of sources. This causes delayed attribution and missed leads."
    )
    lines.append("")
    # Solution
    lines.append("Solution (what Profiler.AI does):")
    lines.append(
        "Profiler.AI ingests local OSINT samples and open breach records, extracts identifiers (emails, phones, usernames), "
        "correlates them across sources, and produces a unified actor profile with confidence scoring, activity classification, "
        "and a verifiable PDF report (SHA-256 hashed)."
    )
    lines.append("")
    # Demo findings
    lines.append("Demo findings (automatically generated):")
    # summarize breach_data
    b = profile.get('breach_data', [])
    if b:
        lines.append(f"- Organization-level breaches found: {len(b)}. Top incident examples:")
        for br in b[:3]:
            org = br.get('Entity') or br.get('organization') or 'Unknown org'
            yr = br.get('Year') or br.get('year') or br.get('year')
            rec = br.get('Records Lost') or br.get('records_lost') or 'Unknown'
            story = (br.get('Story') or br.get('story') or '')[:180]
            lines.append(f"  • {org} ({yr}) — approx. {rec} records lost. {story}")
    else:
        lines.append("- No organization-level breaches matched the query in the breach dataset.")
    # person breaches
    p = profile.get('person_breach', [])
    if p:
        lines.append(f"- Personal exposures (simulated dataset): {len(p)} entries. Examples:")
        for pe in (p[:3]):
            lines.append(f"  • {pe.get('email')} — {pe.get('breach_source')} ({pe.get('year')}) — {pe.get('data_exposed')}")
    # actor intel
    a = profile.get('actor_intel', [])
    if a:
        lines.append(f"- Actor intelligence signals detected: {len(a)} records. Sample activities:")
        # show activity types and platforms
        for act in a[:4]:
            lines.append(f"  • {act.get('activity_type')} on {act.get('platform')} (risk: {act.get('risk_level')}, conf: {act.get('confidence')})")
    else:
        lines.append("- No actor-intel patterns found in the simulated actor dataset.")
    lines.append("")
    # Impact & Outcome
    lines.append("Impact (why this matters):")
    lines.append(
        "Using this tool, investigators reduce manual triage time and receive prioritized, explainable leads. "
        "Output is exportable as a hashed PDF useful for chain-of-custody and case records."
    )
    lines.append("")
    # Roadmap & Pilot Ask
    lines.append("Roadmap / Pilot Ask:")
    lines.append(
        "1) Pilot integration with one police SOC for 3 months using sanitized local logs. "
        "2) Add federated sharing to enable inter-agency model updates without raw data exchange. "
        "3) Integrate permissioned live connectors (GitHub, Etherscan) behind agency-approved keys."
    )
    lines.append("")
    # Recommendations & Caveats
    lines.append("Ethics & Caveats:")
    lines.append(
        "This prototype uses simulated person records for demonstration. Never expose live PII without legal authority. "
        "Confidence scores are heuristics; treat them as investigative leads, not proof."
    )
    lines.append("")
    lines.append("Suggested Next Steps for Judges / Pilots:")
    lines.append("- Evaluate on a 30-case labeled set to produce precision/recall metrics.")
    lines.append("- Approve a limited pilot data-sharing agreement for federated learning tests.")
    return "\n".join(lines)

# ----------------------------
# Core profile builder
# ----------------------------
def build_profile(query):
    query_lower = query.strip().lower()
    profile = {'query': query}

    # 1) Local samples (existing behaviour)
    samples = collect_local_samples()
    hits = [s for s in samples if query_lower in s.get('text', '').lower()]
    profile['local_hits'] = hits
    # entity extraction across local hits
    entity_map = {}
    for h in hits:
        text = h.get('text', '')
        ents = extract(text)
        occ = { "source": h.get('source','local'), "id": h.get('id'), "text": text, "timestamp": h.get('timestamp') }
        for e in ents.get('emails', []):
            entity_map.setdefault(('email', e), []).append(occ)
        for e in ents.get('phones', []):
            entity_map.setdefault(('phone', e), []).append(occ)
        for e in ents.get('wallets', []):
            entity_map.setdefault(('wallet', e), []).append(occ)
        for e in ents.get('names', []):
            entity_map.setdefault(('name', e), []).append(occ)

    clusters = []
    for (etype, val), occs in entity_map.items():
        clusters.append({
            'type': etype,
            'value': val,
            'occurrences': occs,
            'score': score_entity(occs)
        })
    profile['clusters'] = clusters

    # 2) Organization-level breaches (Kaggle dataset)
    breach_hits = []
    if df_breaches is not None:
        # check common columns and normalize names
        cols = [c.lower() for c in df_breaches.columns]
        # find likely entity/alt name columns
        entity_col = None
        alt_col = None
        for c in df_breaches.columns:
            if 'entity' in c.lower():
                entity_col = c
            if 'alternative' in c.lower() or 'alt' in c.lower():
                alt_col = c
        # search in both columns if present
        cond = False
        if entity_col:
            cond = df_breaches[entity_col].astype(str).str.lower().str.contains(query_lower, na=False)
        if alt_col:
            cond = cond | df_breaches[alt_col].astype(str).str.lower().str.contains(query_lower, na=False)
        matches = df_breaches[cond] if isinstance(cond, (pd.Series,)) else df_breaches[ df_breaches.apply(lambda r: query_lower in str(r).lower(), axis=1) ]
        if not matches.empty:
            # select helpful columns if they exist
            pick = []
            for cand in ["Entity","Organization","Story","Year","Records Lost","records_lost","Year "]:
                if cand in matches.columns:
                    pick.append(cand)
            # if none matched, pick first three
            if not pick:
                pick = list(matches.columns[:4])
            breach_hits = matches[pick].to_dict(orient='records')
    profile['breach_data'] = breach_hits

    # 3) Personal breach lookup (synthetic person dataset)
    person_hits = []
    if person_df is not None:
        # if query looks like email, try exact email matches; else substring
        if "@" in query_lower:
            person_hits = person_df[ person_df['email'].astype(str).str.lower() == query_lower ].to_dict(orient='records')
        else:
            # search by username or partial email local part
            person_hits = person_df[
                person_df['email'].astype(str).str.lower().str.contains(query_lower, na=False) |
                person_df.get('username', pd.Series()).astype(str).str.lower().str.contains(query_lower, na=False)
            ].to_dict(orient='records')
    profile['person_breach'] = person_hits

    # 4) Actor intelligence correlation (activity, risk)
    actor_hits = []
    if actor_df is not None:
        actor_hits_df = actor_df[
            safe_contains(actor_df.get('email', pd.Series(dtype=str)), query_lower) |
            safe_contains(actor_df.get('username', pd.Series(dtype=str)), query_lower)
        ]
        if not actor_hits_df.empty:
            actor_hits = actor_hits_df.to_dict(orient='records')
    profile['actor_intel'] = actor_hits

    # 5) compute threat scoring
    breach_score = compute_threat_score_from_breaches(breach_hits)
    final_score = combine_scores(breach_score, actor_hits)
    profile['scores'] = {
        'breach_impact_score': breach_score,
        'actor_boost_estimate': max(0, combine_scores(0, actor_hits) - combine_scores(0, [])),
        'final_threat_score': final_score
    }

    # 6) descriptive report (long text for PPT / slide narration)
    profile['descriptive_report'] = make_descriptive_report(profile)

    return profile

# ----------------------------
# Routes
# ----------------------------
@app.route('/api/profile')
def api_profile():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify({'error': 'missing query parameter q'}), 400
    profile = build_profile(q)
    return jsonify(profile)

@app.route('/api/report', methods=['POST'])
def api_report():
    data = request.json
    if not data:
        return jsonify({'error': 'missing body'}), 400

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, f"Profiler.AI Report - {data.get('query', '')}", ln=True)
    pdf.set_font('Arial', '', 10)
    pdf.multi_cell(0, 6, data.get('summary', data.get('descriptive_report', '')[:1000]))

    # clusters
    for c in data.get('clusters', []):
        pdf.ln(2)
        pdf.set_font('Arial','B',10)
        pdf.cell(0,6, f"{c.get('type')} : {c.get('value')} (score {c.get('score')})", ln=True)
        pdf.set_font('Arial','',9)
        for occ in c.get('occurrences', [])[:5]:
            pdf.multi_cell(0,5, f"- {occ.get('source')} / {occ.get('id')}")

    # breach data
    if data.get('breach_data'):
        pdf.ln(3)
        pdf.set_font('Arial','B',12)
        pdf.cell(0,6, "Breach Records", ln=True)
        pdf.set_font('Arial','',9)
        for b in data.get('breach_data')[:10]:
            pdf.multi_cell(0,5, str(b))

    # actor intel
    if data.get('actor_intel'):
        pdf.ln(3)
        pdf.set_font('Arial','B',12)
        pdf.cell(0,6, "Actor Intelligence", ln=True)
        pdf.set_font('Arial','',9)
        for a in data.get('actor_intel')[:10]:
            pdf.multi_cell(0,5, f"{a.get('username','')} | {a.get('platform','')} | {a.get('activity_type','')} | risk:{a.get('risk_level')} | conf:{a.get('confidence')}")

    # save
    fname = f"report_{data.get('query','profile')}.pdf"
    path = os.path.join(DATA_DIR, fname)
    pdf.output(path)

    h = hashlib.sha256()
    with open(path, 'rb') as f:
        h.update(f.read())
    return jsonify({'report_path': path, 'sha256': h.hexdigest()})

@app.route('/')
def index():
    try:
        return send_from_directory(app.static_folder, 'index.html')
    except Exception:
        return "Profiler.AI Backend running. Use /api/profile?q=..."

# ----------------------------
# Run
# ----------------------------
if __name__ == '__main__':
    # ensure data directory exists
    os.makedirs(DATA_DIR, exist_ok=True)
    app.run(debug=True, port=5000)
