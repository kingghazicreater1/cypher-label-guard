import re

# Test Date Matching
text = "On 12 December 2024... return for a follow-up on 26 December 2024."
val = "2024-12-12"

MONTH_MAP = {
    "january": 1, "jan": 1, "february": 2, "feb": 2, "march": 3, "mar": 3,
    "april": 4, "apr": 4, "may": 5, "june": 6, "jun": 6, "july": 7, "jul": 7,
    "august": 8, "aug": 8, "september": 9, "sep": 9, "october": 10, "oct": 10,
    "november": 11, "nov": 11, "december": 12, "dec": 12
}

def extract_normalized_dates(s: str) -> set[tuple[int, int, int]]:
    dates = set()
    # 1. Matches "12 December 2024" or "Dec 12, 2024"
    for m in re.finditer(r"\b(\d{1,2})[ \t]+([A-Za-z]+)[ \t]+(\d{4})\b", s):
        d, m_name, y = int(m.group(1)), m.group(2).lower(), int(m.group(3))
        if m_name in MONTH_MAP:
            dates.add((y, MONTH_MAP[m_name], d))
    for m in re.finditer(r"\b([A-Za-z]+)[ \t]+(\d{1,2}),?[ \t]+(\d{4})\b", s):
        m_name, d, y = m.group(1).lower(), int(m.group(2)), int(m.group(3))
        if m_name in MONTH_MAP:
            dates.add((y, MONTH_MAP[m_name], d))
    # 2. Matches ISO "2024-12-12" or "2024/12/12"
    for m in re.finditer(r"\b(\d{4})[-/](\d{1,2})[-/](\d{1,2})\b", s):
        y, m_num, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        dates.add((y, m_num, d))
    # 3. Matches "12/12/2024" (DD/MM/YYYY or MM/DD/YYYY)
    for m in re.finditer(r"\b(\d{1,2})[-/](\d{1,2})[-/](\d{4})\b", s):
        a, b, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        # Add canonical tuple
        dates.add((y, min(a, b), max(a, b)))
    return dates

text_dates = extract_normalized_dates(text)
val_dates = extract_normalized_dates(val)
print("Text Dates:", text_dates)
print("Val Dates:", val_dates)
covered = len(text_dates & val_dates)
print(f"Covered: {covered}/{len(text_dates)}")
ratio = covered / len(text_dates)
print("Ratio:", ratio)
