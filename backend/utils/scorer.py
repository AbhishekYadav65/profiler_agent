# Simple scoring by source counts and weights
WEIGHTS = {
    "github": 0.9,
    "leak": 0.8,
    "pastebin": 0.5,
    "forum": 0.6,
    "local": 0.4,
}


def score_entity(occurrences):
    # occurrences: list of dicts with key 'source'
    sources = set([o.get('source', 'local') for o in occurrences])
    base = 0.0
    for s in sources:
        base += WEIGHTS.get(s, 0.3)
    # normalize by number of unique sources
    if not sources:
        return 0.0
    score = base / (len(sources) + 0.5)
    if score > 1.0:
        score = 1.0
    return round(score, 2)
