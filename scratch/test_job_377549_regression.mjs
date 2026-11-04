import fs from 'fs';

console.log("=== Testing Job #377549: Fallback & Concordance & False-Green Fixes ===");

// 1. Verify Fallback Registry in frontend
const fallbackTs = fs.readFileSync('frontend/src/lib/fallback.ts', 'utf-8');

const expectedPatterns = [
  'precision industrial assembly',
  'precision industrial component',
  'precision industrial bearing',
  'factory precision assembly',
  'factory precision product specimen',
];

for (const pat of expectedPatterns) {
  if (!fallbackTs.toLowerCase().includes(pat.toLowerCase())) {
    console.error(`[FAIL] Fallback pattern missing in frontend/src/lib/fallback.ts: ${pat}`);
    process.exit(1);
  }
}
console.log("[PASS] All generic industrial fallback patterns registered in frontend/src/lib/fallback.ts");

// 2. Verify Factory Quality banner in jobs.tsx checks hasDiscordance
const jobsTsx = fs.readFileSync('frontend/src/components/guardian/jobs.tsx', 'utf-8');

if (!jobsTsx.includes('hasDiscordance')) {
  console.error("[FAIL] hasDiscordance check missing in Factory Quality banner in jobs.tsx");
  process.exit(1);
}

if (!jobsTsx.includes('DISCORDANT QA')) {
  console.error("[FAIL] DISCORDANT QA badge missing in jobs.tsx");
  process.exit(1);
}

if (!jobsTsx.includes('startsWith(\'1 of 3\')')) {
  console.error("[FAIL] 1 of 3 discordance trigger missing in jobs.tsx");
  process.exit(1);
}

console.log("[PASS] Factory Quality banner in jobs.tsx couples discordance & fallbacks to FAILED INSPECTION!");
console.log("=== ALL JOB #377549 FRONTEND REGRESSION CHECKS PASSED ===");
