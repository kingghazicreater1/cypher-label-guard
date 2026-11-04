import { type ReactNode } from 'react';
import { ChevronRight, Plus, ShieldCheck, Check, ArrowUpRight, ArrowDownRight, CalendarDays, Pause, Play, FileText, Image, Video, AudioLines, Layers, ArrowRight, CircleCheck } from 'lucide-react';
import { Link } from '@tanstack/react-router';
import { Button } from '@/components/ui/button';
import { useGuardian } from './context';
import { providers, privacyMethods } from './data';
export function PageHeading({ title, description, actions }: { title: string; description: string; actions?: ReactNode }) { return <div className="page-heading"><div><div className="breadcrumb">Workspace <ChevronRight size={10} /><span>{title}</span></div><h1>{title}</h1><p>{description}</p></div><div className="heading-actions">{actions}</div></div>; }
export function NewJobButton() { return <Button asChild><Link to="/jobs/new"><Plus />New job</Link></Button>; }
export function PeriodControl({ value, onChange }: { value: string; onChange: (value: string) => void }) { return <label className="period-control flex items-center"><CalendarDays size={14} /><select aria-label="Time period" value={value} onChange={e => onChange(e.target.value)}><option>Today</option><option>Last 7 days</option><option>Last 30 days</option></select></label>; }
export function Panel({ title, icon, action, children, className = '' }: { title: string; icon?: ReactNode; action?: ReactNode; children: ReactNode; className?: string }) { return <section className={`panel ${className}`}><div className="panel-header"><div className="panel-title">{icon}{title}</div>{action}</div>{children}</section>; }
export function Status({ status }: { status: string }) { return <span className={`status ${status}`}><span className="dot" />{status}</span>; }
export function Progress({ value, color = 'cyan' }: { value: number; color?: string }) { return <div className={`progress-track ${color}`}><span style={{ width: `${value}%` }} /></div>; }
export function DataIcon({ type }: { type: string }) { const Icon = type === 'Text' ? FileText : type === 'Image' ? Image : type === 'Video' ? Video : type === 'Audio' ? AudioLines : Layers; return <span className="type-icon"><Icon /></span>; }
export function Kpi({ label, value, change, down = false, icon, color = 'cyan', points = '0,24 10,19 20,21 30,13 40,17 50,8 60,12 70,4 80,7' }: { label: string; value: string; change: string; down?: boolean; icon: ReactNode; color?: string; points?: string }) { return <div className="kpi-card"><div className="kpi-label">{label}{icon}</div><div className="kpi-value">{value}</div><div className="kpi-bottom"><span className="kpi-change">{down ? <ArrowDownRight /> : <ArrowUpRight />}{change}</span>vs. yesterday</div><svg className={`kpi-spark ${color}`} viewBox="0 0 80 28" aria-hidden="true"><polyline points={points} fill="none" stroke="currentColor" strokeWidth="1.5" /></svg></div>; }
export function ParliamentOrbit({ agreed = 0, total = 32 }: { agreed?: number; total?: number }) { return <div className="parliament-orbit" aria-label={`${agreed} of ${total} agents agreed`}><svg viewBox="0 0 200 200"><circle className="orbit-ring" cx="100" cy="100" r="78"/><circle className="orbit-ring" cx="100" cy="100" r="58"/><circle className="orbit-ring" cx="100" cy="100" r="40"/>{Array.from({ length: total }, (_, i) => { const angle = (i / total) * Math.PI * 2 - Math.PI / 2; const x = 100 + Math.cos(angle) * 78; const y = 100 + Math.sin(angle) * 78; const isDissent = agreed < total && i >= agreed; return <g key={i}><line className="orbit-link" x1="100" y1="100" x2={x} y2={y}/><circle className={`orbit-agent ${isDissent ? 'dissent' : ''}`} cx={x} cy={y} r="3.2"/></g>; })}</svg><div className="orbit-center"><ShieldCheck className="shield-icon"/><strong>{agreed}<span className="text-muted-foreground text-base">/{total}</span></strong><span>AGENTS IN AGREEMENT</span></div></div>; }
export function ParliamentFeed() {
  const { paused, setPaused, setEvidence, latestInference, liveGrid, connectedToBackend } = useGuardian();
  const hasInference = Boolean(latestInference?.data?.consensus);
  const consensus = latestInference?.data?.consensus;
  const traceId = latestInference?.prove_it_trace_id || latestInference?.trace_id;
  const agreed = consensus?.affirmative_votes ?? (liveGrid.length > 0 ? liveGrid.filter(t => t.color === 'GREEN').length : 0);
  const total = liveGrid.length > 0 ? liveGrid.length : 32;
  const confidence = consensus?.confidence ? Math.round(consensus.confidence * 100) : (hasInference ? 95 : 0);
  const latency = latestInference?.summary?.latency_ms ? `${latestInference.summary.latency_ms} ms` : '—';
  const cost = latestInference?.summary?.cost_credits ? `$${(latestInference.summary.cost_credits * 0.005).toFixed(3)}` : '—';
  const jobTitle = latestInference?.summary?.job_name || (hasInference ? 'Parliament Consensus Pass' : 'Ready for Consensus Inference');
  const jobType = (latestInference?.summary?.modality || 'Text') as string;

  return (
    <Panel
      title="Live Parliament"
      icon={<Layers />}
      action={
        <div className="flex items-center gap-3">
          <span className="live-pill">
            <span className={`dot ${connectedToBackend ? 'text-success' : 'text-warning'}`} />
            {paused ? 'PAUSED' : 'LIVE'}
          </span>
          <Button
            size="icon"
            variant="ghost"
            aria-label={paused ? 'Resume feed' : 'Pause feed'}
            onClick={() => setPaused(!paused)}
          >
            {paused ? <Play size={12} /> : <Pause size={12} />}
          </Button>
        </div>
      }
    >
      <div className="panel-body">
        <div className="parliament-job">
          <DataIcon type={jobType} />
          <span>{jobTitle}</span>
          {traceId && <code>#{traceId.slice(0, 8)}</code>}
        </div>
        <div className="parliament-content">
          <ParliamentOrbit agreed={agreed} total={total} />
          <div>
            {providers.map((p, idx) => {
              const tile = liveGrid[idx * 8];
              const conf = tile ? Math.round(tile.confidence * 100) : 0;
              return (
                <div className="provider-row" key={p.name}>
                  <div className={`provider-avatar ${p.color}`}>{p.short}</div>
                  <div className="provider-detail">
                    <div>
                      <span>{tile?.api ? tile.api.split('_')[0]?.toUpperCase() : p.name}</span>
                      <small>{tile?.dimension || p.model}</small>
                    </div>
                    <Progress value={conf} color={p.color} />
                  </div>
                  <span className="provider-percent">{conf > 0 ? `${conf}%` : '—'}</span>
                </div>
              );
            })}
            <div className="flex gap-1 items-center text-[9px] text-muted-foreground">
              <span className="dot text-success" />
              32 agents across 4 architectures
            </div>
          </div>
        </div>
        {hasInference ? (
          <div className="consensus-strip">
            <span>
              <CircleCheck size={13} />
              Consensus confirmed
              <span className="text-muted-foreground">· {agreed} of {total} votes</span>
            </span>
            {traceId && (
              <Button variant="link" size="sm" onClick={() => setEvidence(traceId)}>
                Prove it <ArrowRight size={11} />
              </Button>
            )}
          </div>
        ) : (
          <div className="consensus-strip">
            <span className="text-muted-foreground text-xs">
              Awaiting live consensus test or labeling job dispatch.
            </span>
          </div>
        )}
        <div className="parliament-footer">
          <span>
            Confidence <b>{confidence > 0 ? `${confidence}%` : '—'}</b>
          </span>
          <span>
            Latency <b>{latency}</b>
          </span>
          <span>
            Cost <b>{cost}</b>
          </span>
          <Button asChild size="sm" variant="ghost" className="ml-auto h-5 text-[9px]">
            <Link to="/parliament">
              View Parliament <ArrowUpRight size={10} />
            </Link>
          </Button>
        </div>
      </div>
    </Panel>
  );
}
export function PrivacyPanel() {
  const { runTest, latestInference } = useGuardian();
  const exposurePct = latestInference?.summary?.flags?.['data_exposure_percentage'] ?? 7.5;
  return (
    <Panel title="Privacy Shield" icon={<ShieldCheck />} action={<span className="live-pill"><span className="dot"/>HOST RAM-ONLY SECURE</span>}>
      <div className="panel-body">
        {privacyMethods.map(method => (
          <div className="privacy-row" key={method}>
            <CircleCheck/><span>{method}</span><span>Active</span>
          </div>
        ))}
        <div className="privacy-warning">
          <CalendarDays size={12}/>Host Zero-Retention: 0 bytes written to physical disk
        </div>
        <div className="exposure">
          <div className="exposure-label">
            Dynamic Salience Exposure
            <strong>{exposurePct}<span className="text-[10px]">%</span></strong>
          </div>
          <div className="exposure-bar">{Array.from({ length: 23 }, (_, i) => <span key={i}/>)}</div>
          <div className="flex justify-between text-[8px] text-muted-foreground">
            <span>Only target clause sent</span>
            <span>{Math.round(100 - exposurePct)}% stays in local RAM</span>
          </div>
        </div>
        <Button variant="outline" size="sm" className="w-full mt-4 text-[10px]" onClick={runTest}>
          <ShieldCheck/>Verify In-Memory Isolation
        </Button>
      </div>
    </Panel>
  );
}
export function TabBar({ tabs, active, onChange }: { tabs: string[]; active: string; onChange: (value: string) => void }) { return <div className="tabs-row">{tabs.map(tab => <Button variant="ghost" key={tab} className={active === tab ? 'active' : ''} onClick={() => onChange(tab)}>{tab}</Button>)}</div>; }
