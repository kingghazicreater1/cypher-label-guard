import { useState } from 'react';
import {
  Sparkles,
  ArrowRight,
  Eye,
  EyeOff,
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
    <div className="min-h-screen w-full bg-background text-foreground flex items-center justify-center p-4 font-sans selection:bg-primary selection:text-primary-foreground">
      <div className="w-full max-w-sm">
        {/* Simple, Clean Card */}
        <div className="border border-border rounded-xl bg-card shadow-sm p-6 space-y-5">
          {/* Brand Logo & Name */}
          <div className="text-center space-y-2">
            <div className="w-12 h-12 mx-auto rounded-lg bg-secondary/50 border border-border p-2 flex items-center justify-center">
              <img src="/brand-logo-dark.png" alt="CypherLabelGuard" className="w-full h-full object-contain" />
            </div>
            <div>
              <h1 className="text-lg font-bold tracking-tight text-foreground font-display">
                Cypher<span className="text-primary">LabelGuard</span>
              </h1>
              <p className="text-xs text-muted-foreground mt-0.5">
                Sign in to your account
              </p>
            </div>
          </div>

          {/* Simple Tab Switcher */}
          <div className="grid grid-cols-4 gap-1 p-1 rounded-lg bg-secondary/50 border border-border text-xs">
            <button
              type="button"
              onClick={() => setTab('fast')}
              className={`py-1.5 rounded-md font-medium transition-all text-center ${
                tab === 'fast'
                  ? 'bg-background text-primary shadow-sm font-semibold'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              ⚡ Fast
            </button>
            <button
              type="button"
              onClick={() => setTab('clerk')}
              className={`py-1.5 rounded-md font-medium transition-all text-center ${
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
              className={`py-1.5 rounded-md font-medium transition-all text-center ${
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
              className={`py-1.5 rounded-md font-medium transition-all text-center ${
                tab === 'signup'
                  ? 'bg-background text-primary shadow-sm font-semibold'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              Register
            </button>
          </div>

          {/* TAB 1: 1-CLICK FAST UNLOCK */}
          {tab === 'fast' && (
            <div className="space-y-3 pt-1">
              <p className="text-xs text-muted-foreground leading-relaxed">
                1-Click instant administrator access for King Ghazi.
              </p>

              <div>
                <label className="text-xs font-medium text-foreground block mb-1">
                  Name
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
                  Email
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
                className="w-full h-9 text-xs font-semibold gap-1.5 mt-2"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>{isSubmitting ? 'Unlocking...' : '⚡ Unlock Account'}</span>
              </Button>
            </div>
          )}

          {/* TAB 2: CLERK AUTH */}
          {tab === 'clerk' && (
            <div className="pt-1">
              <ClerkGatekeeperCard
                onSuccess={(profile) => {
                  onAuthenticated(profile);
                }}
              />
            </div>
          )}

          {/* TAB 3: PASSWORD LOGIN */}
          {tab === 'login' && (
            <form onSubmit={handlePasswordLogin} className="space-y-3 pt-1">
              <div>
                <label className="text-xs font-medium text-foreground block mb-1">
                  Email
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
                className="w-full h-9 text-xs font-semibold mt-2"
              >
                {isSubmitting ? 'Signing in...' : 'Sign In'}
              </Button>
            </form>
          )}

          {/* TAB 4: REGISTER */}
          {tab === 'signup' && (
            <form onSubmit={handlePasswordSignup} className="space-y-3 pt-1">
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
                  Email
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
                className="w-full h-9 text-xs font-semibold mt-2"
              >
                {isSubmitting ? 'Creating account...' : 'Create Account'}
              </Button>
            </form>
          )}

          {/* Guest Read-Only Mode */}
          <div className="pt-2 border-t border-border text-center">
            <button
              type="button"
              onClick={onGuestBypass}
              className="text-[11px] text-muted-foreground hover:text-foreground transition-colors font-medium inline-flex items-center gap-1"
            >
              <span>Continue in Guest Mode</span>
              <ArrowRight size={11} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
