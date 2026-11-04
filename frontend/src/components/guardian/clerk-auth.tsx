import { useState, useEffect } from 'react';
import {
  SignIn,
  SignUp,
  UserButton,
  useUser,
  useAuth,
  useClerk,
} from '@clerk/clerk-react';
import { dark } from '@clerk/themes';
import { ShieldCheck, UserCheck, KeyRound, Sparkles } from 'lucide-react';
import { toast } from 'sonner';

export const CLERK_PUBLISHABLE_KEY =
  (typeof import.meta !== 'undefined' &&
    import.meta.env &&
    import.meta.env.VITE_CLERK_PUBLISHABLE_KEY) ||
  '';

export const isClerkConfigured = Boolean(
  CLERK_PUBLISHABLE_KEY &&
    (CLERK_PUBLISHABLE_KEY.startsWith('pk_test_') ||
      CLERK_PUBLISHABLE_KEY.startsWith('pk_live_'))
);

interface ClerkGatekeeperCardProps {
  onSuccess: (profile: {
    name: string;
    email: string;
    authMethod: 'clerk';
    isLoggedIn: boolean;
  }) => void;
}

export function ClerkGatekeeperCard({ onSuccess }: ClerkGatekeeperCardProps) {
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
          // Call backend clerk-sync endpoint
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

  if (!isClerkConfigured) {
    return (
      <div className="rounded-2xl border border-amber-500/30 bg-amber-950/20 p-6 text-center text-amber-200">
        <KeyRound className="mx-auto mb-3 h-8 w-8 text-amber-400" />
        <h4 className="font-semibold text-white">Clerk Publishable Key Pending</h4>
        <p className="mt-1 text-xs text-amber-200/80">
          Paste your <code className="rounded bg-black/40 px-1 py-0.5 font-mono text-amber-300">VITE_CLERK_PUBLISHABLE_KEY=pk_test_...</code> in your local <code className="rounded bg-black/40 px-1 py-0.5 font-mono text-white">.env</code> file.
        </p>
        <p className="mt-3 text-[11px] text-muted-foreground">
          You can use the Commander Direct Unlock or Email 2FA options below in the meantime.
        </p>
      </div>
    );
  }

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

export function ClerkUserAvatar() {
  const { isLoaded, isSignedIn, user } = useUser();

  if (!isClerkConfigured || !isLoaded || !isSignedIn || !user) {
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
