import pandas as pd, random, faker

fake = faker.Faker()

breaches = [
    "LinkedIn", "Adobe", "Zomato", "Canva", "Dropbox", "Facebook",
    "Twitter", "Reddit", "Quora", "GitHub", "MySpace", "Target"
]

platforms = [
    "GitHub", "Reddit", "Telegram", "Discord", "DarkForum", "Twitter",
    "Instagram", "StackOverflow", "Medium", "Pastebin"
]

activities = [
    ("data trading", "Likely engaged in credential or leak sharing."),
    ("crypto scam", "Associated with fraudulent crypto promotions."),
    ("hacking forum", "Discussed tools or exploits in cyber forums."),
    ("tech contributor", "Posted open-source code or projects."),
    ("social activism", "Engaged in political or protest discourse."),
    ("spam marketing", "Involved in spam automation activity."),
    ("malware dev", "Shared or commented on malicious repositories.")
]

countries = ["India", "USA", "UK", "Russia", "Brazil", "Germany", "Japan", "Nigeria", "Pakistan", "Canada"]
risk_map = {"data trading": "High", "crypto scam": "High", "hacking forum": "High",
            "malware dev": "Critical", "spam marketing": "Medium",
            "social activism": "Low", "tech contributor": "Low"}

rows = []
for _ in range(1000):
    person = fake.simple_profile()
    email = person['mail']
    username = person['username']
    phone = f"+{random.choice([91,1,44,61,81])}{random.randint(7000000000,9999999999)}"
    breach = random.choice(breaches)
    platform = random.choice(platforms)
    year = random.randint(2010, 2024)
    country = random.choice(countries)
    activity, note = random.choice(activities)
    risk = risk_map.get(activity, "Medium")
    confidence = round(random.uniform(0.45, 0.98), 2)

    rows.append({
        "email": email,
        "username": username,
        "phone": phone,
        "country": country,
        "breach_source": breach,
        "platform": platform,
        "year": year,
        "activity_type": activity,
        "risk_level": risk,
        "confidence": confidence,
        "note": note
    })

df = pd.DataFrame(rows)
df.to_csv("data/dummy_actor_intelligence.csv", index=False)
print("[+] Generated 1000 synthetic actor intelligence records.")
