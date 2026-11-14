import { useState, useEffect, type FormEvent, type MouseEvent } from 'react';
import {
  Check,
  ChevronDown,
  ChevronUp,
  Copy,
  Eye,
  Printer,
  RotateCcw,
  ShieldCheck,
  Sliders,
  Sparkles,
  X,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';
import {
  copyTextToClipboard,
  formatProductCopyBlock,
  getCriterionTier,
  getDisplayHeading,
  getLocalThumbnail,
  getProductTier,
  normalizeHeadingKey,
  suggestStoreAlias,
  type HeadingAliasMap,
} from '../../lib/label-utils';

export interface ResultFieldItem {
  name?: string | undefined;
  heading?: string | undefined;
  value?: any;
  winning_label?: any;
  confidence?: number | string | undefined;
  agreement?: string | undefined;
  anomaly?: boolean | undefined;
  anomaly_reason?: string | undefined;
}

export interface CopyableResultCardProps {
  title: string;
  subtitle?: string | undefined;
  thumbnailUrl?: string | null | undefined;
  secondaryThumbKey?: string | null | undefined;
  status?: string | undefined;
  decision?: string | undefined;
  overallConfidence?: number | string | undefined;
  votes?: string | undefined;
  traceId?: string | undefined;
  lineageHash?: string | undefined;
  anomalyDetected?: boolean | undefined;
  error?: string | undefined;
  criteria: ResultFieldItem[];
  aliases?: HeadingAliasMap | undefined;
  compact?: boolean | undefined;
  onOpenFull?: (() => void) | undefined;
  onPrintCatalog?: (() => void) | undefined;
}

export function CopyableResultCard({
  title,
  subtitle,
  thumbnailUrl,
  secondaryThumbKey,
  status,
  decision,
  overallConfidence,
  votes,
  traceId,
  lineageHash,
  anomalyDetected,
  error,
  criteria,
  aliases,
  compact = false,
  onOpenFull,
  onPrintCatalog,
}: CopyableResultCardProps) {
  const [copiedFieldIdx, setCopiedFieldIdx] = useState<number | null>(null);
  const [copiedAll, setCopiedAll] = useState(false);
  const [showAuditDetails, setShowAuditDetails] = useState(false);

  const normalizedFields = (criteria || []).map((c, idx) => {
    const origHeading = (c.heading || c.name || `Field ${idx + 1}`).trim();
    const rawVal = c.winning_label !== undefined && c.winning_label !== '' ? c.winning_label : c.value;
    const valStr = String(rawVal ?? '').trim();
    return {
      origHeading,
      displayHeading: getDisplayHeading(origHeading, aliases),
      value: valStr,
      confidence: c.confidence,
      agreement: c.agreement,
      anomaly: Boolean(c.anomaly),
      anomaly_reason: c.anomaly_reason,
    };
  });

  const thumb = getLocalThumbnail(title, thumbnailUrl || undefined, secondaryThumbKey);
  const prodTier = getProductTier({
    status,
    decision,
    overall_confidence: overallConfidence,
    anomaly_detected: anomalyDetected,
    criteria_results: criteria,
  });

  const isFailed = String(status || '').toUpperCase() === 'FAILED';

  const handleCopyField = async (e: MouseEvent, idx: number, heading: string, val: string) => {
    e.stopPropagation();
    const ok = await copyTextToClipboard(val);
    if (ok) {
      setCopiedFieldIdx(idx);
      toast.success(`Copied ${heading}`);
      setTimeout(() => setCopiedFieldIdx((cur) => (cur === idx ? null : cur)), 1800);
    } else {
      toast.error('Clipboard copy blocked by browser');
    }
  };

  const handleCopyAll = async (e: MouseEvent) => {
    e.stopPropagation();
    const block = formatProductCopyBlock(
      normalizedFields.map((f) => ({ heading: f.origHeading, value: f.value })),
      aliases
    );
    if (!block) {
      toast.error('No copyable fields on this item yet');
      return;
    }
    const ok = await copyTextToClipboard(block);
    if (ok) {
      setCopiedAll(true);
      toast.success(`Copied all fields for ${title}`);
      setTimeout(() => setCopiedAll(false), 2000);
    } else {
      toast.error('Clipboard copy blocked by browser');
    }
  };

  return (
    <div
      className={`rounded-xl border-2 ${prodTier.borderClass} bg-card/90 shadow-xs transition-all overflow-hidden`}
    >
      {/* Top Header Strip */}
      <div className={`px-3.5 py-2.5 border-b border-border/60 ${prodTier.bgClass} flex flex-wrap items-center justify-between gap-2`}>
        <div className="flex items-center gap-2.5 min-w-0">
          <span className={`h-2.5 w-2.5 rounded-full shrink-0 ${prodTier.dotClass}`} />
          <div className="min-w-0">
            <div className="text-[13.5px] font-bold text-foreground truncate" title={title}>
              {title}
            </div>
            {subtitle && (
              <div className="text-[11px] text-muted-foreground truncate">{subtitle}</div>
            )}
          </div>
        </div>

        <div className="flex items-center gap-1.5 shrink-0 flex-wrap">
          <span
            className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-[11px] font-semibold ${prodTier.badgeClass}`}
          >
            {isFailed ? 'Failed · Refunded' : prodTier.badgeText}
          </span>
          {!isFailed && normalizedFields.length > 0 && (
            <Button
              type="button"
              size="sm"
              variant={copiedAll ? 'default' : 'outline'}
              className={`h-7 px-2.5 text-[11.5px] font-semibold gap-1 ${
                copiedAll ? 'bg-emerald-600 hover:bg-emerald-600 text-white' : ''
              }`}
              onClick={handleCopyAll}
            >
              {copiedAll ? <Check size={12} /> : <Copy size={12} />}
              {copiedAll ? 'Copied All' : 'Copy All'}
            </Button>
          )}
          {onPrintCatalog && !isFailed && (
            <Button
              type="button"
              size="sm"
              variant="outline"
              className="h-7 px-2 text-[11px] gap-1"
              onClick={(e) => {
                e.stopPropagation();
                onPrintCatalog();
              }}
              title="Open 1-page printable photo catalog"
            >
              <Printer size={12} />
            </Button>
          )}
          {onOpenFull && (
            <Button
              type="button"
              size="sm"
              variant="ghost"
              className="h-7 px-2 text-[11.5px] gap-1"
              onClick={(e) => {
                e.stopPropagation();
                onOpenFull();
              }}
            >
              <Eye size={12} />
              Open
            </Button>
          )}
        </div>
      </div>

      {/* Card Body: Thumbnail Left + Copyable Fields Right */}
      <div className={`p-3.5 flex flex-col ${compact ? 'md:flex-row' : 'sm:flex-row'} gap-3.5 items-start`}>
        {/* Thumbnail / Zero-Retention Stub */}
        <div className={`shrink-0 ${compact ? 'w-full sm:w-28' : 'w-full sm:w-32'}`}>
          {thumb ? (
            <div
              onClick={onOpenFull}
              className={`rounded-lg border border-border overflow-hidden bg-muted/30 flex items-center justify-center ${
                onOpenFull ? 'cursor-pointer hover:ring-2 hover:ring-primary/40 transition-all' : ''
              } ${compact ? 'h-28' : 'h-32'}`}
            >
              <img src={thumb} alt={title} className="w-full h-full object-contain p-1" />
            </div>
          ) : (
            <div
              className={`rounded-lg border border-dashed border-border bg-muted/20 flex flex-col items-center justify-center text-center px-2 ${
                compact ? 'h-24' : 'h-28'
              }`}
            >
              <ShieldCheck size={18} className="text-emerald-500/70 mb-1" />
              <span className="text-[10px] font-medium text-muted-foreground leading-tight">
                Zero-Retention
              </span>
              <span className="text-[9.5px] text-muted-foreground/75 leading-tight mt-0.5">
                Photo purged after labeling
              </span>
            </div>
          )}
        </div>

        {/* Fields / Content Area */}
        <div className="flex-1 min-w-0 w-full space-y-2">
          {isFailed ? (
            <div className="rounded-lg border border-rose-500/50 bg-rose-500/10 p-3 text-xs text-rose-300">
              <div className="font-semibold mb-0.5">Photo could not be processed (credits not charged)</div>
              <div className="text-rose-200/80">{error || 'No structured fields returned.'}</div>
            </div>
          ) : normalizedFields.length === 0 ? (
            <div className="rounded-lg border border-border bg-muted/20 p-3 text-xs text-muted-foreground">
              No structured fields recorded yet for this item.
            </div>
          ) : (
            <div className={`grid grid-cols-1 ${compact ? '' : 'lg:grid-cols-2'} gap-2`}>
              {normalizedFields.map((field, idx) => {
                const cTier = getCriterionTier({
                  confidence: field.confidence,
                  anomaly: field.anomaly,
                  value: field.value,
                });
                const isCopied = copiedFieldIdx === idx;
                const isLongText = field.value.length > 75 || field.origHeading.toLowerCase().includes('description') || field.origHeading.toLowerCase().includes('why');
                return (
                  <div
                    key={`${field.origHeading}-${idx}`}
                    className={`rounded-lg border ${cTier.borderClass} ${cTier.bgClass} p-2.5 flex flex-col justify-between gap-1.5 ${
                      isLongText && !compact ? 'lg:col-span-2' : ''
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-1.5 min-w-0 flex-wrap">
                        <span
                          className="text-[11.5px] font-bold text-foreground/95 leading-snug"
                          title={
                            field.displayHeading !== field.origHeading
                              ? `Original key: ${field.origHeading}`
                              : undefined
                          }
                        >
                          {field.displayHeading}
                        </span>
                        <span className={`inline-flex items-center rounded px-1.5 py-0 text-[9.5px] font-semibold border ${cTier.badgeClass}`}>
                          {cTier.shortTag}
                        </span>
                      </div>

                      {field.value && (
                        <button
                          type="button"
                          onClick={(e) => handleCopyField(e, idx, field.displayHeading, field.value)}
                          className={`inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-[10.5px] font-medium transition-colors shrink-0 ${
                            isCopied
                              ? 'border-emerald-500/60 bg-emerald-500/20 text-emerald-300'
                              : 'border-border bg-background/70 hover:bg-muted text-muted-foreground hover:text-foreground'
                          }`}
                          title={`Copy ${field.displayHeading}`}
                        >
                          {isCopied ? <Check size={11} /> : <Copy size={11} />}
                          {isCopied ? 'Copied' : 'Copy'}
                        </button>
                      )}
                    </div>

                    <div className="text-[12.5px] text-foreground leading-relaxed whitespace-pre-wrap break-words select-text">
                      {field.value || <span className="text-muted-foreground italic">—</span>}
                    </div>

                    {field.anomaly && field.anomaly_reason && (
                      <div className="text-[10.5px] text-rose-300/90 border-t border-rose-500/20 pt-1">
                        {field.anomaly_reason}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}

          {/* Collapsible Technical Verification Details (kept tucked away for Store Owners) */}
          <div className="pt-1">
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                setShowAuditDetails((v) => !v);
              }}
              className="inline-flex items-center gap-1 text-[11px] font-medium text-muted-foreground hover:text-foreground transition-colors"
            >
              {showAuditDetails ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
              AI Verification &amp; Audit Details
              {overallConfidence !== undefined && overallConfidence !== '' && (
                <span className="font-mono text-[10.5px] text-foreground/70">
                  ({overallConfidence}%{votes ? ` · ${votes} votes` : ''})
                </span>
              )}
            </button>
            {showAuditDetails && (
              <div className="mt-1.5 rounded-lg border border-border/70 bg-muted/20 px-3 py-2 text-[11px] text-muted-foreground flex flex-wrap gap-x-4 gap-y-1 font-mono">
                {decision && <span>Decision: {decision}</span>}
                {overallConfidence !== undefined && overallConfidence !== '' && (
                  <span>Overall Confidence: {overallConfidence}%</span>
                )}
                {votes && <span>Votes: {votes}</span>}
                {traceId && <span>Trace: {traceId}</span>}
                {lineageHash && <span>Lineage: {String(lineageHash).slice(0, 14)}</span>}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export interface CustomizeColumnsDialogProps {
  open: boolean;
  onClose: () => void;
  headings: string[];
  aliases: HeadingAliasMap;
  onSave: (next: HeadingAliasMap) => void;
}

export function CustomizeColumnsDialog({
  open,
  onClose,
  headings,
  aliases,
  onSave,
}: CustomizeColumnsDialogProps) {
  const [draft, setDraft] = useState<HeadingAliasMap>({});

  useEffect(() => {
    if (!open) return;
    const init: HeadingAliasMap = { ...aliases };
    for (const h of headings) {
      const clean = h.trim();
      if (clean && !init[clean]) {
        const matchKey = Object.keys(aliases).find(
          (k) => normalizeHeadingKey(k) === normalizeHeadingKey(clean)
        );
        if (matchKey && aliases[matchKey]) {
          init[clean] = aliases[matchKey];
        }
      }
    }
    setDraft(init);
  }, [open, headings, aliases]);

  if (!open) return null;

  const uniqueHeadings = Array.from(
    new Set([
      ...headings.map((h) => h.trim()).filter(Boolean),
      ...Object.keys(aliases).filter(Boolean),
    ])
  );

  const handleApplyPresets = () => {
    const next = { ...draft };
    for (const h of uniqueHeadings) {
      const preset = suggestStoreAlias(h);
      if (preset) {
        next[h] = preset;
      }
    }
    setDraft(next);
    toast.success('Applied Shopify / Daraz display heading presets');
  };

  const handleReset = () => {
    setDraft({});
    onSave({});
    toast.success('Reset column headings to defaults');
    onClose();
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    onSave(draft);
    toast.success('Updated column headings for Cards, CSV & PDF exports');
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-xs flex items-center justify-center p-4">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-2xl rounded-xl border border-border bg-card shadow-2xl overflow-hidden flex flex-col max-h-[85vh]"
      >
        <div className="px-5 py-3.5 border-b border-border flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sliders size={16} className="text-primary" />
            <div>
              <h3 className="text-sm font-bold text-foreground">Customize Column Headings</h3>
              <p className="text-[11.5px] text-muted-foreground">
                Rename output headings for Store Cards, Copy All, CSV headers, and Catalog PDF. Original keys stay untouched.
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-muted-foreground hover:text-foreground p-1 rounded"
          >
            <X size={16} />
          </button>
        </div>

        <div className="p-5 overflow-y-auto space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-2 pb-1">
            <span className="text-xs text-muted-foreground">
              {uniqueHeadings.length} detected field{uniqueHeadings.length === 1 ? '' : 's'}
            </span>
            <Button
              type="button"
              size="sm"
              variant="outline"
              className="h-7 text-xs gap-1.5"
              onClick={handleApplyPresets}
            >
              <Sparkles size={12} className="text-emerald-400" />
              Apply Shopify / Daraz Presets
            </Button>
          </div>

          {uniqueHeadings.length === 0 ? (
            <div className="rounded-lg border border-dashed border-border p-4 text-xs text-muted-foreground text-center">
              Run a product photo or batch first to customize its generated headings.
            </div>
          ) : (
            <div className="space-y-2">
              {uniqueHeadings.map((orig) => {
                const placeholder = suggestStoreAlias(orig) || orig;
                return (
                  <div
                    key={orig}
                    className="grid grid-cols-1 sm:grid-cols-12 gap-2 items-center rounded-lg border border-border/70 bg-muted/20 p-2.5"
                  >
                    <div className="sm:col-span-5 min-w-0">
                      <div className="text-[10px] uppercase tracking-wider text-muted-foreground">
                        Original Prompt Key
                      </div>
                      <div className="text-xs font-mono text-foreground truncate" title={orig}>
                        {orig}
                      </div>
                    </div>
                    <div className="sm:col-span-7">
                      <div className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1">
                        Store Display Heading
                      </div>
                      <input
                        type="text"
                        value={draft[orig] ?? ''}
                        onChange={(e) =>
                          setDraft((prev) => ({
                            ...prev,
                            [orig]: e.target.value,
                          }))
                        }
                        placeholder={placeholder}
                        className="w-full h-8 rounded-md border border-border bg-background px-2.5 text-xs text-foreground placeholder:text-muted-foreground/60 focus:outline-none focus:ring-2 focus:ring-primary/40"
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        <div className="px-5 py-3 border-t border-border bg-muted/15 flex items-center justify-between gap-2">
          <Button type="button" size="sm" variant="ghost" className="text-xs gap-1" onClick={handleReset}>
            <RotateCcw size={12} />
            Reset Defaults
          </Button>
          <div className="flex items-center gap-2">
            <Button type="button" size="sm" variant="outline" className="text-xs" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" size="sm" className="text-xs font-semibold">
              Save Headings
            </Button>
          </div>
        </div>
      </form>
    </div>
  );
}
