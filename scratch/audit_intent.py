import sys, os
sys.path.insert(0, os.path.abspath("."))
from features.cat_a_inference.feat_04_subspace_voting.feature import SubspaceDisagreementVotingFeature as F

headings = [
    "UPFRONT_FEE", "PRIMARY_FACILITY_AMOUNT", "PARTIES", "MATURITY_DATES",
    "diagnosis", "discount code", "county", "account number", "accountant name",
    "background check result", "ground rent", "setting of the incident", "environment variable",
    "original invoice number", "scratch pad notes", "tear down date", "wear and tear clause",
    "count of transactions", "head of household", "surface area", "organism culture result",
    "authentic signature present", "persons", "events",
]
for h in headings:
    print(f"{h:<30} -> {F.classify_heading_intent(h)}")
