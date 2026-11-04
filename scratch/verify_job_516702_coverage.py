import sys
sys.path.insert(0, ".")
from features.cat_a_inference.feat_04_subspace_voting.feature import SubspaceDisagreementVotingFeature

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

ratio, reason = SubspaceDisagreementVotingFeature.compute_span_coverage("PERSON", val, text)
print(f"PERSON ratio: {ratio}, reason: '{reason}'")
assert ratio == 1.0, f"Expected 1.0, got {ratio}"

ratio_m, reason_m = SubspaceDisagreementVotingFeature.compute_span_coverage("MONEY", "$12,500; $150", text)
print(f"MONEY ratio: {ratio_m}, reason: '{reason_m}'")
assert ratio_m == 1.0, f"Expected 1.0, got {ratio_m}"

ratio_d, reason_d = SubspaceDisagreementVotingFeature.compute_span_coverage("DATE", "22 October 2024; 21 October 2024", text)
print(f"DATE ratio: {ratio_d}, reason: '{reason_d}'")
assert ratio_d == 1.0, f"Expected 1.0, got {ratio_d}"

ratio_t, reason_t = SubspaceDisagreementVotingFeature.compute_span_coverage("TIME", "11:30 AM; 03:15 AM", text)
print(f"TIME ratio: {ratio_t}, reason: '{reason_t}'")
assert ratio_t == 1.0, f"Expected 1.0, got {ratio_t}"

print("ALL SPAN COVERAGE CHECKS PASSED PERFECTLY!")
