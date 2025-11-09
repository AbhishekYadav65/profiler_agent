import json, os
os.makedirs("data/samples", exist_ok=True)


templates = [
{"source":"pastebin","text":"Selling DB. Contact darklion99@protonmail.com, wallet bc1qabc123xyz, phone +919876543210"},
{"source":"github","text":"Repo by darklion99 includes creds-list.txt and notes: contact darklion99@gmail.com"},
{"source":"forum","text":"User d_lion posted invoices with phone +919876543210 and email user123@gmail.com"},
{"source":"leak","text":"Email: victim@example.com leaked in breach 'loanapp-2023' with mention of darklion99"}
]


for i in range(30):
    t = templates[i % len(templates)].copy()
    t["id"] = f"sample{i+1}"
    t["timestamp"] = "2025-11-09T00:00:00Z"
    p = os.path.join("data/samples", f"{t['id']}.json")
    with open(p, "w", encoding='utf-8') as f:
        json.dump(t, f, indent=2)


print("Generated", len(os.listdir("data/samples")), "samples in data/samples")