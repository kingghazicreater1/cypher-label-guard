import json
import urllib.request

def test_dynamic_criteria_e2e():
    url = "http://127.0.0.1:8000/api/v2/infer"
    
    # 1. Test user-defined dynamic criteria payload
    payload = {
        "text": "Premium genuine leather jacket in bold red colorway, mid tier price bracket PKR 45,000, high quality stitching, zero defect found.",
        "modality": "TEXT",
        "depth_tier": "Standard",
        "criteria": [
            {"name": "Color", "type": "Enum", "range": "Red, Blue, Green, Black"},
            {"name": "Price Tier", "type": "Enum", "range": "Budget, Mid, Premium"},
            {"name": "Quality", "type": "Scale", "range": "1-10"},
            {"name": "Defective?", "type": "Boolean", "range": "Yes / No"},
            {"name": "Rejection Reason", "type": "Free Text", "range": "Max 200 chars"}
        ]
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    
    resp = urllib.request.urlopen(req)
    assert resp.status == 200, f"Expected 200, got {resp.status}"
    
    result = json.loads(resp.read().decode("utf-8"))
    print("\n" + "="*60)
    print("DYNAMIC CRITERIA E2E PIPELINE EXECUTION RESULT")
    print("="*60)
    
    assert "criteria_results" in result, "Missing criteria_results in response"
    assert "overall_criteria_confidence" in result, "Missing overall_criteria_confidence in response"
    
    crit_results = result["criteria_results"]
    overall_conf = result["overall_criteria_confidence"]
    
    print(f"Overall Confidence: {overall_conf}%\n")
    print(f"{'Heading':<20} {'Type':<12} {'Output Value':<16} {'Confidence & Agreement'}")
    print("-" * 65)
    
    results_by_name = {c["name"]: c for c in crit_results}
    
    for c in crit_results:
        print(f"{c['name']:<20} {c['type']:<12} {str(c['value']):<16} [OK] {c['confidence']}% ({c['agreement']})")
    
    print("-" * 65)
    
    # Verify exact criteria match
    assert "Color" in results_by_name
    assert results_by_name["Color"]["value"] == "Red"
    assert results_by_name["Color"]["confidence"] == 100.0
    
    assert "Quality" in results_by_name
    assert results_by_name["Quality"]["type"] == "Scale"
    assert isinstance(results_by_name["Quality"]["value"], (int, float))
    
    assert "Defective?" in results_by_name
    assert results_by_name["Defective?"]["value"] == "No"
    
    assert "Rejection Reason" in results_by_name
    assert results_by_name["Rejection Reason"]["value"] == "(none)"
    
    print("\n[OK] ALL ASSERTIONS PASSED! Dynamic criteria engine operational and verified.")

if __name__ == "__main__":
    test_dynamic_criteria_e2e()
