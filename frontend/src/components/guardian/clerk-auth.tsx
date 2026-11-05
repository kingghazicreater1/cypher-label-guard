import { useState, useEffect } from 'react';
import {
  SignIn,
  SignUp,
  UserButton,
  useUser,
  useAuth,
} from '@clerk/clerk-react';
import { dark } from '@clerk/themes';
import { KeyRound, Sparkles, ArrowRight } from 'lucide-react';
import { toast } from 'sonner';

export function getClerkPublishableKey(): string {
  if (typeof window !== 'undefined') {
    const local = localStorage.getItem('clerk_pub_key');
    if (local && (local.startsWith('pk_test_') || local.startsWith('pk_live_'))) {
      return local;
    }
  }
  if (typeof import.meta !== 'undefined' && import.meta.env) {
    const envKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY;
    if (envKey && (envKey.startsWith('pk_test_') || envKey.startsWith('pk_live_'))) {
      return envKey;
    }
  }
  return '';
}

export const CLERK_PUBLISHABLE_KEY = getClerkPublishableKey();
export const isClerkConfigured = Boolean(CLERK_PUBLISHABLE_KEY);

interface ClerkGatekeeperCardProps {
  onSuccess: (profile: {
    name: string;
    email: string;
    authMethod: 'clerk';
    isLoggedIn: boolean;
  }) => void;
}

// 1. Setup Form when Key has not been configured yet (NO CLERK HOOKS CALLED)
function ClerkKeySetupForm() {
  const [inputKey, setInputKey] = useState('');

  const handleSavePublishableKey = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const clean = inputKey.trim();
    if (!clean.startsWith('pk_test_') && !clean.startsWith('pk_live_')) {
      toast.error('Publishable key must start with pk_test_... or pk_live_...');
      return;
    }
    localStorage.setItem('clerk_pub_key', clean);
    toast.success('Clerk Publishable Key saved! Activating Clerk...');
    window.location.reload();
  };

  return (
    <div className="rounded-2xl border border-emerald-500/30 bg-[#061009] p-6 text-emerald-200 shadow-xl">
      <div className="flex items-center gap-3 mb-3">
        <div className="w-10 h-10 rounded-xl bg-emerald-950/80 border border-emerald-500/50 flex items-center justify-center shrink-0">
          <KeyRound className="h-5 w-5 text-emerald-400" />
        </div>
        <div>
          <h4 className="font-bold text-white text-sm">Clerk.com One-Click Connect</h4>
          <p className="text-[11px] text-emerald-400/70 font-mono">
            Publishable Key (pk_test_...) is public & safe to enter
          </p>
        </div>
      </div>

      <p className="text-xs text-muted-foreground mb-4">
        Apna Clerk <strong>Publishable Key</strong> paste karein (from <code className="text-cyan-300 font-mono">dashboard.clerk.com &rarr; API Keys</code>):
      </p>

      <form onSubmit={handleSavePublishableKey} className="space-y-3">
        <div>
          <input
            type="text"
            value={inputKey}
            onChange={(e) => setInputKey(e.target.value)}
            placeholder="pk_test_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
            className="w-full rounded-xl border border-emerald-500/40 bg-black/60 px-3.5 py-2.5 text-xs font-mono text-emerald-200 placeholder:text-emerald-900 focus:border-emerald-400 focus:outline-none focus:ring-1 focus:ring-emerald-400"
          />
        </div>
        <button
          type="submit"
          className="w-full cursor-pointer rounded-xl bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-400 hover:to-cyan-400 py-2.5 text-xs font-bold text-black shadow-lg shadow-emerald-500/20 flex items-center justify-center gap-2 transition-all"
        >
          <Sparkles className="w-4 h-4 text-black" />
          <span>Connect & Activate Clerk Auth</span>
          <ArrowRight className="w-4 h-4 text-black" />
        </button>
      </form>

      <div className="mt-4 pt-3 border-t border-emerald-900/40 text-[11px] text-muted-foreground flex items-center justify-between">
        <span>Ya direct instant entry ke liye:</span>
        <span className="text-cyan-300 font-semibold cursor-pointer">Commander Direct Access &uarr;</span>
      </div>
    </div>
  );
}

// 2. Active Session Card when ClerkProvider is active (SAFE TO USE CLERK HOOKS)
function ClerkActiveCard({ onSuccess }: ClerkGatekeeperCardProps) {
  const [authMode, setAuthMode] = useState<'signin' | 'signup'>('signin');
  const { isLoaded, isSignedIn, user } = useUser();
  const { getToken } = useAuth();

  // Automatic sync when Clerk user signs in
  useEffect(() => {
    if (isLoaded && isSignedIn && user) {
      const email =
        user.primaryEmailAddress?.emailAddress ||
        user.emailAddresses?.[0]?.emailAddress ||
        '';
      const fullName = user.fullName || user.firstName || email.split('@')[0] || 'Clerk User';

      const syncWithBackend = async () => {
        try {
          const token = await getToken();
          const res = await fetch('/api/v2/auth/clerk-sync', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              ...(token ? { Authorization: `Bearer ${token}` } : {}),
            },
            body: JSON.stringify({
              clerk_id: user.id,
              email: email || `${user.id}@clerk.user`,
              full_name: fullName,
              image_url: user.imageUrl,
            }),
          });
          if (res.ok) {
            const data = await res.json();
            if (data.token) {
              localStorage.setItem('cypher_auth_token', data.token);
            }
          }
        } catch {
          // Fallback gracefully
        }

        const profile = {
          name: fullName,
          email,
          authMethod: 'clerk' as const,
          isLoggedIn: true,
        };
        localStorage.setItem('cypher_user_profile', JSON.stringify(profile));
        toast.success(`Verified via Clerk.com! Welcome, ${fullName}`);
        onSuccess(profile);
      };

      syncWithBackend();
    }
  }, [isLoaded, isSignedIn, user, getToken, onSuccess]);

  return (
    <div className="flex flex-col items-center justify-center">
      {/* Clerk Mode Toggle */}
      <div className="mb-4 flex items-center gap-2 rounded-xl border border-emerald-500/30 bg-black/40 p-1">
        <button
          type="button"
          onClick={() => setAuthMode('signin')}
          className={`rounded-lg px-4 py-1.5 text-xs font-medium transition-all ${
            authMode === 'signin'
              ? 'bg-emerald-500 text-black shadow-md shadow-emerald-500/20 font-semibold'
              : 'text-muted-foreground hover:text-white'
          }`}
        >
          Clerk Sign In
        </button>
        <button
          type="button"
          onClick={() => setAuthMode('signup')}
          className={`rounded-lg px-4 py-1.5 text-xs font-medium transition-all ${
            authMode === 'signup'
              ? 'bg-emerald-500 text-black shadow-md shadow-emerald-500/20 font-semibold'
              : 'text-muted-foreground hover:text-white'
          }`}
        >
          Create Clerk Account
        </button>
      </div>

      {/* Clerk UI Component Container */}
      <div className="clerk-container w-full max-w-md overflow-hidden rounded-2xl border border-emerald-500/30 bg-[#090f0b]/95 p-2 shadow-2xl backdrop-blur-xl">
        {authMode === 'signin' ? (
          <SignIn
            routing="hash"
            appearance={{
              baseTheme: dark,
              variables: {
                colorPrimary: '#10b981',
                colorBackground: '#090f0b',
                colorInputBackground: '#0c1610',
                colorInputText: '#ecfdf5',
                colorText: '#ffffff',
              },
              elements: {
                card: 'border-0 bg-transparent shadow-none',
                footerAction: 'text-emerald-400 hover:text-emerald-300',
                formButtonPrimary:
                  'bg-emerald-500 hover:bg-emerald-400 text-black font-semibold shadow-lg shadow-emerald-500/20',
              },
            }}
          />
        ) : (
          <SignUp
            routing="hash"
            appearance={{
              baseTheme: dark,
              variables: {
                colorPrimary: '#10b981',
                colorBackground: '#090f0b',
                colorInputBackground: '#0c1610',
                colorInputText: '#ecfdf5',
                colorText: '#ffffff',
              },
              elements: {
                card: 'border-0 bg-transparent shadow-none',
                footerAction: 'text-emerald-400 hover:text-emerald-300',
                formButtonPrimary:
                  'bg-emerald-500 hover:bg-emerald-400 text-black font-semibold shadow-lg shadow-emerald-500/20',
              },
            }}
          />
        )}
      </div>
    </div>
  );
}

// 3. Exported Gatekeeper Card that safely handles configured vs unconfigured
export function ClerkGatekeeperCard({ onSuccess }: ClerkGatekeeperCardProps) {
  if (!isClerkConfigured) {
    return <ClerkKeySetupForm />;
  }
  return <ClerkActiveCard onSuccess={onSuccess} />;
}

// 4. Exported Avatar that is safe from hook exceptions when Clerk is unconfigured
export function ClerkUserAvatar() {
  if (!isClerkConfigured) {
    return null;
  }
  return <ClerkUserAvatarInner />;
}

function ClerkUserAvatarInner() {
  const { isLoaded, isSignedIn, user } = useUser();

  if (!isLoaded || !isSignedIn || !user) {
    return null;
  }

  return (
    <div className="flex items-center gap-2">
      <UserButton
        appearance={{
          baseTheme: dark,
          variables: {
            colorPrimary: '#10b981',
            colorBackground: '#0c1610',
          },
        }}
      />
    </div>
  );
}
