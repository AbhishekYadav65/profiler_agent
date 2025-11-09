from flask import Flask, request, jsonify, send_from_directory
from collectors.sample_collector import collect_local_samples
from extractors.entities import extract
from utils.scorer import score_entity
import os
import hashlib
from fpdf import FPDF

app = Flask(__name__, static_folder='../frontend/dist', template_folder='templates')

# helper: build profile from input

def build_profile(query):
    samples = collect_local_samples()
    # find samples that contain the query string (case-insensitive)
    hits = [s for s in samples if query.lower() in s.get('text','').lower()]

    # aggregate occurrences by entity
    entity_map = {}
    for h in hits:
        text = h.get('text','')
        ents = extract(text)
        # create occurrence record
        occ = {"source": h.get('source','local'), "id": h.get('id'), "text": text, "timestamp": h.get('timestamp')}
        # add each entity
        for e in ents.get('emails',[]):
            entity_map.setdefault(('email', e), []).append(occ)
        for e in ents.get('phones',[]):
            entity_map.setdefault(('phone', e), []).append(occ)
        for e in ents.get('wallets',[]):
            entity_map.setdefault(('wallet', e), []).append(occ)
        for e in ents.get('names',[]):
            entity_map.setdefault(('name', e), []).append(occ)

    # build cluster list
    clusters = []
    for (etype, val), occs in entity_map.items():
        clusters.append({
            'type': etype,
            'value': val,
            'occurrences': occs,
            'score': score_entity(occs)
        })

    # simple summary
    summary_lines = []
    for c in clusters:
        summary_lines.append(f"{c['type'].upper()} {c['value']} appears in {len(c['occurrences'])} sources. Confidence {c['score']}")
    summary = ' '.join(summary_lines)[:1000]

    profile = {
        'query': query,
        'clusters': clusters,
        'summary': summary,
        'hit_count': len(hits)
    }
    return profile


@app.route('/api/profile')
def api_profile():
    q = request.args.get('q','').strip()
    if not q:
        return jsonify({'error':'missing query parameter q'}), 400
    profile = build_profile(q)
    return jsonify(profile)


@app.route('/api/report', methods=['POST'])
def api_report():
    data = request.json
    if not data:
        return jsonify({'error':'missing body'}), 400
    # create simple PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, f"Profiler.AI Report - {data.get('query','')}", ln=True)
    pdf.set_font('Arial', '', 10)
    pdf.multi_cell(0, 6, data.get('summary',''))

    # list clusters
    for c in data.get('clusters',[]):
        pdf.ln(2)
        pdf.set_font('Arial','B',10)
        pdf.cell(0,6, f"{c.get('type')} : {c.get('value')} (score {c.get('score')})", ln=True)
        pdf.set_font('Arial','',9)
        for occ in c.get('occurrences',[])[:3]:
            s = f"- {occ.get('source')} / {occ.get('id')}"
            pdf.multi_cell(0,5,s)

    fname = f"report_{data.get('query','profile')}.pdf"
    path = os.path.join('data', fname)
    pdf.output(path)
    # compute sha256
    h = hashlib.sha256()
    with open(path,'rb') as f:
        h.update(f.read())
    return jsonify({'report_path': path, 'sha256': h.hexdigest()})


@app.route('/')
def index():
    # serve frontend in production build if present
    try:
        return send_from_directory(app.static_folder, 'index.html')
    except Exception:
        return "Profiler.AI Backend running. Use /api/profile?q=..."


if __name__ == '__main__':
    # ensure sample data exists
    if not os.path.isdir('data/samples') or len(os.listdir('data/samples'))==0:
        from utils.make_samples import __file__ as mfile
        # run generator
        try:
            import utils.make_samples as mg
            mg
        except Exception:
            pass
    app.run(debug=True, port=5000)
