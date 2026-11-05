/**
 * Centralized Fallback Registry for Frontend (CypherLabelGuard).
 * Prevents generic descriptors or canned mock strings from receiving passes or false approvals.
 */

export const TEXT_FALLBACKS = [
  /high-definition video stream specimen/i,
  /generic text specimen/i,
  /unspecified document body/i,
  /target (media|visual|audio|video) stream/i,
];

export const IMAGE_FALLBACKS = [
  /precision industrial assembly/i,
  /precision industrial component/i,
  /precision industrial bearing/i,
  /factory precision assembly/i,
  /factory precision product specimen/i,
  /industrial component/i,
  /industrial precision bearing assembly/i,
  /generic visual specimen/i,
  /canonical industry product designation/i,
];

export const VIDEO_FALLBACKS = [
  /temporal video stream specimen/i,
  /standard test video sequence/i,
];

export const AUDIO_FALLBACKS = [
  /acoustic signal processing specimen/i,
  /synthesized acoustic stream/i,
];

export const MULTIMODAL_FALLBACKS = [
  /mixed modality specimen/i,
  /synthetic pair assertion/i,
];

export const FALLBACK_PATTERNS: RegExp[] = [
  ...TEXT_FALLBACKS,
  ...IMAGE_FALLBACKS,
  ...VIDEO_FALLBACKS,
  ...AUDIO_FALLBACKS,
  ...MULTIMODAL_FALLBACKS,
  /\[unverified.*\]/i,
  /\[rejected.*\]/i,
  /verified \/ pristine/i,
  /no specimen detected/i,
];

export function isFallbackString(value: unknown): boolean {
  if (value === null || value === undefined) return false;
  const str = String(value).trim();
  return FALLBACK_PATTERNS.some((pattern) => pattern.test(str));
}
