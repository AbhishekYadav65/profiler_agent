import re
import spacy

# load small model
nlp = spacy.load("en_core_web_sm")

EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_RE = re.compile(r"(?:\+91|0)?[6-9]\d{9}")
WALLET_RE = re.compile(r"\b(bc1q[a-z0-9]{6,})\b", re.IGNORECASE)


def extract(text):
    text = text or ""
    entities = {"emails": [], "phones": [], "wallets": [], "names": []}
    entities["emails"] = list(set(EMAIL_RE.findall(text)))
    entities["phones"] = list(set(PHONE_RE.findall(text)))
    entities["wallets"] = list(set(WALLET_RE.findall(text)))

    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ in ("PERSON", "ORG"):
            entities["names"].append(ent.text)
    # dedupe names
    entities["names"] = list(set(entities["names"]))
    return entities
