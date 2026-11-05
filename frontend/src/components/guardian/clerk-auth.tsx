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
import { Button } from '@/components/ui/button';
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
    <div className="space-y-3">
      <p className="text-xs text-muted-foreground leading-relaxed">
        Enter your Clerk <strong>Publishable Key</strong> (from <code className="text-primary font-mono text-[11px]">dashboard.clerk.com &rarr; API Keys</code>):
      </p>

      <form onSubmit={handleSavePublishableKey} className="space-y-3">
        <div>
          <input
            type="text"
            value={inputKey}
            onChange={(e) => setInputKey(e.target.value)}
            placeholder="pk_test_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
            className="w-full rounded-md border border-border bg-background px-3 py-2 text-xs font-mono text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none"
          />
        </div>
        <Button
          type="submit"
          className="w-full text-xs font-semibold h-9 gap-1.5"
        >
          <Sparkles className="w-3.5 h-3.5" />
          <span>Connect Clerk Auth</span>
        </Button>
      </form>
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
    <div className="flex flex-col items-center justify-center space-y-3">
      {/* Clerk Mode Toggle */}
      <div className="flex items-center gap-1 rounded-md border border-border bg-secondary/50 p-1 w-full max-w-sm">
        <button
          type="button"
          onClick={() => setAuthMode('signin')}
          className={`flex-1 rounded py-1 text-xs font-medium transition-all text-center ${
            authMode === 'signin'
              ? 'bg-background text-foreground shadow-sm font-semibold'
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          Clerk Sign In
        </button>
        <button
          type="button"
          onClick={() => setAuthMode('signup')}
          className={`flex-1 rounded py-1 text-xs font-medium transition-all text-center ${
            authMode === 'signup'
              ? 'bg-background text-foreground shadow-sm font-semibold'
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          Create Clerk Account
        </button>
      </div>

      {/* Clerk UI Component Container */}
      <div className="clerk-container w-full max-w-md overflow-hidden rounded-lg border border-border bg-card p-2 shadow-sm">
        {authMode === 'signin' ? (
          <SignIn
            routing="hash"
            appearance={{
              baseTheme: dark,
              variables: {
                colorPrimary: 'oklch(0.515 0.222 262)',
                colorBackground: 'transparent',
              },
              elements: {
                card: 'border-0 bg-transparent shadow-none',
              },
            }}
          />
        ) : (
          <SignUp
            routing="hash"
            appearance={{
              baseTheme: dark,
              variables: {
                colorPrimary: 'oklch(0.515 0.222 262)',
                colorBackground: 'transparent',
              },
              elements: {
                card: 'border-0 bg-transparent shadow-none',
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
        }}
      />
    </div>
  );
}
