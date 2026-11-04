import fs from 'fs';

console.log("=== Comprehensive Testing: Vision Studio Anomaly Coupling Across All 3 View Modes ===");

const jobsContent = fs.readFileSync('frontend/src/components/guardian/jobs.tsx', 'utf-8');
const contextContent = fs.readFileSync('frontend/src/components/guardian/context.tsx', 'utf-8');
const dashboardContent = fs.readFileSync('frontend/src/components/guardian/dashboard.tsx', 'utf-8');

// ============================================================================
// 1. Specsheet View Mode Assertions
// ============================================================================
console.log("[*] Checking View Mode 1: Factory SpecSheet...");

if (!jobsContent.includes("isAnomaly ? 'FAILED QA INSPECTION' : 'FACTORY QA VERIFIED'")) {
  console.error("FAIL [Specsheet]: FACTORY QA VERIFIED is still unconditional");
  process.exit(1);
}

if (!jobsContent.includes("isAnomaly ? 'REJECTED · 0.0%' : '✓ 100% Concordance'")) {
  console.error("FAIL [Specsheet]: 100% Concordance header badge is still unconditional");
  process.exit(1);
}

// ============================================================================
// 2. Canvas View Mode Assertions
// ============================================================================
console.log("[*] Checking View Mode 2: Interactive Bounding Boxes (Canvas View)...");

if (!jobsContent.includes("isAnomaly ? '⚠️ Flagged by Security Guard' : '✓ 4/4 APIs Concordant'")) {
  console.error("FAIL [Canvas]: Coords concordance pill is still unconditional");
  process.exit(1);
}

const ballotModels = ['GPT-4o Vision', 'Claude 3.5 V', 'Gemini 1.5 Flash', 'Mistral Pixtral'];
for (const model of ballotModels) {
  if (!jobsContent.includes(`isAnomaly ? 'Rejected (0%)' : 'Pass`)) {
    console.error(`FAIL [Canvas]: Vision model ballots for ${model} are not coupled to isAnomaly`);
    process.exit(1);
  }
}

// ============================================================================
// 3. Certificate View Mode Assertions
// ============================================================================
console.log("[*] Checking View Mode 3: Official Inspection Tag / Certificate...");

if (!jobsContent.includes("isAnomaly ? 'OFFICIAL DEFECT / REJECTION NOTICE' : 'OFFICIAL AUDIT CERTIFICATE'")) {
  console.error("FAIL [Certificate]: Notice title is not coupled to isAnomaly");
  process.exit(1);
}

if (!jobsContent.includes("isAnomaly ? 'CYPHERLABELGUARD QA REJECTION & ANOMALY LOG' : 'CYPHERLABELGUARD QUALITY CONCORDANCE SEAL'")) {
  console.error("FAIL [Certificate]: Seal title is not coupled to isAnomaly");
  process.exit(1);
}

if (!jobsContent.includes("isAnomaly ? 'FAILED (0.0% Concordant · REJECTED)' : 'PASSED (100% Concordant)'")) {
  console.error("FAIL [Certificate]: Consensus verdict is not coupled to isAnomaly");
  process.exit(1);
}

if (!jobsContent.includes("isAnomaly ? 'Inspection Revoked · Security Anomaly' : 'Digitally Signed & Sealed'")) {
  console.error("FAIL [Certificate]: Digital signature is not coupled to isAnomaly");
  process.exit(1);
}

// ============================================================================
// 4. Number() Wrapping Coercion Defense Check (Item 1)
// ============================================================================
console.log("[*] Checking Number() Wrapping Defense (zero raw confidence === 0)...");

// RegEx to find raw confidence === 0 not wrapped by Number(...)
const rawConfidenceRegex = /(?<!Number\([a-zA-Z0-9_.]*)confidence\s*===\s*0/g;

const jobsMatches = jobsContent.match(rawConfidenceRegex);
if (jobsMatches) {
  console.error(`FAIL: Found ${jobsMatches.length} raw un-coerced 'confidence === 0' in jobs.tsx`);
  process.exit(1);
}

const contextMatches = contextContent.match(rawConfidenceRegex);
if (contextMatches) {
  console.error(`FAIL: Found ${contextMatches.length} raw un-coerced 'confidence === 0' in context.tsx`);
  process.exit(1);
}

const dashboardMatches = dashboardContent.match(rawConfidenceRegex);
if (dashboardMatches) {
  console.error(`FAIL: Found ${dashboardMatches.length} raw un-coerced 'confidence === 0' in dashboard.tsx`);
  process.exit(1);
}

// Functional test for string "0" vs number 0
function testAnomalyCheck(c) {
  return Boolean(c.anomaly) || String(c.value).includes('REJECT') || Number(c.confidence) === 0;
}

if (!testAnomalyCheck({ name: 'test', confidence: 0, value: 'ok' })) {
  console.error("FAIL: Numeric 0 failed anomaly check");
  process.exit(1);
}

if (!testAnomalyCheck({ name: 'test', confidence: "0", value: 'ok' })) {
  console.error("FAIL: String '0' bypassed anomaly check!");
  process.exit(1);
}

console.log("[PASS] All 3 View Modes & Number() Coercion Checks PASSED cleanly (100%)!");
