import re

text_416976 = """
Horizon Bank customer service sent an email to Mrs. Amara Obi regarding an attempted transfer to Mr. Femi Adeleke.
Signed by Ms. Ngozi Okoro, Operations Lead.
"""

val_incomplete = "Mrs. Obi; Ms. Ngozi Okoro"

raw_names = set(re.findall(r"\b(?:Mr\.|Mrs\.|Ms\.|Miss|Dr\.|Prof\.)[ \t]+[A-Z][a-z]+(?:[ \t]+[A-Z][a-z]+)*\b", text_416976))
identities = {}
for n in raw_names:
    parts = n.split()
    key = (parts[0], parts[-1])
    if key not in identities or len(n) > len(identities[key]):
        identities[key] = n
unique_people = set(identities.values())
print("Job 416976 unique_people:", unique_people)

covered = 0
for person in unique_people:
    parts = person.split()
    first_last = f"{parts[1]} {parts[-1]}" if len(parts) >= 3 else parts[-1]
    title_last = f"{parts[0]} {parts[-1]}"
    is_match = (
        person.lower() in val_incomplete.lower() or
        val_incomplete.lower() in person.lower() or
        title_last.lower() in val_incomplete.lower() or
        first_last.lower() in val_incomplete.lower()
    )
    print(f"person='{person}' matched={is_match}")
    if is_match:
        covered += 1

ratio = round(covered / len(unique_people), 2)
print("covered:", covered, "total:", len(unique_people), "ratio:", ratio)
