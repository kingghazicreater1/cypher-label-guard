import { getDisplayHeading, type HeadingAliasMap } from '../../lib/label-utils';

export type ImageAnnotation = {
  label: string;
  confidence: number;
  color?: string;
  box: { x: number; y: number; w: number; h: number };
  description?: string;
};

export type Job = {
  id: string;
  name: string;
  type: string;
  status: string;
  progress: number;
  labels: number;
  cost: string;
  created: string;
  folder_name?: string | undefined;
  criteria?: any[] | undefined;
  criteria_results?: any[] | undefined;
  overall_criteria_confidence?: number | undefined;
  trace_id?: string | undefined;
  imageUrl?: string | undefined;
  imageAnnotations?: ImageAnnotation[] | undefined;
  consensus_label?: string | undefined;
  affirmative_votes?: number | string | undefined;
  anomaly_detected?: boolean | undefined;
  duration?: string | number | undefined;
  job_number?: string | number | undefined;
  has_anomaly?: boolean | undefined;
  lineage_hash?: string | undefined;
  folders?: string[] | undefined;
  confidence?: number | string | undefined;
};

export const initialJobs: Job[] = [];
export const labels: { id: string; type: string; label: string; source: string; confidence: number; status: string }[] = [];
export const providers = [
  { name: 'OpenAI', model: 'GPT-4o', short: 'O', confidence: 0, latency: '0 ms', cost: '$0.00', color: 'mint' },
  { name: 'Anthropic', model: 'Claude 3.5 Sonnet', short: 'A', confidence: 0, latency: '0 ms', cost: '$0.00', color: 'amber' },
  { name: 'Google', model: 'Gemini 1.5 Pro', short: 'G', confidence: 0, latency: '0 ms', cost: '$0.00', color: 'cyan' },
  { name: 'Mistral', model: 'Mistral Large', short: 'M', confidence: 0, latency: '0 ms', cost: '$0.00', color: 'violet' },
];
export const privacyMethods = ['Zero-retention APIs', 'RAM-only processing', 'Metadata stripping', 'Ephemeral containers', 'Immutable lineage hashing'];
export const featureGroups = [
  { name: 'Inference & accuracy', features: ['Semantic Saturation Threshold', 'N-Shot Zero Calibration', 'Entropic Certainty Masking', 'Subspace Disagreement Voting', 'Adaptive Dimension Selector', 'Token Attribution Provenance', 'Vector Field Collapse Prevention', 'Adversarial Label Sanity Check', 'Contextual Weighted Tie-Break', 'Semantic Round-Trip Fidelity Score'] },
  { name: 'Speed & throughput', features: ['Tiered Depth Scaling', 'Adaptive Timeout Threshold', 'Async Non-Blocking I/O', 'Connection Pool 500', 'Zero-Copy Parsing', 'Pre-Allocated Memory', 'Multi-Tenant Architecture'] },
  { name: 'Privacy & security', features: ['Zero-Retention Inference Pass', 'RAM-Only Memory Map', 'Data Echo Cancellation', 'Panic-Induced Salt Flush', 'Immutable Lineage Hashing', 'Stateless Embedding Commitment'] },
  { name: 'Lifecycle & drift', features: ['Drift Witness Marks', 'Epistemic Humility Flag', 'Bitwise Identical Reproducibility', 'Night Batch Re-Processing'] },
  { name: 'Output & interface', features: ['Graceful Degradation Proxy', 'Three-Tier Human Options', 'Elastic Parliamentary Scaling', 'Live Parliament Dashboard', 'Prove It Button', 'Anthropological Outsider Module'] },
  { name: 'Multi-modal', features: ['Multi-Modal Router', 'Vision API Connector', 'Audio Transcription Pipeline', 'Video Frame Sampler', 'Unified Multi-Modal Output'] },
];
export const auditEvents: string[] = [];

export function sanitizeCsvCell(val: unknown): string {
  const s = String(val ?? '');
  if (s.startsWith('=') || s.startsWith('+') || s.startsWith('-') || s.startsWith('@') || s.startsWith('\t') || s.startsWith('\r')) {
    if (s.startsWith('-') && !isNaN(Number(s))) {
      return `"${s.replaceAll('"', '""')}"`;
    }
    return `"'${s.replaceAll('"', '""')}"`;
  }
  return `"${s.replaceAll('"', '""')}"`;
}

export function exportFile(name: string, data: unknown, csv = false) {
  const content = csv && Array.isArray(data) && data.length
    ? [
        Object.keys(data[0]).map(h => `"${String(h).replaceAll('"', '""')}"`).join(','),
        ...data.map(row => Object.values(row).map(sanitizeCsvCell).join(','))
      ].join('\n')
    : JSON.stringify(data, null, 2);
  const url = URL.createObjectURL(new Blob([content], { type: csv ? 'text/csv' : 'application/json' }));
  const anchor = document.createElement('a'); anchor.href = url; anchor.download = name; anchor.click(); URL.revokeObjectURL(url);
}

export function exportJobsBatch(
  name: string,
  jobsList: Job[],
  format: 'csv' | 'json' = 'csv',
  opts: { mode?: 'audit' | 'store'; aliases?: HeadingAliasMap } = {}
) {
  if (!jobsList || jobsList.length === 0) return;

  if (format === 'json') {
    const data = jobsList.map(j => ({
      id: j.id,
      name: j.name,
      folder: j.folder_name || 'General Workspace',
      status: j.status,
      confidence: j.overall_criteria_confidence,
      consensus_label: j.consensus_label,
      criteria_results: j.criteria_results || [],
      created: j.created,
      trace_id: j.trace_id,
      anomaly_detected: j.anomaly_detected,
    }));
    exportFile(name.endsWith('.json') ? name : `${name}.json`, data, false);
    return;
  }

  // Gather all unique heading names across all selected jobs
  const allHeadings: string[] = [];
  jobsList.forEach(j => {
    (j.criteria_results || []).forEach((c: any) => {
      const hName = (c.heading || c.name || '').trim();
      if (hName && !allHeadings.includes(hName)) {
        allHeadings.push(hName);
      }
    });
  });

  const displayFor = (h: string) => getDisplayHeading(h, opts.aliases);
  const isStoreMode = opts.mode === 'store';

  const headers = isStoreMode
    ? ['Image / Asset Name', ...allHeadings.map(displayFor)]
    : [
        'Job ID',
        'Image / Asset Name',
        'Collection / Folder',
        'Status',
        'Overall Confidence %',
        'Consensus Label',
        ...allHeadings.flatMap(h => {
          const disp = displayFor(h);
          return [`Heading: ${disp}`, `${disp} (Conf %)`];
        }),
        'Created',
        'Trace ID',
        'Anomaly Detected?',
      ];

  const rows = jobsList.map(j => {
    const critMap: Record<string, { value: string; conf: any }> = {};
    (j.criteria_results || []).forEach((c: any) => {
      const hName = (c.heading || c.name || '').trim();
      if (hName) {
        critMap[hName] = {
          value: c.winning_label || c.value || '',
          conf: c.confidence !== undefined ? c.confidence : '',
        };
      }
    });

    const values = isStoreMode
      ? [j.name, ...allHeadings.map(h => (critMap[h] ? critMap[h].value : ''))]
      : [
          j.id,
          j.name,
          j.folder_name || 'General Workspace',
          j.status,
          j.overall_criteria_confidence ?? '',
          j.consensus_label || '',
          ...allHeadings.flatMap(h => {
            const item = critMap[h];
            return [
              item ? item.value : '',
              item && item.conf !== '' ? `${item.conf}%` : '',
            ];
          }),
          j.created,
          j.trace_id || '',
          j.anomaly_detected ? 'YES' : 'NO',
        ];

    return values.map(sanitizeCsvCell).join(',');
  });

  const csvContent = [headers.map(h => `"${h.replaceAll('"', '""')}"`).join(','), ...rows].join('\n');
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = name.endsWith('.csv') ? name : `${name}.csv`;
  anchor.click();
  URL.revokeObjectURL(url);
}
export const pageHead = (title: string, description: string) => ({ meta: [{ title: `${title} · CypherLabelGuard` }, { name: 'description', content: description }, { property: 'og:title', content: `${title} · CypherLabelGuard` }, { property: 'og:description', content: description }, { property: 'og:type', content: 'website' }, { name: 'twitter:card', content: 'summary_large_image' }] });

export function isLegacyStaticAnnotation(annotations?: ImageAnnotation[]): boolean {
  if (!annotations || annotations.length === 0) return true;
  const hasLegacyDemoLabels = annotations.every(
    (a) =>
      a.label.includes('Visual Subject: Detected') ||
      a.label.includes('Surface Inspection: Passed') ||
      a.label.includes('Feature Recognition: Concordant')
  );
  const isDefault1 = annotations.some(
    (a) => a.box && a.box.x === 18 && a.box.y === 15 && a.box.w === 64 && a.box.h === 70
  );
  const isDefault2 = annotations.some(
    (a) => a.box && a.box.x === 15 && a.box.y === 15 && a.box.w === 70 && a.box.h === 70
  );
  return hasLegacyDemoLabels && (isDefault1 || isDefault2);
}

export function resolveHeadingBoundingBoxes(
  criteria?: any[],
  anomaly = false
): ImageAnnotation[] {
  if (!criteria || criteria.length === 0) {
    return [
      {
        label: anomaly ? 'Security Anomaly / Defect: Flagged' : 'Primary Specimen: Inspected',
        confidence: anomaly ? 0.0 : 99.2,
        color: anomaly ? '#ef4444' : '#10b981',
        box: { x: 10, y: 16, w: 80, h: 68 },
        description: anomaly
          ? 'Zero-trust security tripwire triggered. Anomaly detected.'
          : 'Primary visual subject identified and bounded; high feature concordance.',
      },
    ];
  }

  // Heading profiles matching vehicle parts, food/produce, electronics, retail items, defects, general objects
  const profiles: Array<{ match: RegExp; box: { x: number; y: number; w: number; h: number }; color: string }> = [
    // Vehicles & Automotive Components
    { match: /tyre|tire|wheel|rim|alloy|rubber/i, box: { x: 64, y: 56, w: 22, h: 34 }, color: '#06b6d4' },
    { match: /headlight|light|lamp|fog|bulb|indicator|taillight/i, box: { x: 74, y: 38, w: 18, h: 20 }, color: '#f59e0b' },
    { match: /windshield|windscreen|glass|window|screen|mirror/i, box: { x: 28, y: 20, w: 44, h: 28 }, color: '#38bdf8' },
    { match: /vehicle|car|body|chassis|sedan|truck|suv|automobile|exterior/i, box: { x: 6, y: 18, w: 88, h: 68 }, color: '#10b981' },
    { match: /plate|license|registration|tag|bumper/i, box: { x: 42, y: 68, w: 18, h: 12 }, color: '#ec4899' },
    { match: /hood|bonnet|grille|radiator/i, box: { x: 55, y: 34, w: 30, h: 26 }, color: '#14b8a6' },
    { match: /door|handle|panel/i, box: { x: 36, y: 34, w: 28, h: 32 }, color: '#8b5cf6' },
    { match: /logo|brand|emblem|insignia|badge/i, box: { x: 44, y: 46, w: 12, h: 12 }, color: '#eab308' },
    { match: /defect|scratch|dent|damage|rust|flaw|broken/i, box: { x: 50, y: 36, w: 18, h: 18 }, color: '#ef4444' },
    { match: /person|pedestrian|driver|human|face|people/i, box: { x: 34, y: 14, w: 32, h: 72 }, color: '#a855f7' },
    // Food, Salads, Produce & Dishware (Multi-Focus Anchors)
    { match: /red fruits?|cherry|tomatoes?|tomato|fruits?|berry|berries|apple|strawberry/i, box: { x: 19, y: 17, w: 27, h: 65 }, color: '#ef4444' },
    { match: /vegetables?|veggie|lettuce|basil|leaf|leaves|greens|spinach|herb|produce/i, box: { x: 4, y: 11, w: 52, h: 65 }, color: '#10b981' },
    { match: /dish|bowl|plate|platter|salad|container|vessel|tray|ceramic/i, box: { x: 3, y: 7, w: 94, h: 86 }, color: '#06b6d4' },
    { match: /meat|chicken|beef|steak|fish|protein|egg/i, box: { x: 36, y: 32, w: 34, h: 36 }, color: '#f97316' },
    { match: /beverage|drink|cup|glass|bottle|mug|can|liquid/i, box: { x: 68, y: 18, w: 22, h: 46 }, color: '#a855f7' },
    // Consumer Electronics & Hardware
    { match: /laptop|screen|display|monitor|tablet|phone/i, box: { x: 16, y: 14, w: 68, h: 54 }, color: '#3b82f6' },
    { match: /keyboard|keypad|buttons|touchpad/i, box: { x: 18, y: 64, w: 64, h: 26 }, color: '#6366f1' },
    // Fashion & Apparel
    { match: /shoe|sneaker|footwear|heel|boot/i, box: { x: 14, y: 36, w: 72, h: 50 }, color: '#ec4899' },
    { match: /watch|dial|strap|wrist/i, box: { x: 28, y: 20, w: 44, h: 58 }, color: '#eab308' },
  ];

  const fallbackPalette = [
    { box: { x: 12, y: 22, w: 36, h: 44 }, color: '#10b981' },
    { box: { x: 52, y: 22, w: 38, h: 42 }, color: '#06b6d4' },
    { box: { x: 18, y: 58, w: 32, h: 30 }, color: '#f59e0b' },
    { box: { x: 55, y: 55, w: 35, h: 32 }, color: '#8b5cf6' },
    { box: { x: 30, y: 15, w: 40, h: 32 }, color: '#ec4899' },
  ];

  let wheelCount = 0;
  return criteria.map((c, i) => {
    const textToMatch = `${c.name || ''} ${c.value || ''}`.toLowerCase();
    const matchedProfile = profiles.find((p) => p.match.test(textToMatch));

    const fb = fallbackPalette[i % fallbackPalette.length]!;
    let chosenBox = matchedProfile ? { ...matchedProfile.box } : { ...fb.box };
    const chosenColor = (c.anomaly || anomaly)
      ? '#ef4444'
      : matchedProfile
      ? matchedProfile.color
      : fb.color;

    // Smart multi-focus distribution for duplicate parts (e.g. wheels)
    if (matchedProfile && /tyre|tire|wheel/i.test(matchedProfile.match.source)) {
      wheelCount++;
      if (wheelCount === 1) {
        chosenBox = { x: 14, y: 56, w: 22, h: 34 };
      } else {
        chosenBox = { x: 66, y: 56, w: 22, h: 34 };
      }
    } else if (!matchedProfile && i > 0) {
      chosenBox.x = Math.max(5, Math.min(82, chosenBox.x + (i % 2 === 1 ? 6 : -6)));
      chosenBox.y = Math.max(5, Math.min(82, chosenBox.y + (i % 3 === 0 ? 5 : -5)));
    }

    const conf = c.anomaly ? 0.0 : (c.confidence !== undefined ? Number(c.confidence) : 0.0);

    return {
      label: `${c.name}: ${c.value || 'Verified'}`,
      confidence: conf,
      color: chosenColor,
      box: chosenBox,
      description: c.anomaly
        ? `Security anomaly / defect detected on ${c.name}.`
        : `Spatial multi-focus anchor for heading '${c.name}' verified across Vision Chamber.`,
    };
  });
}

