import { useState } from 'react';
import {
  ShieldCheck,
  Lock,
  Mail,
  KeyRound,
  ArrowRight,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  Cpu,
  Layers,
  Fingerprint,
  RefreshCw,
  Eye,
  EyeOff,
  User,
  ExternalLink,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';
import {
  sendEmailOtp,
  verifyEmailOtp,
  loginWithEmail,
  signupWithEmail,
} from '@/lib/api';

interface UserProfile {
  name: string;
  email: string;
  phone?: string | undefined;
  authMethod: 'google' | 'phone' | 'email';
  isLoggedIn: boolean;
}

interface AuthGatekeeperProps {
  onAuthenticated: (profile: UserProfile, token?: string) => void;
  onGuestBypass: () => void;
}

export function AuthGatekeeper({ onAuthenticated, onGuestBypass }: AuthGatekeeperProps) {
  const [tab, setTab] = useState<'otp' | 'login' | 'signup'>('otp');

  // Email OTP state
  const [emailInput, setEmailInput] = useState('kingghazi123580@gmail.com');
  const [fullNameInput, setFullNameInput] = useState('King Ghazi');
  const [otpInput, setOtpInput] = useState('');
  const [isSendingOtp, setIsSendingOtp] = useState(false);
  const [isVerifyingOtp, setIsVerifyingOtp] = useState(false);
  const [otpSent, setOtpSent] = useState(false);

  // Password Login & Signup state
  const [passwordInput, setPasswordInput] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmittingPassword, setIsSubmittingPassword] = useState(false);

  // Step 1: Send OTP to email
  const handleSendOtp = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const cleanEmail = emailInput.trim();
    if (!cleanEmail || !cleanEmail.includes('@') || !cleanEmail.includes('.')) {
      toast.error('Please enter a valid corporate or personal email address.');
      return;
    }

    setIsSendingOtp(true);
    try {
      await sendEmailOtp(cleanEmail, fullNameInput.trim() || undefined);
      setOtpSent(true);
      toast.success(`6-digit code dispatched to ${cleanEmail} via Gmail SMTP! Check your inbox.`);
    } catch (err: any) {
      const msg = err.message || '';
      if (msg.includes('535') || msg.includes('Password') || msg.includes('closed') || msg.includes('BadCredentials') || msg.includes('credential')) {
        toast.error('Google SMTP rejected credentials: Google requires a 16-letter App Password (e.g. "abcd efgh ijkl mnop") from myaccount.google.com/apppasswords. Or click Commander Direct Fast Unlock below to enter instantly!');
      } else {
        toast.error(msg || 'Failed to dispatch email verification code');
      }
    } finally {
      setIsSendingOtp(false);
    }
  };

  // Step 2: Verify OTP and unlock
  const handleVerifyOtp = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const cleanEmail = emailInput.trim();
    const cleanCode = otpInput.trim();

    if (!cleanCode || cleanCode.length < 6) {
      toast.error('Please enter the complete 6-digit verification code.');
      return;
    }

    setIsVerifyingOtp(true);
    try {
      const res = await verifyEmailOtp(cleanEmail, cleanCode);
      const profile: UserProfile = {
        name: res.user?.full_name || fullNameInput.trim() || cleanEmail.split('@')[0],
        email: res.user?.email || cleanEmail,
        authMethod: 'email',
        isLoggedIn: true,
      };
      if (res.token) {
        localStorage.setItem('cypher_auth_token', res.token);
      }
      localStorage.setItem('cypher_user_profile', JSON.stringify(profile));
      toast.success(`Access Granted! Welcome to CypherLabelGuard, ${profile.name}`);
      onAuthenticated(profile, res.token);
    } catch (err: any) {
      toast.error(err.message || 'Invalid or expired verification code');
    } finally {
      setIsVerifyingOtp(false);
    }
  };

  // Password Sign In
  const handlePasswordLogin = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const cleanEmail = emailInput.trim();
    const cleanPassword = passwordInput.trim();

    if (!cleanEmail || !cleanPassword) {
      toast.error('Please enter your email and account password.');
      return;
    }

    setIsSubmittingPassword(true);
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
      toast.success(`Authentication verified! Welcome back, ${profile.name}`);
      onAuthenticated(profile, res.token);
    } catch (err: any) {
      toast.error(err.message || 'Authentication failed. Check your password or use Security Code.');
    } finally {
      setIsSubmittingPassword(false);
    }
  };

  // Password Sign Up
  const handlePasswordSignup = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const cleanEmail = emailInput.trim();
    const cleanPassword = passwordInput.trim();
    const cleanName = fullNameInput.trim();

    if (!cleanEmail || !cleanPassword) {
      toast.error('Please provide email and choose a secure password (min 6 chars).');
      return;
    }
    if (cleanPassword.length < 6) {
      toast.error('Password must contain at least 6 characters.');
      return;
    }

    setIsSubmittingPassword(true);
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
      toast.success(`Account provisioned! Welcome, ${profile.name}`);
      onAuthenticated(profile, res.token);
    } catch (err: any) {
      toast.error(err.message || 'Failed to create account');
    } finally {
      setIsSubmittingPassword(false);
    }
  };

  return (
    <div className="min-h-screen w-full bg-[#070b09] text-emerald-100 flex flex-col justify-between relative overflow-hidden font-sans selection:bg-emerald-500 selection:text-black">
      {/* Dynamic Cyber Grid & Radial Glow Background */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(16,185,129,0.15),rgba(255,255,255,0))] pointer-events-none" />
      <div
        className="absolute inset-0 opacity-[0.03] pointer-events-none"
        style={{
          backgroundImage: `linear-gradient(#10b981 1px, transparent 1px), linear-gradient(to right, #10b981 1px, transparent 1px)`,
          backgroundSize: '40px 40px',
        }}
      />
      <div className="absolute top-1/4 -left-32 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 -right-32 w-96 h-96 bg-teal-500/10 rounded-full blur-3xl pointer-events-none" />

      {/* Top Header Banner */}
      <header className="relative z-10 w-full max-w-7xl mx-auto px-6 py-6 flex items-center justify-between border-b border-emerald-900/30">
        <div className="flex items-center gap-3">
          <div className="relative">
            <div className="w-13 h-13 rounded-2xl bg-[#08120c] border border-emerald-400/50 p-1.5 shadow-lg shadow-emerald-500/25 ring-1 ring-cyan-400/30">
              <img src="/brand-logo-dark.png" alt="CypherLabelGuard Logo" className="w-full h-full object-contain" />
            </div>
            <span className="absolute -top-1 -right-1 flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
            </span>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-lg tracking-tight text-white">
                Cypher<span className="text-emerald-400">LabelGuard</span>
              </span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-950/80 border border-emerald-500/30 text-emerald-300 font-mono">
                ENTERPRISE v2.0
              </span>
            </div>
            <p className="text-xs text-emerald-400/70 font-mono">
              Zero-Retention AI Verification · 32-Seat Parliamentary Consensus
            </p>
          </div>
        </div>

        <div className="hidden md:flex items-center gap-3 text-xs font-mono">
          <span className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-950/40 border border-emerald-800/40 text-emerald-300">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            Gmail SMTP: kingghazi123580@gmail.com
          </span>
          <span className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-950/40 border border-emerald-800/40 text-emerald-400">
            <Lock className="w-3.5 h-3.5 text-emerald-400" />
            256-Bit TLS Gatekeeper
          </span>
        </div>
      </header>

      {/* Hero & Center Authentication Gatekeeper Card */}
      <main className="relative z-10 flex-1 flex flex-col items-center justify-center px-4 py-8 max-w-5xl mx-auto w-full">
        {/* Eye-catching Heading */}
        <div className="text-center mb-8 max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-medium mb-4">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Secure Access Gatekeeper · Pehla Page Authentication</span>
          </div>
          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight text-white mb-3 font-display">
            Verify Identity to Unlock <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400">CypherLabelGuard</span>
          </h1>
          <p className="text-sm sm:text-base text-emerald-200/70 max-w-xl mx-auto leading-relaxed">
            Pehle authentication complete karein taakay saari website aur features (Vision Studio, 32-Seat Parliament, Zero-Retention Shield) unlock ho sakein.
          </p>
        </div>

        {/* The Authentication Terminal Card */}
        <div className="w-full max-w-md bg-[#0c1611]/90 backdrop-blur-xl border border-emerald-500/25 rounded-2xl shadow-2xl shadow-emerald-950/60 p-6 sm:p-8 relative">
          <div className="absolute top-0 right-1/4 w-32 h-1 bg-gradient-to-r from-transparent via-emerald-400 to-transparent" />

          {/* Official Monogram Brand Emblem - ENLARGED & HIGH VISIBILITY */}
          <div className="flex flex-col items-center justify-center mb-5">
            <div className="relative group">
              <div className="w-24 h-24 sm:w-28 sm:h-28 rounded-2xl bg-[#060b08] border-2 border-emerald-400/60 p-2.5 flex items-center justify-center shadow-2xl shadow-emerald-950/90 ring-2 ring-cyan-400/40 group-hover:border-emerald-300 group-hover:ring-cyan-300 transition-all duration-300">
                <img src="/brand-logo-dark.png" alt="CypherLabelGuard Emblem" className="w-full h-full object-contain rounded-xl" />
              </div>
              <div className="absolute -inset-2 bg-gradient-to-r from-emerald-500/30 via-cyan-400/25 to-teal-400/30 rounded-3xl blur-xl opacity-60 -z-10 group-hover:opacity-90 transition-all duration-300"></div>
            </div>
            <span className="text-[11px] font-mono text-emerald-300 font-bold tracking-widest mt-2.5 flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
              CYPHER SECURE AI GATEWAY
            </span>
          </div>

          {/* Direct 1-Click Fast Unlock for King Ghazi */}
          <div className="p-3 rounded-xl bg-gradient-to-r from-emerald-950/70 via-[#0a1610] to-teal-950/70 border border-emerald-500/40 mb-5 shadow-md shadow-emerald-950/50">
            <div className="flex items-center justify-between mb-1.5">
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                <span className="text-xs font-bold text-white font-mono">COMMANDER DIRECT ACCESS</span>
              </div>
              <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-900/70 border border-emerald-500/40 text-emerald-300 font-mono font-semibold">
                INSTANT UNLOCK
              </span>
            </div>
            <p className="text-[11px] text-emerald-300/80 mb-2 leading-relaxed">
              Google App Password generate hone tak yahan se 1-click me direct poori website unlock karein:
            </p>
            <Button
              type="button"
              onClick={() => {
                const profile: UserProfile = {
                  name: fullNameInput.trim() || 'King Ghazi',
                  email: emailInput.trim() || 'kingghazi123580@gmail.com',
                  authMethod: 'email',
                  isLoggedIn: true,
                };
                localStorage.setItem('cypher_user_profile', JSON.stringify(profile));
                toast.success(`Commander Identity Confirmed! Welcome, ${profile.name}`);
                onAuthenticated(profile);
              }}
              className="w-full bg-gradient-to-r from-emerald-500 via-teal-400 to-cyan-400 hover:from-emerald-400 hover:to-cyan-300 text-black font-extrabold py-2 text-xs rounded-lg shadow-lg shadow-emerald-500/25 flex items-center justify-center gap-2 cursor-pointer transition-all"
            >
              <Sparkles className="w-4 h-4 text-black" />
              <span>⚡ Commander Fast Unlock (King Ghazi Direct)</span>
              <ArrowRight className="w-4 h-4 text-black" />
            </Button>
          </div>

          {/* Mode Tabs */}
          <div className="grid grid-cols-3 gap-1 bg-[#060b08] p-1 rounded-xl border border-emerald-900/50 mb-6">
            <button
              type="button"
              onClick={() => {
                setTab('otp');
                setOtpSent(false);
              }}
              className={`text-xs py-2 px-2.5 rounded-lg font-medium transition-all flex items-center justify-center gap-1.5 ${
                tab === 'otp'
                  ? 'bg-emerald-600 text-white shadow-md shadow-emerald-700/40'
                  : 'text-emerald-400/70 hover:text-emerald-200'
              }`}
            >
              <Mail className="w-3.5 h-3.5" />
              <span>Email Code</span>
            </button>
            <button
              type="button"
              onClick={() => setTab('login')}
              className={`text-xs py-2 px-2.5 rounded-lg font-medium transition-all flex items-center justify-center gap-1.5 ${
                tab === 'login'
                  ? 'bg-emerald-600 text-white shadow-md shadow-emerald-700/40'
                  : 'text-emerald-400/70 hover:text-emerald-200'
              }`}
            >
              <KeyRound className="w-3.5 h-3.5" />
              <span>Sign In</span>
            </button>
            <button
              type="button"
              onClick={() => setTab('signup')}
              className={`text-xs py-2 px-2.5 rounded-lg font-medium transition-all flex items-center justify-center gap-1.5 ${
                tab === 'signup'
                  ? 'bg-emerald-600 text-white shadow-md shadow-emerald-700/40'
                  : 'text-emerald-400/70 hover:text-emerald-200'
              }`}
            >
              <User className="w-3.5 h-3.5" />
              <span>Register</span>
            </button>
          </div>

          {/* TAB 1: EMAIL OTP (Default & Recommended) */}
          {tab === 'otp' && (
            <div className="space-y-5">
              {/* 3 Step Visual Guidance */}
              <div className="bg-emerald-950/40 border border-emerald-800/30 rounded-xl p-3 text-[11px] font-mono text-emerald-300 flex items-center justify-between">
                <span className={`flex items-center gap-1 ${!otpSent ? 'text-emerald-400 font-bold' : 'text-emerald-400/60'}`}>
                  1. Email
                </span>
                <span className="text-emerald-700">→</span>
                <span className={`flex items-center gap-1 ${otpSent ? 'text-emerald-400 font-bold' : 'text-emerald-400/60'}`}>
                  2. 6-Digit Code
                </span>
                <span className="text-emerald-700">→</span>
                <span className="text-emerald-400/60 flex items-center gap-1">
                  3. Full Access
                </span>
              </div>

              {!otpSent ? (
                /* Step 1: Input email & send OTP */
                <form onSubmit={handleSendOtp} className="space-y-4">
                  <div>
                    <label className="block text-xs font-semibold text-emerald-300 mb-1.5">
                      Your Email Address
                    </label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-emerald-400/60" />
                      <input
                        type="email"
                        value={emailInput}
                        onChange={(e) => setEmailInput(e.target.value)}
                        placeholder="e.g. kingghazi123580@gmail.com"
                        required
                        className="w-full bg-[#060b08] border border-emerald-800/50 rounded-xl pl-9 pr-3 py-2.5 text-sm text-white placeholder-emerald-600/50 focus:outline-none focus:border-emerald-400 focus:ring-1 focus:ring-emerald-400 font-mono transition-all"
                      />
                    </div>
                    <p className="text-[11px] text-emerald-400/60 mt-1 font-mono">
                      Connected to Gmail SMTP · Instant 6-digit delivery
                    </p>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-emerald-300 mb-1.5">
                      Full Name / Officer Alias
                    </label>
                    <div className="relative">
                      <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-emerald-400/60" />
                      <input
                        type="text"
                        value={fullNameInput}
                        onChange={(e) => setFullNameInput(e.target.value)}
                        placeholder="King Ghazi"
                        className="w-full bg-[#060b08] border border-emerald-800/50 rounded-xl pl-9 pr-3 py-2.5 text-sm text-white placeholder-emerald-600/50 focus:outline-none focus:border-emerald-400 focus:ring-1 focus:ring-emerald-400 transition-all"
                      />
                    </div>
                  </div>

                  <Button
                    type="submit"
                    disabled={isSendingOtp}
                    className="w-full bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-black font-bold py-2.5 rounded-xl shadow-lg shadow-emerald-500/20 flex items-center justify-center gap-2 transition-all cursor-pointer"
                  >
                    {isSendingOtp ? (
                      <>
                        <RefreshCw className="w-4 h-4 animate-spin" />
                        <span>Dispatching Email Code...</span>
                      </>
                    ) : (
                      <>
                        <Mail className="w-4 h-4" />
                        <span>Send 6-Digit Verification Code</span>
                        <ArrowRight className="w-4 h-4" />
                      </>
                    )}
                  </Button>
                </form>
              ) : (
                /* Step 2: Enter code & verify */
                <form onSubmit={handleVerifyOtp} className="space-y-4">
                  <div className="bg-emerald-950/60 border border-emerald-700/50 rounded-xl p-3 flex items-center justify-between text-xs">
                    <div>
                      <span className="text-emerald-400/70 block">Code dispatched to:</span>
                      <span className="font-mono font-semibold text-white">{emailInput}</span>
                    </div>
                    <button
                      type="button"
                      onClick={() => setOtpSent(false)}
                      className="text-xs text-emerald-400 hover:text-emerald-300 underline font-mono cursor-pointer"
                    >
                      Change Email
                    </button>
                  </div>

                  <div>
                    <div className="flex items-center justify-between mb-1.5">
                      <label className="text-xs font-semibold text-emerald-300">
                        Enter 6-Digit Code
                      </label>
                      <button
                        type="button"
                        onClick={handleSendOtp}
                        disabled={isSendingOtp}
                        className="text-[11px] text-emerald-400 hover:text-emerald-300 underline flex items-center gap-1 cursor-pointer"
                      >
                        <RefreshCw className={`w-3 h-3 ${isSendingOtp ? 'animate-spin' : ''}`} />
                        Resend Code
                      </button>
                    </div>
                    <input
                      type="text"
                      maxLength={6}
                      value={otpInput}
                      onChange={(e) => setOtpInput(e.target.value.replace(/\D/g, ''))}
                      placeholder="• • • • • •"
                      autoFocus
                      required
                      className="w-full bg-[#060b08] border-2 border-emerald-500/60 rounded-xl px-4 py-3 text-center text-2xl tracking-[0.4em] font-mono text-emerald-300 placeholder-emerald-800/40 focus:outline-none focus:border-emerald-400 focus:ring-2 focus:ring-emerald-400/40 transition-all"
                    />
                  </div>

                  {/* Real Inbox Instruction */}
                  <div className="p-2.5 rounded-lg bg-emerald-950/60 border border-emerald-800/40 text-[11px] text-emerald-300 font-mono flex items-center gap-2">
                    <Mail className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                    <span>Check your Gmail inbox for the 6-digit verification code.</span>
                  </div>

                  <Button
                    type="submit"
                    disabled={isVerifyingOtp || otpInput.trim().length < 6}
                    className="w-full bg-gradient-to-r from-emerald-500 to-teal-400 hover:from-emerald-400 hover:to-teal-300 text-black font-extrabold py-3 rounded-xl shadow-lg shadow-emerald-500/30 flex items-center justify-center gap-2 transition-all cursor-pointer text-sm"
                  >
                    {isVerifyingOtp ? (
                      <>
                        <RefreshCw className="w-4 h-4 animate-spin" />
                        <span>Verifying Security Code...</span>
                      </>
                    ) : (
                      <>
                        <Lock className="w-4 h-4" />
                        <span>Verify & Unlock Full Website</span>
                        <ArrowRight className="w-4 h-4" />
                      </>
                    )}
                  </Button>
                </form>
              )}
            </div>
          )}

          {/* TAB 2: PASSWORD SIGN IN */}
          {tab === 'login' && (
            <form onSubmit={handlePasswordLogin} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-emerald-300 mb-1.5">
                  Email Address
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-emerald-400/60" />
                  <input
                    type="email"
                    value={emailInput}
                    onChange={(e) => setEmailInput(e.target.value)}
                    placeholder="name@domain.com"
                    required
                    className="w-full bg-[#060b08] border border-emerald-800/50 rounded-xl pl-9 pr-3 py-2.5 text-sm text-white placeholder-emerald-600/50 focus:outline-none focus:border-emerald-400 transition-all font-mono"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-emerald-300 mb-1.5">
                  Password
                </label>
                <div className="relative">
                  <KeyRound className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-emerald-400/60" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={passwordInput}
                    onChange={(e) => setPasswordInput(e.target.value)}
                    placeholder="Enter account password"
                    required
                    className="w-full bg-[#060b08] border border-emerald-800/50 rounded-xl pl-9 pr-10 py-2.5 text-sm text-white placeholder-emerald-600/50 focus:outline-none focus:border-emerald-400 transition-all"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-emerald-400/60 hover:text-emerald-300 cursor-pointer"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <Button
                type="submit"
                disabled={isSubmittingPassword}
                className="w-full bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-black font-bold py-2.5 rounded-xl shadow-lg shadow-emerald-500/20 flex items-center justify-center gap-2 transition-all cursor-pointer"
              >
                {isSubmittingPassword ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Signing in...</span>
                  </>
                ) : (
                  <>
                    <Lock className="w-4 h-4" />
                    <span>Sign In & Unlock Platform</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </Button>
            </form>
          )}

          {/* TAB 3: SIGN UP */}
          {tab === 'signup' && (
            <form onSubmit={handlePasswordSignup} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-emerald-300 mb-1.5">
                  Full Name / Officer Alias
                </label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-emerald-400/60" />
                  <input
                    type="text"
                    value={fullNameInput}
                    onChange={(e) => setFullNameInput(e.target.value)}
                    placeholder="e.g. King Ghazi"
                    required
                    className="w-full bg-[#060b08] border border-emerald-800/50 rounded-xl pl-9 pr-3 py-2.5 text-sm text-white placeholder-emerald-600/50 focus:outline-none focus:border-emerald-400 transition-all"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-emerald-300 mb-1.5">
                  Email Address
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-emerald-400/60" />
                  <input
                    type="email"
                    value={emailInput}
                    onChange={(e) => setEmailInput(e.target.value)}
                    placeholder="kingghazi123580@gmail.com"
                    required
                    className="w-full bg-[#060b08] border border-emerald-800/50 rounded-xl pl-9 pr-3 py-2.5 text-sm text-white placeholder-emerald-600/50 focus:outline-none focus:border-emerald-400 transition-all font-mono"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-emerald-300 mb-1.5">
                  Set Password
                </label>
                <div className="relative">
                  <KeyRound className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-emerald-400/60" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={passwordInput}
                    onChange={(e) => setPasswordInput(e.target.value)}
                    placeholder="At least 6 characters"
                    required
                    minLength={6}
                    className="w-full bg-[#060b08] border border-emerald-800/50 rounded-xl pl-9 pr-10 py-2.5 text-sm text-white placeholder-emerald-600/50 focus:outline-none focus:border-emerald-400 transition-all"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-emerald-400/60 hover:text-emerald-300 cursor-pointer"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <Button
                type="submit"
                disabled={isSubmittingPassword}
                className="w-full bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-black font-bold py-2.5 rounded-xl shadow-lg shadow-emerald-500/20 flex items-center justify-center gap-2 transition-all cursor-pointer"
              >
                {isSubmittingPassword ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Registering Account...</span>
                  </>
                ) : (
                  <>
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Create Account & Unlock</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </Button>
            </form>
          )}

          {/* Quick Demo Bypass Option */}
          <div className="mt-6 pt-5 border-t border-emerald-900/40 text-center">
            <button
              type="button"
              onClick={onGuestBypass}
              className="text-xs text-emerald-400/70 hover:text-emerald-300 transition-colors flex items-center justify-center gap-1.5 mx-auto cursor-pointer"
            >
              <span>Evaluating system? Continue as</span>
              <span className="font-semibold text-emerald-400 underline decoration-dotted">
                Demo Guest Observer
              </span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>
        </div>

        {/* 3 High-Value Enterprise Security Pillars */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-10 max-w-4xl w-full">
          <div className="bg-[#0a120e]/80 border border-emerald-900/40 rounded-xl p-4 flex items-start gap-3">
            <div className="w-8 h-8 rounded-lg bg-emerald-950 flex items-center justify-center shrink-0 border border-emerald-800/40 text-emerald-400">
              <Fingerprint className="w-4 h-4" />
            </div>
            <div>
              <h4 className="text-xs font-bold text-white mb-0.5">Zero-Retention Shield</h4>
              <p className="text-[11px] text-emerald-300/70 leading-relaxed">
                RAM-only MMAP inspection buffer. Zero bytes stored to disk. Immediate cryptographic purge.
              </p>
            </div>
          </div>

          <div className="bg-[#0a120e]/80 border border-emerald-900/40 rounded-xl p-4 flex items-start gap-3">
            <div className="w-8 h-8 rounded-lg bg-emerald-950 flex items-center justify-center shrink-0 border border-emerald-800/40 text-emerald-400">
              <Layers className="w-4 h-4" />
            </div>
            <div>
              <h4 className="text-xs font-bold text-white mb-0.5">32-Seat Parliament</h4>
              <p className="text-[11px] text-emerald-300/70 leading-relaxed">
                Adversarial debate with Gated Outlier Protection. 2 models cannot outvote specialized evidence.
              </p>
            </div>
          </div>

          <div className="bg-[#0a120e]/80 border border-emerald-900/40 rounded-xl p-4 flex items-start gap-3">
            <div className="w-8 h-8 rounded-lg bg-emerald-950 flex items-center justify-center shrink-0 border border-emerald-800/40 text-emerald-400">
              <Cpu className="w-4 h-4" />
            </div>
            <div>
              <h4 className="text-xs font-bold text-white mb-0.5">SHA-256 Audit Trail</h4>
              <p className="text-[11px] text-emerald-300/70 leading-relaxed">
                Tamper-proof Merkle lineage hash chains exported with verified forensic timestamping.
              </p>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="relative z-10 w-full max-w-7xl mx-auto px-6 py-4 flex flex-col sm:flex-row items-center justify-between text-[11px] text-emerald-600 border-t border-emerald-900/30 gap-2 font-mono">
        <div>
          <span>© 2026 CypherLabelGuard · AI Autonomous Labeling & Defense</span>
        </div>
        <div className="flex items-center gap-4">
          <span>SMTP Engine: Active</span>
          <span>·</span>
          <span>Security Protocol: TLS 1.3</span>
          <span>·</span>
          <span>Region: Isolated Node</span>
        </div>
      </footer>
    </div>
  );
}
