import glob, json, os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SAMPLES_DIR = os.path.join(BASE_DIR, "data", "samples")


def collect_local_samples():
    files = glob.glob(os.path.join(SAMPLES_DIR, "*.json"))
    results = []
    for p in files:
        try:
            with open(p, 'r', encoding='utf-8') as f:
                results.append(json.load(f))
        except Exception:
            continue
    return results
if __name__ == "__main__":
    print(len(collect_local_samples()))
