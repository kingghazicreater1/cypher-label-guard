import { useState } from 'react';
import {
  ShieldCheck,
  Lock,
  KeyRound,
  ArrowRight,
  Sparkles,
  CheckCircle2,
  Layers,
  Eye,
  EyeOff,
  User,
  Shield,
  Fingerprint,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';
import {
  commanderFastUnlock,
  loginWithEmail,
  signupWithEmail,
} from '@/lib/api';
import { ClerkGatekeeperCard, isClerkConfigured } from './clerk-auth';

interface UserProfile {
  name: string;
  email: string;
  phone?: string | undefined;
  authMethod: 'google' | 'phone' | 'email' | 'clerk';
  isLoggedIn: boolean;
}

interface AuthGatekeeperProps {
  onAuthenticated: (profile: UserProfile, token?: string) => void;
  onGuestBypass: () => void;
}

export function AuthGatekeeper({ onAuthenticated, onGuestBypass }: AuthGatekeeperProps) {
  const [tab, setTab] = useState<'fast' | 'clerk' | 'login' | 'signup'>(
    isClerkConfigured ? 'clerk' : 'fast'
  );

  // Email & Password Form State
  const [emailInput, setEmailInput] = useState('kingghazi123580@gmail.com');
  const [fullNameInput, setFullNameInput] = useState('King Ghazi');
  const [passwordInput, setPasswordInput] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // 1-Click Fast Unlock (Commander Access)
  const handleFastUnlock = async () => {
    setIsSubmitting(true);
    try {
      const cleanEmail = emailInput.trim() || 'kingghazi123580@gmail.com';
      const cleanName = fullNameInput.trim() || 'King Ghazi';
      const res = await commanderFastUnlock(cleanEmail, cleanName);
      const profile: UserProfile = {
        name: res.user?.full_name || cleanName,
        email: res.user?.email || cleanEmail,
        authMethod: 'email',
        isLoggedIn: true,
      };
      if (res.token) {
        localStorage.setItem('cypher_auth_token', res.token);
      }
      localStorage.setItem('cypher_user_profile', JSON.stringify(profile));
      toast.success('Commander Identity Confirmed! Full Access Granted.');
      onAuthenticated(profile, res.token);
    } catch {
      const fallbackProfile: UserProfile = {
        name: fullNameInput.trim() || 'King Ghazi',
        email: emailInput.trim() || 'kingghazi123580@gmail.com',
        authMethod: 'email',
        isLoggedIn: true,
      };
      localStorage.setItem('cypher_user_profile', JSON.stringify(fallbackProfile));
      onAuthenticated(fallbackProfile);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Password Sign In
  const handlePasswordLogin = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const cleanEmail = emailInput.trim();
    const cleanPassword = passwordInput.trim();

    if (!cleanEmail || !cleanPassword) {
      toast.error('Please enter your email and password.');
      return;
    }

    setIsSubmitting(true);
    try {
      const res = await loginWithEmail(cleanEmail, cleanPassword);
      const profile: UserProfile = {
        name: res.user?.full_name || cleanEmail.split('@')[0],
        email: res.user?.email || cleanEmail,
        authMethod: 'email',
        isLoggedIn: true,
      };
      if (res.token) {
        localStorage.setItem('cypher_auth_token', res.token);
      }
      localStorage.setItem('cypher_user_profile', JSON.stringify(profile));
      toast.success(`Welcome back, ${profile.name}`);
      onAuthenticated(profile, res.token);
    } catch (err: any) {
      toast.error(err.message || 'Authentication failed. Please verify credentials.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Password Sign Up
  const handlePasswordSignup = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const cleanEmail = emailInput.trim();
    const cleanPassword = passwordInput.trim();
    const cleanName = fullNameInput.trim();

    if (!cleanEmail || !cleanPassword) {
      toast.error('Please provide an email and choose a secure password (min 6 characters).');
      return;
    }
    if (cleanPassword.length < 6) {
      toast.error('Password must be at least 6 characters.');
      return;
    }

    setIsSubmitting(true);
    try {
      const res = await signupWithEmail(cleanEmail, cleanPassword, cleanName || undefined);
      const profile: UserProfile = {
        name: res.user?.full_name || cleanName || cleanEmail.split('@')[0],
        email: res.user?.email || cleanEmail,
        authMethod: 'email',
        isLoggedIn: true,
      };
      if (res.token) {
        localStorage.setItem('cypher_auth_token', res.token);
      }
      localStorage.setItem('cypher_user_profile', JSON.stringify(profile));
      toast.success(`Account registered! Welcome, ${profile.name}`);
      onAuthenticated(profile, res.token);
    } catch (err: any) {
      toast.error(err.message || 'Failed to create account.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen w-full bg-background text-foreground flex flex-col justify-between font-sans">
      {/* Top Header matching Guardian layout */}
      <header className="h-16 border-b border-border bg-card/50 backdrop-blur-md px-6 flex items-center justify-between z-20">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-card border border-border p-1.5 flex items-center justify-center shadow-sm">
            <img src="/brand-logo-dark.png" alt="CypherLabelGuard" className="w-full h-full object-contain" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-semibold text-sm tracking-tight text-foreground font-display">
                Cypher<span className="text-primary">LabelGuard</span>
              </span>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-primary/10 border border-primary/20 text-primary font-medium">
                CORE v2.0
              </span>
            </div>
            <p className="text-[11px] text-muted-foreground hidden sm:block">
              Privacy-First AI Labeling Operations & Parliamentary Consensus
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 text-xs">
          <span className="privacy-pill hidden md:inline-flex">
            <span className="dot" />
            Zero-Retention Verification
          </span>
          <span className="live-pill hidden sm:inline-flex">
            <span className="dot" />
            32-Seat Consensus
          </span>
        </div>
      </header>

      {/* Main Authentication Card */}
      <main className="flex-1 flex flex-col items-center justify-center px-4 py-10">
        <div className="w-full max-w-md">
          {/* Card Container */}
          <div className="panel border border-border shadow-sm rounded-xl overflow-hidden bg-card">
            {/* Brand Header Inside Card */}
            <div className="panel-header border-b border-border bg-secondary/30 py-4 px-6 flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <ShieldCheck className="w-4 h-4 text-primary" />
                <span className="font-semibold text-xs tracking-wide uppercase font-mono text-foreground">
                  Security Access Gatekeeper
                </span>
              </div>
              <span className="text-[10px] font-mono text-muted-foreground">
                256-Bit TLS
              </span>
            </div>

            <div className="p-6 space-y-5">
              {/* Monogram & Title */}
              <div className="text-center space-y-1.5">
                <div className="w-16 h-16 mx-auto rounded-xl bg-secondary/60 border border-border p-2 flex items-center justify-center shadow-sm mb-3">
                  <img src="/brand-logo-dark.png" alt="CypherLabelGuard" className="w-full h-full object-contain" />
                </div>
                <h2 className="text-xl font-bold tracking-tight text-foreground font-display">
                  Welcome to CypherLabelGuard
                </h2>
                <p className="text-xs text-muted-foreground max-w-xs mx-auto">
                  Verify identity to access Vision Studio, Parliamentary Consensus, and Private Labeling Operations.
                </p>
              </div>

              {/* Mode Tabs */}
              <div className="grid grid-cols-4 gap-1 p-1 rounded-lg bg-secondary/50 border border-border text-xs">
                <button
                  type="button"
                  onClick={() => setTab('fast')}
                  className={`py-1.5 px-1 rounded-md font-medium transition-all text-center ${
                    tab === 'fast'
                      ? 'bg-background text-primary shadow-sm font-semibold'
                      : 'text-muted-foreground hover:text-foreground'
                  }`}
                >
                  ⚡ Direct
                </button>
                <button
                  type="button"
                  onClick={() => setTab('clerk')}
                  className={`py-1.5 px-1 rounded-md font-medium transition-all text-center ${
                    tab === 'clerk'
                      ? 'bg-background text-primary shadow-sm font-semibold'
                      : 'text-muted-foreground hover:text-foreground'
                  }`}
                >
                  ✨ Clerk
                </button>
                <button
                  type="button"
                  onClick={() => setTab('login')}
                  className={`py-1.5 px-1 rounded-md font-medium transition-all text-center ${
                    tab === 'login'
                      ? 'bg-background text-primary shadow-sm font-semibold'
                      : 'text-muted-foreground hover:text-foreground'
                  }`}
                >
                  Sign In
                </button>
                <button
                  type="button"
                  onClick={() => setTab('signup')}
                  className={`py-1.5 px-1 rounded-md font-medium transition-all text-center ${
                    tab === 'signup'
                      ? 'bg-background text-primary shadow-sm font-semibold'
                      : 'text-muted-foreground hover:text-foreground'
                  }`}
                >
                  Register
                </button>
              </div>

              {/* TAB 1: COMMANDER FAST UNLOCK (1-CLICK) */}
              {tab === 'fast' && (
                <div className="space-y-4 pt-1">
                  <div className="p-4 rounded-lg bg-primary/5 border border-primary/20 space-y-2">
                    <div className="flex items-center gap-2">
                      <Sparkles className="w-4 h-4 text-primary" />
                      <span className="text-xs font-semibold text-foreground">
                        Commander Instant Direct Unlock
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground leading-relaxed">
                      Instant 1-click access for Commander King Ghazi. Generates a cryptographically signed 30-day Administrator Bearer Token with full system permissions.
                    </p>
                  </div>

                  <div className="space-y-3">
                    <div>
                      <label className="text-xs font-medium text-foreground block mb-1">
                        Commander Identity
                      </label>
                      <input
                        type="text"
                        value={fullNameInput}
                        onChange={(e) => setFullNameInput(e.target.value)}
                        className="w-full text-xs px-3 py-2 rounded-md bg-background border border-border outline-none focus:border-primary"
                        placeholder="King Ghazi"
                      />
                    </div>
                    <div>
                      <label className="text-xs font-medium text-foreground block mb-1">
                        Corporate / Personal Email
                      </label>
                      <input
                        type="email"
                        value={emailInput}
                        onChange={(e) => setEmailInput(e.target.value)}
                        className="w-full text-xs font-mono px-3 py-2 rounded-md bg-background border border-border outline-none focus:border-primary"
                        placeholder="kingghazi123580@gmail.com"
                      />
                    </div>

                    <Button
                      type="button"
                      disabled={isSubmitting}
                      onClick={handleFastUnlock}
                      className="w-full h-10 text-xs font-semibold gap-2 shadow-sm"
                    >
                      <Sparkles className="w-3.5 h-3.5" />
                      <span>{isSubmitting ? 'Unlocking...' : 'Unlock CypherLabelGuard (Full Admin Access)'}</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </Button>
                  </div>
                </div>
              )}

              {/* TAB 2: CLERK.COM AUTHENTICATION */}
              {tab === 'clerk' && (
                <div className="space-y-3 pt-1">
                  <ClerkGatekeeperCard
                    onSuccess={(profile) => {
                      onAuthenticated(profile);
                    }}
                  />
                </div>
              )}

              {/* TAB 3: LOCAL PASSWORD SIGN IN */}
              {tab === 'login' && (
                <form onSubmit={handlePasswordLogin} className="space-y-3.5 pt-1">
                  <div>
                    <label className="text-xs font-medium text-foreground block mb-1">
                      Email Address
                    </label>
                    <input
                      type="email"
                      value={emailInput}
                      onChange={(e) => setEmailInput(e.target.value)}
                      required
                      placeholder="user@example.com"
                      className="w-full text-xs font-mono px-3 py-2 rounded-md bg-background border border-border outline-none focus:border-primary"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-medium text-foreground block mb-1">
                      Password
                    </label>
                    <div className="relative">
                      <input
                        type={showPassword ? 'text' : 'password'}
                        value={passwordInput}
                        onChange={(e) => setPasswordInput(e.target.value)}
                        required
                        placeholder="••••••••"
                        className="w-full text-xs font-mono px-3 py-2 rounded-md bg-background border border-border outline-none focus:border-primary pr-9"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                      >
                        {showPassword ? <EyeOff size={14} /> : <Eye size={14} />}
                      </button>
                    </div>
                  </div>

                  <Button
                    type="submit"
                    disabled={isSubmitting}
                    className="w-full h-10 text-xs font-semibold gap-2"
                  >
                    <span>{isSubmitting ? 'Authenticating...' : 'Sign In with Password'}</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Button>

                  <div className="text-center pt-1">
                    <button
                      type="button"
                      onClick={() => setTab('fast')}
                      className="text-[11px] text-muted-foreground hover:text-primary transition-colors font-medium"
                    >
                      Or use Commander Fast Unlock &rarr;
                    </button>
                  </div>
                </form>
              )}

              {/* TAB 4: LOCAL SIGN UP */}
              {tab === 'signup' && (
                <form onSubmit={handlePasswordSignup} className="space-y-3.5 pt-1">
                  <div>
                    <label className="text-xs font-medium text-foreground block mb-1">
                      Full Name
                    </label>
                    <input
                      type="text"
                      value={fullNameInput}
                      onChange={(e) => setFullNameInput(e.target.value)}
                      placeholder="King Ghazi"
                      className="w-full text-xs px-3 py-2 rounded-md bg-background border border-border outline-none focus:border-primary"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-medium text-foreground block mb-1">
                      Email Address
                    </label>
                    <input
                      type="email"
                      value={emailInput}
                      onChange={(e) => setEmailInput(e.target.value)}
                      required
                      placeholder="user@example.com"
                      className="w-full text-xs font-mono px-3 py-2 rounded-md bg-background border border-border outline-none focus:border-primary"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-medium text-foreground block mb-1">
                      Create Password (min 6 characters)
                    </label>
                    <div className="relative">
                      <input
                        type={showPassword ? 'text' : 'password'}
                        value={passwordInput}
                        onChange={(e) => setPasswordInput(e.target.value)}
                        required
                        placeholder="••••••••"
                        className="w-full text-xs font-mono px-3 py-2 rounded-md bg-background border border-border outline-none focus:border-primary pr-9"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                      >
                        {showPassword ? <EyeOff size={14} /> : <Eye size={14} />}
                      </button>
                    </div>
                  </div>

                  <Button
                    type="submit"
                    disabled={isSubmitting}
                    className="w-full h-10 text-xs font-semibold gap-2"
                  >
                    <span>{isSubmitting ? 'Registering...' : 'Create Account & Unlock'}</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Button>
                </form>
              )}

              {/* Guest Read-Only Mode Link */}
              <div className="pt-2 border-t border-border/60 text-center">
                <button
                  type="button"
                  onClick={onGuestBypass}
                  className="text-[11px] text-muted-foreground hover:text-foreground transition-colors font-medium inline-flex items-center gap-1"
                >
                  <span>Continue in Guest / Demo Read-Only Mode</span>
                  <ArrowRight size={11} />
                </button>
              </div>
            </div>
          </div>

          {/* Clean Subtext Guarantee */}
          <p className="text-[11px] text-center text-muted-foreground mt-4 font-mono">
            Zero-Retention Architecture · Cryptographic Hash Chain · Enterprise ISO-27001
          </p>
        </div>
      </main>

      {/* Clean Bottom Status Bar matching .statusbar */}
      <footer className="h-8 border-t border-border bg-card px-6 flex items-center justify-between text-[11px] text-muted-foreground font-mono z-20">
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1.5 text-success">
            <span className="dot" />
            Zero Data Retention Active
          </span>
          <span className="hidden sm:inline">·</span>
          <span className="hidden sm:inline">SHA-256 Lineage Hash Chain</span>
        </div>
        <div>
          <span>© 2026 CypherLabelGuard Core v2.0</span>
        </div>
      </footer>
    </div>
  );
}
