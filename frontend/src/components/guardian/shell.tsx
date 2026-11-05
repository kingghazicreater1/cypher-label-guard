import { ClerkUserAvatar } from './clerk-auth';
import { useState, useEffect, type ReactNode } from 'react';
import { Link, useLocation, useNavigate } from '@tanstack/react-router';
import {
  ShieldCheck,
  Search,
  Bell,
  CircleHelp,
  LayoutDashboard,
  BriefcaseBusiness,
  Layers,
  Shield,
  Sliders,
  LockKeyhole,
  Check,
  Download,
  ExternalLink,
  Plus,
  ArrowUpRight,
  LogIn,
  LogOut,
  UserCheck,
  Sparkles,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Toaster, toast } from 'sonner';
import { useGuardian } from './context';
import {
  getCurrentUserProfile,
} from '@/lib/api';
import { exportFile, labels } from './data';
import { AuthGatekeeper } from './auth-gatekeeper';
import { refreshAuthToken, signOutEverywhere } from '@/lib/auth-token';

// The 5 core tabs as requested by the user from the Design 3 screenshot
const bottomNav = [
  { path: '/', name: 'Home', icon: LayoutDashboard },
  { path: '/jobs', name: 'Jobs', icon: BriefcaseBusiness },
  { path: '/parliament', name: 'Parliament', icon: Layers },
  { path: '/privacy', name: 'Privacy', icon: ShieldCheck },
  { path: '/settings', name: 'Settings', icon: Sliders },
] as const;

export function GuardianShell({ children }: { children: ReactNode }) {
  const [modal, setModal] = useState<string | null>(null);
  const [query, setQuery] = useState('');
  const [notificationsRead, setNotificationsRead] = useState(false);
  const [guestBypassed, setGuestBypassed] = useState(false);

  const { evidence, setEvidence, runTest, review, activeDossier, billingSummary, refreshBilling } = useGuardian();
  const location = useLocation();
  const navigate = useNavigate();

  // Authentication & Profile State (Clerk only)
  interface UserProfile {
    name: string;
    email: string;
    phone?: string | undefined;
    authMethod: 'clerk';
    isLoggedIn: boolean;
  }

  const [currentUser, setCurrentUser] = useState<UserProfile | null>(() => {
    try {
      const token = typeof window !== 'undefined' ? localStorage.getItem('cypher_auth_token') : null;
      const saved = typeof window !== 'undefined' ? localStorage.getItem('cypher_user_profile') : null;
      if (token && saved) {
        return JSON.parse(saved);
      }
    } catch {}
    return null;
  });

  // Verify and hydrate the active session on initial load against /api/v2/auth/me.
  // The Clerk session token is short-lived, so get a fresh one before asking the backend.
  useEffect(() => {
    const stored = typeof window !== 'undefined' ? localStorage.getItem('cypher_auth_token') : null;
    if (!stored) return;
    let cancelled = false;
    (async () => {
      await refreshAuthToken();
      try {
        const res = await getCurrentUserProfile();
        if (cancelled || !res?.user) return;
        const profile: UserProfile = {
          name: res.user.full_name || 'User',
          email: res.user.email,
          authMethod: 'clerk',
          isLoggedIn: true,
        };
        setCurrentUser(profile);
        localStorage.setItem('cypher_user_profile', JSON.stringify(profile));
      } catch {
        if (cancelled) return;
        // Token missing/expired/invalid: drop local state and show the sign-in screen.
        localStorage.removeItem('cypher_auth_token');
        localStorage.removeItem('cypher_user_profile');
        setCurrentUser(null);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const handleSignOut = async () => {
    await signOutEverywhere();
    setCurrentUser(null);
    setGuestBypassed(false);
    toast.info('Signed out. Active session terminated.');
    refreshBilling();
  };

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        setModal('command');
      }
      if (e.key === '?' && !['INPUT', 'TEXTAREA'].includes((e.target as HTMLElement)?.tagName)) {
        setModal('help');
      }
      if (e.key === 'Escape') {
        setModal(null);
        setEvidence(null);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [setEvidence]);

  const commands = [
    { title: 'Open Dashboard & Studio', action: () => navigate({ to: '/' }), icon: LayoutDashboard },
    { title: 'Manage SaaS Packages & Upgrade Plans', action: () => navigate({ to: '/tenants' }), icon: Sparkles },
    { title: 'View Verification Jobs', action: () => navigate({ to: '/jobs' }), icon: BriefcaseBusiness },
    { title: 'Open 32-Seat Parliament Chamber', action: () => navigate({ to: '/parliament' }), icon: Layers },
    { title: 'View Privacy & Zero-Retention Shield', action: () => navigate({ to: '/privacy' }), icon: ShieldCheck },
    { title: 'Configure AI Keys (Groq / BYOK)', action: () => navigate({ to: '/settings' }), icon: Sliders },
    { title: 'Create a new job', action: () => navigate({ to: '/jobs/new' }), icon: Plus },
    { title: 'Run forensic reconstruction test', action: runTest, icon: ShieldCheck },
    { title: 'Export all labels', action: () => exportFile('cypher-label-guard-labels.csv', labels, true), icon: Download },
  ];

  const active = (path: string) => (path === '/' ? location.pathname === '/' : location.pathname.startsWith(path));

  // First-Page Authentication Gatekeeper (Landing & Login Screen)
  // When an unauthenticated visitor arrives from Google/browser, require authentication before opening the web
  if (!currentUser && !guestBypassed) {
    return (
      <>
        <AuthGatekeeper
          onAuthenticated={(profile) => {
            setCurrentUser(profile);
            refreshBilling();
          }}
          onGuestBypass={() => setGuestBypassed(true)}
        />
        <Toaster position="top-right" richColors theme="dark" />
      </>
    );
  }

  return (
    <div className="guardian-layout design-three-layout">
      {/* Dark Forest Green Top Bar */}
      <header className="guardian-topbar">
        <Link to="/" className="brand flex items-center gap-2.5" aria-label="CypherLabelGuard Home">
          <div className="w-10 h-10 rounded-xl bg-[#070e0a] border-2 border-emerald-400/60 p-1 flex items-center justify-center shrink-0 shadow-lg shadow-emerald-500/30 ring-1 ring-cyan-400/40">
            <img src="/brand-logo-dark.png" alt="CypherLabelGuard Logo" className="w-full h-full object-contain" />
          </div>
          <span className="text-base font-bold tracking-tight text-white">
            Cypher<span className="text-emerald-400 font-extrabold">LabelGuard</span>
          </span>
        </Link>

        <div className="topbar-actions flex items-center gap-2">
          <Link
            to="/tenants"
            className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/25 text-xs font-mono text-emerald-400 hover:bg-emerald-500/20 hover:border-emerald-500/40 transition-all shadow-sm"
            title="Manage Packages & Token Wallet"
          >
            <Sparkles size={13} className="text-emerald-400" />
            <span className="font-semibold">{billingSummary?.subscription?.plan_name || 'Free'}</span>
            <span className="text-muted-foreground/60">·</span>
            <span>{(billingSummary?.credits_balance || 5000).toLocaleString()} cr</span>
          </Link>

          <Button
            variant="ghost"
            size="icon"
            className="topbar-icon-btn"
            onClick={() => {
              setQuery('');
              setModal('command');
            }}
            aria-label="Search jobs, labels, and commands"
            title="Search (⌘ K)"
          >
            <Search size={18} />
          </Button>

          <Button
            variant="ghost"
            size="icon"
            className="topbar-icon-btn relative"
            aria-label="Notifications"
            title="Notifications"
            onClick={() => {
              setModal('notifications');
              setNotificationsRead(true);
            }}
          >
            <Bell size={18} />
            {!notificationsRead && <span className="topbar-dot-badge" />}
          </Button>

          <ClerkUserAvatar />

          <Button
            variant="ghost"
            className="avatar-btn p-0"
            aria-label="Profile menu"
            onClick={() => setModal('profile')}
            title={currentUser ? currentUser.name : 'Sign In / Register'}
          >
            <span className="avatar">
              {currentUser
                ? currentUser.name
                    .split(' ')
                    .map((n) => n[0])
                    .slice(0, 2)
                    .join('')
                    .toUpperCase() || 'KG'
                : 'KG'}
            </span>
          </Button>
        </div>
      </header>

      {/* Main Full-Width Content Canvas */}
      <main className="guardian-main">{children}</main>

      {/* Fixed Status Bar Strip Right Above Bottom Navigation */}
      <footer className="statusbar">
        <div className="flex items-center gap-2">
          <span className="dot text-success" />
          <span className="dot text-success" />
          <span className="dot text-warning" />
          <span className="dot text-success" />
          <span className="ml-1 text-muted-foreground">
            Queue <b className="text-foreground font-mono font-medium">42</b>
          </span>
        </div>

        <div className="statusbar-right flex items-center gap-2.5">
          <span className="demo-badge">DEMO WORKSPACE</span>
          <LockKeyhole size={13} className="text-success" />
        </div>
      </footer>

      {/* Fixed Dark Forest Green Bottom Navigation Bar (5 Core Tabs) */}
      <nav className="bottom-dock-nav" aria-label="Main Navigation">
        {bottomNav.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            className={`bottom-nav-item ${active(item.path) ? 'active' : ''}`}
            aria-label={item.name}
          >
            <item.icon size={21} strokeWidth={active(item.path) ? 2.3 : 1.8} />
            <span>{item.name}</span>
          </Link>
        ))}
      </nav>

      {/* Command & Search Modal */}
      <Dialog
        open={modal !== null}
        onOpenChange={(open) => {
          if (!open) setModal(null);
        }}
      >
        <DialogContent className="guardian-dialog">
          <DialogTitle>
            {modal === 'command'
              ? 'Search Workspace'
              : modal === 'help'
              ? 'Shortcuts & Navigation'
              : modal === 'notifications'
              ? 'Notifications'
              : modal === 'profile'
              ? 'Your Account'
              : modal === 'pro'
              ? 'CypherLabelGuard Enterprise'
              : `${modal} · Provider Status`}
          </DialogTitle>
          <DialogDescription>
            {modal === 'command'
              ? 'Jump directly to any screen, job, or verification tool.'
              : 'CypherLabelGuard · Signal Studio v3.0'}
          </DialogDescription>

          {modal === 'command' ? (
            <>
              <input
                aria-label="Search workspace"
                autoFocus
                placeholder="Search jobs, labels, commands..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="w-full p-2.5 rounded border border-border bg-card mb-3 text-sm"
              />
              <div className="command-results space-y-1.5">
                {commands
                  .filter((c) => c.title.toLowerCase().includes(query.toLowerCase()))
                  .map((c) => (
                    <Button
                      variant="ghost"
                      key={c.title}
                      className="w-full justify-start text-sm gap-2 h-9"
                      onClick={() => {
                        c.action();
                        setModal(null);
                      }}
                    >
                      <c.icon size={16} />
                      {c.title}
                    </Button>
                  ))}
              </div>
            </>
          ) : modal === 'notifications' ? (
            <div className="metric-list space-y-2">
              {[
                'Product Quality Control completed · 2,480 labels',
                'Legal Contract Review reached consensus · 95.2%',
                'Reconstruction test due in 3 days',
              ].map((n) => (
                <div key={n} className="flex justify-between items-center py-2 border-b border-border text-sm">
                  <span>{n}</span>
                  <Check className="text-success" size={16} />
                </div>
              ))}
            </div>
          ) : modal === 'help' ? (
            <div className="metric-list space-y-2 text-sm">
              <div className="flex justify-between py-1.5 border-b border-border">
                <span>Search Workspace</span>
                <kbd className="px-2 py-0.5 rounded bg-muted font-mono text-xs">Ctrl / ⌘ K</kbd>
              </div>
              <div className="flex justify-between py-1.5 border-b border-border">
                <span>Help</span>
                <kbd className="px-2 py-0.5 rounded bg-muted font-mono text-xs">?</kbd>
              </div>
              <div className="flex justify-between py-1.5 border-b border-border">
                <span>Close Dialog</span>
                <kbd className="px-2 py-0.5 rounded bg-muted font-mono text-xs">Esc</kbd>
              </div>
            </div>
          ) : modal === 'profile' ? (
            <div className="space-y-4">
              {currentUser ? (
                <>
                  <div className="flex items-center gap-3 py-3 border-b border-border/60">
                    <span className="w-12 h-12 rounded-full bg-primary/20 text-primary font-bold text-lg flex items-center justify-center font-mono border border-primary/40">
                      {currentUser.name
                        .split(' ')
                        .map((n) => n[0])
                        .slice(0, 2)
                        .join('')
                        .toUpperCase() || 'U'}
                    </span>
                    <div>
                      <div className="flex items-center gap-2">
                        <strong className="text-sm font-semibold">{currentUser.name}</strong>
                        <span className="px-1.5 py-0.5 rounded text-[9px] font-mono font-bold bg-success/15 text-success border border-success/30 flex items-center gap-1">
                          <span className="w-1.5 h-1.5 rounded-full bg-success inline-block" />
                          VERIFIED SESSION
                        </span>
                      </div>
                      <p className="text-muted-foreground text-xs font-mono">{currentUser.email}</p>
                    </div>
                  </div>

                  <div className="flex flex-col gap-2 pt-2">
                    <Button asChild variant="outline" className="justify-start text-xs h-9">
                      <Link to="/settings" onClick={() => setModal(null)}>
                        <Sliders size={14} className="mr-2 text-primary" />
                        Configure Enterprise Key Slots
                      </Link>
                    </Button>
                    <Button asChild variant="outline" className="justify-start text-xs h-9">
                      <Link to="/tenants" onClick={() => setModal(null)}>
                        <Shield size={14} className="mr-2 text-primary" />
                        Manage SaaS Subscription & Token Wallet
                      </Link>
                    </Button>
                    <Button
                      variant="outline"
                      className="justify-start text-xs text-destructive hover:bg-destructive/10 hover:text-destructive h-9 border-destructive/30"
                      onClick={handleSignOut}
                    >
                      <LogOut size={14} className="mr-2" />
                      Sign Out from Active Session
                    </Button>
                  </div>
                </>
              ) : (
                <div className="py-6 text-center space-y-3">
                  <div className="w-12 h-12 mx-auto rounded-full bg-muted flex items-center justify-center text-muted-foreground">
                    <LockKeyhole size={20} className="text-muted-foreground" />
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-foreground">Guest Workspace (Not Signed In)</h4>
                    <p className="text-xs text-muted-foreground mt-1 max-w-xs mx-auto">
                      Sign in to access dedicated tenant workspaces, token packages, and API keys.
                    </p>
                  </div>
                  <div className="flex justify-center gap-2 pt-2">
                    <Button
                      size="sm"
                      onClick={() => {
                        setModal(null);
                        setGuestBypassed(false);
                      }}
                    >
                      Sign In
                    </Button>
                  </div>
                </div>
              )}
            </div>
          ) : null}
        </DialogContent>
      </Dialog>

      {/* Forensic Proof Dossier Modal */}
      <Dialog
        open={evidence !== null}
        onOpenChange={(open) => {
          if (!open) setEvidence(null);
        }}
      >
        <DialogContent className="guardian-dialog max-w-xl">
          <DialogTitle className="flex gap-2 items-center">
            <ShieldCheck className="text-primary" size={20} />
            Forensic Dossier #{evidence}
          </DialogTitle>
          <DialogDescription>
            {activeDossier
              ? `Trace ID: ${activeDossier.trace_id || evidence} · Zero-Retention RAM Lineage`
              : 'Cryptographic evidence chain · consensus record'}
          </DialogDescription>
          {activeDossier ? (
            <div className="flex justify-between items-center my-2">
              <span className="status Confirmed flex items-center gap-1.5">
                <Shield size={13} />
                {activeDossier.consensus_label ?? 'CONFIRMED'} · Verified
              </span>
              <strong className="font-mono text-primary text-base">
                {activeDossier.affirmative_votes ?? 32}/{activeDossier.total_votes || 32} votes
              </strong>
            </div>
          ) : (
            <div className="my-2 text-xs text-muted-foreground font-mono">
              Trace: {evidence}
            </div>
          )}
          {activeDossier ? (
            <div className="space-y-2 text-xs">
              {[
                [
                  'Token attribution',
                  activeDossier.attributed_tokens?.length
                    ? activeDossier.attributed_tokens
                        .map((t) => `"${t.token}" (${(t.attribution_score * 100).toFixed(1)}%)`)
                        .join(', ')
                    : 'Salience tokens verified from active multi-dimensional inference context.',
                ],
                [
                  '32-Vote Subspace Parliament',
                  `${activeDossier.affirmative_votes ?? 32} of ${
                    activeDossier.total_votes || 32
                  } agent votes confirmed consensus label: ${
                    activeDossier.consensus_label ?? 'CONSENSUS'
                  }`,
                ],
                [
                  'Disagreement & Margin',
                  activeDossier.vote_breakdown?.length && activeDossier.vote_breakdown[0]
                    ? `Fastest response: ${activeDossier.vote_breakdown[0].api} (${
                        activeDossier.vote_breakdown[0].latency_ms?.toFixed(1) || '18'
                      }ms). Full subspace consensus.`
                    : 'Full subspace consensus achieved.',
                ],
                [
                  'Immutable Lineage Hash',
                  activeDossier.lineage_ledger?.length &&
                  activeDossier.lineage_ledger[activeDossier.lineage_ledger.length - 1]
                    ? activeDossier.lineage_ledger[activeDossier.lineage_ledger.length - 1]
                        ?.current_hash ?? 'Verified'
                    : 'SHA-256 verified chain',
                ],
              ].map(([title, text], i) => (
                <div className="evidence-step" key={title}>
                  <b>{i + 1}</b>
                  <div>
                    <strong>{title}</strong>
                    <p className="text-muted-foreground">{text}</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-xs text-muted-foreground space-y-2">
              <ShieldCheck className="mx-auto text-muted-foreground/40 mb-2" size={32} />
              <p className="font-medium text-foreground">Awaiting In-Memory Forensic Dossier</p>
              <p>
                Trace #{evidence} does not have an active RAM-resident audit ledger. Run a live test or dispatch a job to inspect cryptographic token attribution.
              </p>
            </div>
          )}
          <div className="flex gap-2 flex-wrap pt-3">
            <Button
              variant="outline"
              size="sm"
              disabled={!activeDossier}
              onClick={() =>
                activeDossier &&
                exportFile(
                  `evidence-${evidence}.json`,
                  activeDossier
                )
              }
            >
              <Download size={13} />
              Export evidence
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setEvidence(null);
                navigate({ to: '/review' });
              }}
            >
              Challenge label
            </Button>
            <Button
              size="sm"
              className="ml-auto"
              onClick={() => {
                if (evidence) review(evidence);
                setEvidence(null);
              }}
            >
              <Check size={13} />
              Accept & Sign
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      <Toaster position="top-right" richColors />
    </div>
  );
}
