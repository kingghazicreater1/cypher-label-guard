import re

text = """From: "Chase Fraud Alert" <security@chase-verify-portal.com>
To: customer@example.com
Date: 22 October 2024, 11:30 AM
Subject: URGENT: Your account is locked. Action required within 12 hours.
Body:
Dear Customer,
We detected an unauthorized login attempt on your Chase Online account on 21 October 2024 at 03:15 AM from an unrecognized IP address in London, UK.
To protect your funds, we have placed a temporary hold on your account and blocked a pending wire transfer of $12,500.
You must verify your identity to unlock your account. Please click the link below to log in and confirm a $150 processing fee:
👉 [https://chase-verify-portal.com/login]
If you do not verify within 12 hours, your account will be permanently closed, and the $12,500 will be seized by the fraud department.
If you did not authorize this, call us immediately at +1-800-555-0199.
Sincerely,
Mr. Robert Vance
Head of Fraud Prevention, Chase"""

val = "Mr. Robert Vance"

# Using [ \t]+ instead of \s+
raw_names = set(re.findall(r"\b(?:Mr\.|Mrs\.|Ms\.|Miss|Dr\.|Prof\.)[ \t]+[A-Z][a-z]+(?:[ \t]+[A-Z][a-z]+)*\b", text))
print("raw_names with [ \\t]+:", raw_names)

identities = {}
for n in raw_names:
    parts = n.split()
    key = (parts[0], parts[-1])
    if key not in identities or len(n) > len(identities[key]):
        identities[key] = n
unique_people = set(identities.values())
print("unique_people:", unique_people)

covered = 0
for person in unique_people:
    parts = person.split()
    print(f"Testing person='{person}', val='{val}'")
    # Check if person in val, or val in person, or title + surname in val, or first + last in val
    first_last = f"{parts[1]} {parts[-1]}" if len(parts) >= 3 else parts[-1]
    title_last = f"{parts[0]} {parts[-1]}"
    
    is_match = (
        person.lower() in val.lower() or
        val.lower() in person.lower() or
        title_last.lower() in val.lower() or
        first_last.lower() in val.lower()
    )
    print(f"Match result: {is_match}")
    if is_match:
        covered += 1

print("covered:", covered)
ratio = round(covered / len(unique_people), 2)
print("ratio:", ratio)
