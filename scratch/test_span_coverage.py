import re
import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

def compute_span_coverage(heading_name: str, chosen_val: str, text: str) -> tuple[float, str]:
    """Computes mathematical span coverage recall ratio for objective universal entity categories."""
    hl = heading_name.lower()
    val = str(chosen_val).strip()
    
    # 1. Currency / Money Coverage
    if any(k in hl for k in ["money", "currency", "amount", "cost", "fee", "price", "charge"]):
        raw_spans = set(re.findall(r"(?:[₦$€£]|PKR|INR|USD|EUR)\s*[0-9]+(?:,[0-9]{3})*(?:\.[0-9]+)?", text))
        if raw_spans:
            # normalize for comparison
            covered = sum(1 for s in raw_spans if re.sub(r"[\s,]", "", s) in re.sub(r"[\s,]", "", val))
            ratio = covered / len(raw_spans)
            return ratio, f"Currency Span Coverage: {covered}/{len(raw_spans)}"

    # 2. Date Coverage
    if any(k in hl for k in ["date", "calendar"]):
        raw_dates = set(re.findall(r"\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\b", text, re.IGNORECASE))
        if raw_dates:
            covered = sum(1 for d in raw_dates if re.search(re.escape(d), val, re.IGNORECASE))
            ratio = covered / len(raw_dates)
            return ratio, f"Date Span Coverage: {covered}/{len(raw_dates)}"

    # 3. Clock Time Coverage
    if any(k in hl for k in ["time", "timestamp", "clock"]):
        raw_times = set(re.findall(r"\b\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?\b", text))
        if raw_times:
            covered = sum(1 for t in raw_times if re.search(re.escape(t), val, re.IGNORECASE))
            ratio = covered / len(raw_times)
            return ratio, f"Clock Time Span Coverage: {covered}/{len(raw_times)}"

    # 4. Titled Proper Names Coverage
    if any(k in hl for k in ["person", "people", "names", "individuals"]):
        raw_names = set(re.findall(r"\b(?:Mr\.|Mrs\.|Ms\.|Dr\.|Prof\.)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", text))
        if raw_names:
            covered = 0
            for name in raw_names:
                parts = name.split()
                # Check if either full name or honorific + last name matches
                if name.lower() in val.lower() or (len(parts) >= 2 and f"{parts[0]} {parts[-1]}".lower() in val.lower()):
                    covered += 1
            ratio = covered / len(raw_names)
            return ratio, f"Titled Names Span Coverage: {covered}/{len(raw_names)}"

    return 1.0, "Universal Coverage Verified"

# Test with bad extraction from Job #416976:
text = (
    "On 12 June 2024, a customer, Mrs. Amara Obi, attempted to transfer ₦1,500,000 from her current account "
    "at Horizon Bank to a beneficiary, Mr. Femi Adeleke. The transfer was initiated via mobile banking but was "
    "blocked by the bank's anti-fraud policy because the beneficiary account had been flagged for suspicious activity "
    "on 9 June 2024. Mrs. Obi was informed that the funds would not be released unless she visited a branch and "
    "provided additional identification. She argued that she had made similar transfers before without issues and "
    "claimed the bank's SMS notification system had never alerted her to the flag. Horizon Bank's compliance officer, "
    "Ms. Ngozi Okoro, stated that the alert had been sent and that a charge of ₦2,500 had been deducted for the manual "
    "review. Mrs. Obi threatened to close her account if the matter was not resolved within 72 hours. The compliance "
    "officer agreed to expedite the review but confirmed that no refund of the ₦2,500 charge would be issued unless the "
    "flag was proven to be an error. A complaint was filed at 3:15 PM, and Mrs. Obi left without the transfer being completed."
)

print("BAD EXTRACTIONS:")
print("PERSON (Mrs. Obi; Ms. Ngozi Okoro):", compute_span_coverage("PERSON", "Mrs. Obi; Ms. Ngozi Okoro", text))
print("MONEY (₦2,500):", compute_span_coverage("MONEY", "₦2,500", text))
print("DATE (9 June 2024):", compute_span_coverage("DATE", "9 June 2024", text))
print("TIME (72 hours):", compute_span_coverage("TIME", "72 hours", text))

print("\nPERFECT EXTRACTIONS:")
print("PERSON (Mrs. Amara Obi; Mr. Femi Adeleke; Ms. Ngozi Okoro):", compute_span_coverage("PERSON", "Mrs. Amara Obi; Mr. Femi Adeleke; Ms. Ngozi Okoro", text))
print("MONEY (₦1,500,000; ₦2,500):", compute_span_coverage("MONEY", "₦1,500,000; ₦2,500", text))
print("DATE (12 June 2024; 9 June 2024):", compute_span_coverage("DATE", "12 June 2024; 9 June 2024", text))
print("TIME (3:15 PM):", compute_span_coverage("TIME", "3:15 PM", text))
