import re

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

# Test pattern detections
money_in_text = list(set(re.findall(r"(?:₦|\$|€|£|PKR|INR|USD|EUR)\s*[0-9]+(?:,[0-9]{3})*(?:\.[0-9]+)?", text)))
dates_in_text = list(set(re.findall(r"\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\b", text, re.IGNORECASE)))
times_in_text = list(set(re.findall(r"\b\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?\b", text)))
names_in_text = list(set(re.findall(r"\b(?:Mr\.|Mrs\.|Ms\.|Dr\.|Prof\.)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", text)))

print("Detected Money in Text :", money_in_text)
print("Detected Dates in Text :", dates_in_text)
print("Detected Times in Text :", times_in_text)
print("Detected Names in Text :", names_in_text)
