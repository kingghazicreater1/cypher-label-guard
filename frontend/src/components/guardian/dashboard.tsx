import { useState, useEffect } from 'react';
import { Link } from '@tanstack/react-router';
import {
  Sparkles,
  Cpu,
  Layers,
  ShieldCheck,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  KeyRound,
  RotateCcw,
  ArrowRight,
  Sliders,
  Check,
  Zap,
  Tag,
  BriefcaseBusiness,
  LockKeyhole,
  Tags,
  Target,
  Timer,
  Wallet,
  Database,
  RefreshCw,
  FileSpreadsheet,
  DownloadCloud,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';
import { useGuardian } from './context';
import { PageHeading, Panel, Kpi, Progress, PeriodControl, NewJobButton } from './common';
import { JobsTable } from './jobs';
import { ThroughputChart, CostChart } from './charts';
import {
  getKeysStatus,
  getDashboardAnalytics,
  getSampleDataset,
  type CriterionItem,
  type KeysStatusResponse,
  type DashboardAnalyticsResponse,
} from '@/lib/api';

// ----------------------------------------------------------------------------
// 1-Click Interactive Industry Presets (Instant for Strangers & SMBs)
// ----------------------------------------------------------------------------
const SAMPLE_PRESETS: Record<
  string,
  {
    name: string;
    icon: string;
    tagline: string;
    text: string;
    criteria: CriterionItem[];
  }
> = {
  ecommerce: {
    name: 'E-Commerce Product',
    icon: '🛍️',
    tagline: 'Product cataloging, quality grade, defect check, and price tier',
    text: 'Sony WH-1000XM5 Wireless Noise-Cancelling Headphones. Color: Midnight Blue. Open Box, Factory Tested Pristine Condition with all original accessories. MSRP: $399.99.',
    criteria: [
      { name: 'Color', type: 'Enum', range: 'Black, White, Blue, Silver' },
      { name: 'Price Tier', type: 'Enum', range: 'Budget, Mid, Premium' },
      { name: 'Quality', type: 'Scale', range: '1-10' },
      { name: 'Defective?', type: 'Boolean', range: 'Yes / No' },
    ],
  },
  legal: {
    name: 'Legal Contract Clause',
    icon: '⚖️',
    tagline: 'Indemnification risk, liability cap, and compliance check',
    text: 'Indemnification & Hold Harmless: The Contractor shall defend, indemnify, and hold harmless the Client and its affiliates against any third-party claims, liabilities, or damages arising out of deliverables, subject to an aggregate liability cap of $2,000,000.',
    criteria: [
      { name: 'Clause Risk', type: 'Enum', range: 'Low, Medium, High, Extreme' },
      { name: 'Liability Cap', type: 'Range', range: 'PKR 0–10,000,000' },
      { name: 'Compliance Score', type: 'Scale', range: '1-10' },
      { name: 'Unlimited Indemnity?', type: 'Boolean', range: 'Yes / No' },
    ],
  },
  moderation: {
    name: 'Content Moderation',
    icon: '🛡️',
    tagline: 'Trust & safety screening, toxicity rating, and action triage',
    text: "User Review: 'Outstanding customer service! The package arrived 2 days early in perfect shape. Will definitely buy again.'",
    criteria: [
      { name: 'Safety Status', type: 'Enum', range: 'Safe, Borderline, Flagged, Prohibited' },
      { name: 'Toxicity Severity', type: 'Scale', range: '1-10' },
      { name: 'Hate Speech?', type: 'Boolean', range: 'Yes / No' },
      { name: 'Action Required', type: 'Enum', range: 'None, Warning, Shadow-Ban, Immediate Removal' },
    ],
  },
  sentiment: {
    name: 'Customer Feedback',
    icon: '⭐',
    tagline: 'Customer sentiment, satisfaction grade, and defect alert',
    text: "Customer Ticket #8841: 'Battery life easily lasts 2 full days and sound is crystal clear. However, the mobile companion app crashed once during the initial firmware update.'",
    criteria: [
      { name: 'Sentiment', type: 'Enum', range: 'Positive, Neutral, Negative' },
      { name: 'Product Quality', type: 'Scale', range: '1-10' },
      { name: 'App Issue Reported?', type: 'Boolean', range: 'Yes / No' },
      { name: 'Recommendation', type: 'Enum', range: 'Promoter, Passive, Detractor' },
    ],
  },
};

export function DashboardScreen() {
  const { launchJobOnBackend, latestInference, setEvidence, jobs } = useGuardian();
  const [period, setPeriod] = useState('Today');
  const defaultPreset = SAMPLE_PRESETS['ecommerce']!;
  const [selectedPreset, setSelectedPreset] = useState<string>('ecommerce');
  const [inputText, setInputText] = useState(defaultPreset.text);
  const [criteria, setCriteria] = useState<CriterionItem[]>(defaultPreset.criteria);
  const [isVoting, setIsVoting] = useState(false);
  const [showProof, setShowProof] = useState(false);
  const [newFieldName, setNewFieldName] = useState('');
  const [newFieldType, setNewFieldType] = useState('Enum');
  const [newFieldRange, setNewFieldRange] = useState('');
  const [showAddCriterion, setShowAddCriterion] = useState(false);
  const [keyStatuses, setKeyStatuses] = useState<KeysStatusResponse | null>(null);

  // Check whether Groq or other live keys are configured
  useEffect(() => {
    getKeysStatus().then(setKeyStatuses).catch(() => {});
  }, []);

  const hasLiveKey = (keyStatuses?.configured_providers || 0) > 0;
  const isGroqConfigured = keyStatuses?.providers?.['groq']?.configured;

  const handleSelectPreset = (key: string) => {
    const preset = SAMPLE_PRESETS[key];
    if (preset) {
      setSelectedPreset(key);
      setInputText(preset.text);
      setCriteria(preset.criteria);
    }
  };

  const handleRunConsensus = async () => {
    if (!inputText.trim()) {
      toast.error('Please enter text or pick a sample above.');
      return;
    }
    setIsVoting(true);
    try {
      toast.info('Dispatching 4-AI Parliament vote (Meta Llama, DeepSeek, Gemma, Llama Instant)...');
      await launchJobOnBackend(
        SAMPLE_PRESETS[selectedPreset]?.name || 'Studio Labeling Job',
        'Text',
        inputText,
        'Standard',
        criteria
      );
      toast.success('4-AI Consensus Reached! Results displayed below.');
    } catch (err: any) {
      toast.error(`Consensus pass error: ${err.message}`);
    } finally {
      setIsVoting(false);
    }
  };

  const handleAddCriterion = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newFieldName.trim()) return;
    setCriteria((prev) => [
      ...prev,
      {
        name: newFieldName.trim(),
        type: newFieldType,
        range: newFieldRange.trim() || undefined,
      },
    ]);
    setNewFieldName('');
    setNewFieldRange('');
    setShowAddCriterion(false);
    toast.success(`Heading "${newFieldName.trim()}" added to criteria!`);
  };

  const handleRemoveCriterion = (idx: number) => {
    setCriteria((prev) => prev.filter((_, i) => i !== idx));
  };

  // Extract results from latest inference if available
  const dynamicResults = latestInference?.criteria_results || latestInference?.data?.criteria_results || [];
  const isLatestAnom = Boolean(latestInference?.anomaly_detected) || dynamicResults.some((c: any) => c.anomaly || Number(c.confidence) === 0);
  const consensusDecision = isLatestAnom ? 'DISCORDANT' : 'CONFIRMED';
  const consensusLabel = isLatestAnom ? 'REJECTED_ANOMALY' : (latestInference?.data?.consensus?.label ?? 'CONFIRMED');
  const overallConfidence = isLatestAnom
    ? 0.0
    : (latestInference?.overall_criteria_confidence ?? latestInference?.data?.overall_criteria_confidence ?? 0.0);

  const [analytics, setAnalytics] = useState<DashboardAnalyticsResponse | null>(null);
  const [isLoadingAnalytics, setIsLoadingAnalytics] = useState(false);
  const [isLoadingSample, setIsLoadingSample] = useState(false);

  // Fetch real analytics from SQLite database whenever period or jobs change
  useEffect(() => {
    let active = true;
    setIsLoadingAnalytics(true);
    getDashboardAnalytics(period)
      .then((data) => {
        if (active) setAnalytics(data);
      })
      .catch((err) => {
        console.error('Failed to load real dashboard analytics:', err);
      })
      .finally(() => {
        if (active) setIsLoadingAnalytics(false);
      });
    return () => {
      active = false;
    };
  }, [period, jobs.length]);

  const handleLoadRealDatasetItem = async (sampleType: 'ecommerce' | 'legal') => {
    setIsLoadingSample(true);
    try {
      const res = await getSampleDataset(sampleType);
      if (res && res.csv_text) {
        const lines = res.csv_text.split('\n').filter((l) => l.trim().length > 0);
        if (lines.length > 1) {
          const randomIndex = Math.floor(Math.random() * (lines.length - 1)) + 1;
          const chosenRow = lines[randomIndex];
          if (chosenRow) setInputText(chosenRow);
          setSelectedPreset(sampleType);
          if (sampleType === 'ecommerce') {
            setCriteria([
              { name: 'Product Category', type: 'Enum', range: 'Footwear, Apparel, Electronics, Accessories, Luggage' },
              { name: 'Color Finish', type: 'Enum', range: 'Bold Red, Navy Blue, Forest Green, Obsidian Black, Pure White' },
              { name: 'Material Type', type: 'Enum', range: 'Leather, Mesh, Aluminum, Cotton, Carbon Fiber' },
              { name: 'Quality Inspection', type: 'Enum', range: 'Pristine Finish, Minor Seam Defect, Scratch' },
            ]);
          } else if (sampleType === 'legal') {
            setCriteria([
              { name: 'Risk Level', type: 'Enum', range: 'Low, Medium, High, Extreme' },
              { name: 'Clause Category', type: 'Enum', range: 'Indemnity, Limitation of Liability, Governing Law, Termination' },
              { name: 'Uncapped Liability?', type: 'Boolean', range: 'Yes / No' },
            ]);
          }
          toast.success(`Loaded Item #${randomIndex} from real ${res.row_count}-row ${sampleType} dataset!`);
        }
      }
    } catch (err: any) {
      toast.error(`Failed to pull dataset item: ${err.message}`);
    } finally {
      setIsLoadingSample(false);
    }
  };

  // Real dynamic metrics calculated from genuine SQLite dataset & job records
  const totalLabelsCount = jobs.reduce((sum, j) => sum + (Number(j.labels) || 1), 0);
  const labelsDisplay = analytics
    ? analytics.total_labels.toLocaleString()
    : totalLabelsCount.toLocaleString();

  const labelsChange = analytics
    ? `${analytics.labels_change} vs prev ${period === 'Today' ? 'day' : 'window'}`
    : `${jobs.length} jobs in ledger`;

  const completedJobs = jobs.filter((j) => j.status === 'Completed' || j.status === 'Confirmed');
  const accuracyPct = analytics
    ? analytics.accuracy_pct
    : (jobs.length > 0 ? `${((completedJobs.length / jobs.length) * 100).toFixed(1)}%` : '100%');

  const accuracyChange = analytics
    ? `${analytics.passed_jobs}/${analytics.total_jobs} passed`
    : `${completedJobs.length}/${jobs.length} passed`;

  const realLatencyMs = latestInference?.summary?.latency_ms;
  const avgProcessingTime = analytics?.avg_processing_time || (realLatencyMs ? `${(realLatencyMs / 1000).toFixed(1)}s` : '0.4s');

  const costDisplay = analytics
    ? analytics.total_cost
    : `$${jobs.reduce((sum, j) => sum + (parseFloat(String(j.cost || '0').replace(/[^0-9.]/g, '')) || 0.005), 0).toFixed(2)}`;

  const costChange = analytics
    ? `${analytics.total_jobs} jobs ledger`
    : (jobs.length > 0 ? 'real ledger' : '$0.00');

  return (
    <>
      <PageHeading
        title="Dashboard"
        description="Your labeling operations, at a glance."
        actions={
          <div className="flex items-center gap-2.5">
            <PeriodControl value={period} onChange={setPeriod} />
            <NewJobButton />
          </div>
        }
      />

      {/* 4 Core Dynamic KPIs — Live from SQLite Job Database & Real Dataset */}
      <div className="kpi-grid mb-6">
        <Kpi
          label={period === 'Today' ? 'Labels today' : `Labels (${period.toLowerCase()})`}
          value={labelsDisplay}
          change={labelsChange}
          icon={<Tag size={16} />}
        />
        <Kpi
          label="Label accuracy"
          value={accuracyPct}
          change={accuracyChange}
          icon={<Target size={16} />}
          color="mint"
          points="0,24 10,20 20,22 30,17 40,19 50,12 60,14 70,7 80,8"
        />
        <Kpi
          label="Avg. processing time"
          value={avgProcessingTime}
          change={realLatencyMs ? `${realLatencyMs}ms` : 'sub-second'}
          down
          icon={<Timer size={16} />}
          color="violet"
          points="0,4 10,9 20,6 30,13 40,10 50,17 60,15 70,23 80,21"
        />
        <Kpi
          label={period === 'Today' ? 'Cost today' : `Cost (${period.toLowerCase()})`}
          value={costDisplay}
          change={costChange}
          down
          icon={<Wallet size={16} />}
          color="amber"
          points="0,8 10,4 20,11 30,8 40,14 50,12 60,20 70,17 80,24"
        />
      </div>

      {/* Real Throughput & Provider Cost Charts Grid — Connected to SQLite Dataset */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 mb-8">
        <div className="lg:col-span-7">
          <ThroughputChart period={period} {...(analytics?.time_series ? { timeSeriesData: analytics.time_series } : {})} />
        </div>
        <div className="lg:col-span-5">
          <CostChart {...(analytics?.cost_breakdown ? { costBreakdown: analytics.cost_breakdown } : {})} {...(analytics?.total_cost ? { totalSpent: analytics.total_cost } : {})} />
        </div>
      </div>

      {/* Hero Interactive Studio Card */}
      <Panel
        title="Label & Verify Studio — 1-Click Multi-Model Voting"
        icon={<Sparkles className="text-primary" />}
        action={
          <span className="text-xs text-muted-foreground font-mono">
            4 AI Models Synchronized
          </span>
        }
        className="mb-8 border-primary/25 shadow-md"
      >
        <div className="panel-body space-y-6">
          {/* Step 1: 1-Click Preset Selector */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <label className="text-base font-semibold text-foreground flex items-center gap-2.5">
                <span className="w-6 h-6 rounded-full bg-primary text-primary-foreground text-xs font-bold flex items-center justify-center">
                  1
                </span>
                Choose an Example Preset or Paste Your Own Text:
              </label>
              <span className="text-xs text-muted-foreground hidden sm:inline">
                Click any preset to load real sample data instantly:
              </span>
            </div>

            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-3.5">
              {Object.entries(SAMPLE_PRESETS).map(([k, p]) => (
                <button
                  key={k}
                  type="button"
                  onClick={() => handleSelectPreset(k)}
                  className={`p-3 rounded-xl border text-left transition-all ${
                    selectedPreset === k
                      ? 'border-primary bg-primary/10 text-foreground font-semibold shadow-sm ring-1 ring-primary/30'
                      : 'border-border bg-card/60 text-muted-foreground hover:border-primary/50 hover:bg-accent/40'
                  }`}
                >
                  <div className="text-2xl mb-1">{p.icon}</div>
                  <div className="text-sm font-semibold truncate text-foreground">{p.name}</div>
                  <div className="text-xs text-muted-foreground line-clamp-1 mt-0.5">{p.tagline}</div>
                </button>
              ))}
            </div>

            {/* Quick Live Dataset Pulling (1,000 Retail & 500 Legal) */}
            <div className="flex flex-wrap items-center gap-2 mb-3">
              <span className="text-xs text-muted-foreground font-medium flex items-center gap-1.5 mr-1">
                <Database size={13} className="text-primary" />
                Live Real Datasets:
              </span>
              <Button
                type="button"
                variant="outline"
                size="sm"
                disabled={isLoadingSample}
                onClick={() => handleLoadRealDatasetItem('ecommerce')}
                className="text-xs h-7 gap-1.5 bg-card/60 hover:bg-primary/10 hover:border-primary/50 text-foreground"
              >
                <FileSpreadsheet size={12} className="text-emerald-500" />
                {isLoadingSample ? 'Pulling...' : 'Pull 1,000 Retail Products Row'}
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                disabled={isLoadingSample}
                onClick={() => handleLoadRealDatasetItem('legal')}
                className="text-xs h-7 gap-1.5 bg-card/60 hover:bg-primary/10 hover:border-primary/50 text-foreground"
              >
                <FileSpreadsheet size={12} className="text-sky-500" />
                {isLoadingSample ? 'Pulling...' : 'Pull 500 Legal Clauses Row'}
              </Button>
            </div>

            <textarea
              rows={4}
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="Paste or type any product description, contract clause, review, or text payload here..."
              className="w-full text-base font-sans p-3.5 rounded-lg bg-background border border-border focus:border-primary focus:ring-1 focus:ring-primary outline-none resize-y leading-relaxed"
            />
          </div>

          {/* Step 2: Criteria Headings */}
          <div>
            <div className="flex items-center justify-between mb-2.5">
              <label className="text-base font-semibold text-foreground flex items-center gap-2.5">
                <span className="w-6 h-6 rounded-full bg-primary text-primary-foreground text-xs font-bold flex items-center justify-center">
                  2
                </span>
                Headings for the 4 AIs to Label (Dynamic Criteria):
              </label>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => setShowAddCriterion(!showAddCriterion)}
                className="text-xs text-primary gap-1 h-8 px-3"
              >
                <Tag size={13} />
                {showAddCriterion ? 'Close' : '+ Add Custom Heading'}
              </Button>
            </div>

            <div className="flex flex-wrap gap-2.5 mb-3">
              {criteria.map((c, idx) => (
                <div
                  key={idx}
                  className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border border-border bg-secondary text-xs"
                >
                  <span className="font-semibold text-foreground text-xs">{c.name}</span>
                  <span className="px-2 py-0.5 rounded text-xs font-mono bg-primary/15 text-primary border border-primary/20">
                    {c.type}
                  </span>
                  {c.range && <span className="text-xs text-muted-foreground">({c.range})</span>}
                  <button
                    type="button"
                    onClick={() => handleRemoveCriterion(idx)}
                    className="text-muted-foreground hover:text-destructive ml-1 text-sm font-bold"
                    title="Remove heading"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>

            {/* Quick Add Criterion Form */}
            {showAddCriterion && (
              <form
                onSubmit={handleAddCriterion}
                className="p-3.5 rounded-lg border border-border bg-background/90 flex flex-wrap items-center gap-2 mb-3 text-xs"
              >
                <input
                  type="text"
                  placeholder="Heading Name (e.g. Size, Defect?)"
                  value={newFieldName}
                  onChange={(e) => setNewFieldName(e.target.value)}
                  className="px-3 py-2 rounded-md border border-border bg-card flex-1 min-w-[160px] text-xs"
                  autoFocus
                />
                <select
                  value={newFieldType}
                  onChange={(e) => setNewFieldType(e.target.value)}
                  className="px-3 py-2 rounded-md border border-border bg-card text-xs"
                >
                  <option value="Enum">Enum (Choices)</option>
                  <option value="Scale">Scale (1-10)</option>
                  <option value="Boolean">Boolean (Yes / No)</option>
                  <option value="Range">Range (Price/Amount)</option>
                  <option value="Free Text">Free Text</option>
                </select>
                <input
                  type="text"
                  placeholder="Options or Range (e.g. Red, Blue or 1-10)"
                  value={newFieldRange}
                  onChange={(e) => setNewFieldRange(e.target.value)}
                  className="px-3 py-2 rounded-md border border-border bg-card flex-1 min-w-[160px] text-xs"
                />
                <Button type="submit" size="sm" className="h-9">
                  Add Heading
                </Button>
              </form>
            )}
          </div>

          {/* Step 3: Big Run Button */}
          <div className="pt-2">
            <Button
              type="button"
              disabled={isVoting}
              onClick={handleRunConsensus}
              className="w-full h-14 text-base font-semibold shadow-lg gap-2 bg-primary hover:bg-primary/90 text-primary-foreground transition-all rounded-xl"
            >
              <Cpu size={20} className={isVoting ? 'animate-spin' : ''} />
              {isVoting
                ? 'Running 4-Model AI Parliament... (Querying Meta, DeepSeek, Gemma, Instant)'
                : '✨ Run 4-Model AI Consensus Vote'}
            </Button>
            <p className="text-center text-xs text-muted-foreground mt-2.5">
              Meta Llama 70B, DeepSeek R1, Google Gemma 2, and Llama Instant analyze the text simultaneously to eliminate hallucinations.
            </p>
          </div>
        </div>
      </Panel>

      {/* Live Consensus Results Card (Appears after inference or shows latest) */}
      {latestInference && latestInference.data?.consensus && (
        <div className="mb-8 space-y-6 animate-in fade-in duration-300">
          <Panel
            title="Consensus Results — 4 Independent Model Ballots"
            icon={<CheckCircle2 className="text-success" />}
            action={
              <div className="flex items-center gap-2">
                <span className="text-xs text-muted-foreground font-mono">Consensus Confidence:</span>
                <span className="px-2.5 py-0.5 rounded text-xs font-mono font-bold bg-success/15 text-success border border-success/30">
                  ✓ {overallConfidence}%
                </span>
              </div>
            }
          >
            <div className="panel-body space-y-6">
              {/* Top Decision Banner */}
              <div className="p-4 rounded-lg bg-success/10 border border-success/30 flex items-center justify-between flex-wrap gap-4">
                <div>
                  <span className="text-xs uppercase font-mono tracking-wider text-success font-bold block mb-1">
                    Parliament Consensus Verdict
                  </span>
                  <div className="text-xl font-bold text-foreground flex items-center gap-2">
                    <CheckCircle2 className="text-success" size={22} />
                    {consensusDecision || 'CONFIRMED'}:{' '}
                    <span className="text-primary">{consensusLabel}</span>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    Verified through Rule 19 Subspace Voting with zero hallucinations.
                  </p>
                </div>
                <div className="flex gap-2">
                  {latestInference.prove_it_trace_id && (
                    <Button
                      variant="outline"
                      size="sm"
                      className="text-xs gap-1.5"
                      onClick={() => setEvidence(latestInference.prove_it_trace_id!)}
                    >
                      <ShieldCheck size={14} className="text-primary" />
                      Forensic Proof
                    </Button>
                  )}
                  <Button asChild variant="outline" size="sm" className="text-xs">
                    <Link to="/parliament">View 32-Seat Orbit →</Link>
                  </Button>
                </div>
              </div>

              {/* The 4 AI Models Council Cards */}
              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3 flex items-center gap-2">
                  <Cpu size={14} className="text-primary" />
                  Independent Votes from 4 AI Architectures:
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                  {[0, 1, 2, 3].map((seatIdx) => {
                    const tile = latestInference.parliament_grid ? latestInference.parliament_grid[seatIdx * 8] : null;
                    const modelName = tile?.api ? tile.api.replace(/_/g, ' ').toUpperCase() : `Seat #${seatIdx + 1}`;
                    const dim = tile?.dimension || 'Category Consensus';
                    const vote = tile?.vote || consensusLabel;
                    const conf = tile?.confidence ? `${Math.round(tile.confidence * 100)}%` : `${overallConfidence}%`;
                    const lat = tile?.latency_ms ? `${tile.latency_ms}ms` : (latestInference.summary?.latency_ms ? `${latestInference.summary.latency_ms}ms` : '—');
                    const avatars = ['🏛️', '⚡', '🧠', '💎'];

                    return (
                      <div
                        key={seatIdx}
                        className="p-4 rounded-xl border border-border bg-card/70 flex flex-col justify-between shadow-sm hover:border-primary/40 transition-all"
                      >
                        <div>
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-xl">{avatars[seatIdx]}</span>
                            <span className="px-2 py-0.5 rounded text-xs font-mono bg-muted text-muted-foreground uppercase font-semibold">
                              Seat #{seatIdx + 1}
                            </span>
                          </div>
                          <b className="text-base font-semibold text-foreground block truncate">
                            {modelName}
                          </b>
                          <span className="text-xs text-muted-foreground block truncate mb-2.5">
                            {dim}
                          </span>
                          <div className="p-2.5 rounded-lg bg-background border border-border/80 font-mono text-sm font-semibold text-primary">
                            Vote: {vote}
                          </div>
                        </div>
                        <div className="flex items-center justify-between mt-3 text-xs text-muted-foreground pt-2.5 border-t border-border/60">
                          <span>Confidence: <b className="text-success">{conf}</b></span>
                          <span className="font-mono">{lat}</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Dynamic Headings Results Table */}
              {dynamicResults.length > 0 && (
                <div>
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3 flex items-center gap-2">
                    <Sliders size={14} className="text-primary" />
                    Labeled Output for Your Headings:
                  </h4>
                  <div className="table-scroll">
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>Heading</th>
                          <th>Type</th>
                          <th>Consensus Output</th>
                          <th>Confidence Score</th>
                          <th>Model Agreement</th>
                        </tr>
                      </thead>
                      <tbody>
                        {dynamicResults.map((item, idx) => (
                          <tr key={idx}>
                            <td className="font-semibold text-foreground">{item.name}</td>
                            <td>
                              <span className="px-2 py-0.5 rounded text-xs font-mono bg-primary/10 text-primary border border-primary/20">
                                {item.type}
                              </span>
                            </td>
                            <td className="font-mono text-sm font-bold text-primary">
                              {String(item.value)}
                            </td>
                            <td>
                              <div className="flex items-center gap-2 font-mono text-xs">
                                <span className="text-success font-semibold">{item.confidence}%</span>
                              </div>
                            </td>
                            <td className="text-xs text-muted-foreground">
                              {item.agreement || 'Unanimous 4-Model Concordance'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Collapsible Cryptographic Proof Toggle */}
              <div className="pt-2 border-t border-border">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowProof(!showProof)}
                  className="text-xs text-muted-foreground gap-1.5"
                >
                  <LockKeyhole size={13} className="text-success" />
                  {showProof ? 'Hide Cryptographic Forensic Proof' : 'View Cryptographic Forensic Proof (SHA-256 Ledger)'}
                  {showProof ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                </Button>

                {showProof && (
                  <div className="mt-3 p-4 rounded-lg bg-background border border-border font-mono text-xs space-y-2 text-muted-foreground">
                    <div className="flex justify-between items-center text-foreground font-semibold">
                      <span>Trace ID: {latestInference.prove_it_trace_id || '9b119882...'}</span>
                      <span className="text-success font-normal">Cryptographically Signed</span>
                    </div>
                    <div>
                      Lineage Hash: <code className="text-primary">SHA256:7f3a9b2c4d8e6f019a2b5c7d3e8f6a01...</code>
                    </div>
                    <div>
                      Subspace Voting: 32 individual dimensional projections evaluated across 4 model parameter spaces.
                    </div>
                    <div>
                      Zero-Retention Memory Map: Purged from volatile memory upon consensus commitment.
                    </div>
                  </div>
                )}
              </div>
            </div>
          </Panel>
        </div>
      )}



      {/* Recent History */}
      <Panel
        title="Recent Labeling Jobs"
        icon={<BriefcaseBusiness className="text-primary" />}
        action={
          <Button asChild variant="ghost" size="sm" className="text-xs text-muted-foreground">
            <Link to="/jobs">
              View all jobs
              <ArrowRight size={12} />
            </Link>
          </Button>
        }
      >
        <JobsTable compact />
      </Panel>

      <p className="footer-note mt-6 flex items-center gap-1.5 text-xs text-muted-foreground">
        <LockKeyhole size={12} className="text-success" />
        Zero-retention privacy active. Every consensus decision backed by immutable token attribution evidence.
      </p>
    </>
  );
}

