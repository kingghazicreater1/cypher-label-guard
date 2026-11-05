import { ArrowRight } from 'lucide-react';
import { ClerkGatekeeperCard } from './clerk-auth';

interface UserProfile {
  name: string;
  email: string;
  phone?: string | undefined;
  authMethod: 'clerk';
  isLoggedIn: boolean;
}

interface AuthGatekeeperProps {
  onAuthenticated: (profile: UserProfile, token?: string) => void;
  onGuestBypass: () => void;
}

// Sign-in is handled exclusively by Clerk. The backend verifies the Clerk session token's
// signature on every request, so there is no local/password/one-click path here.
export function AuthGatekeeper({ onAuthenticated, onGuestBypass }: AuthGatekeeperProps) {
  return (
    <div className="min-h-screen w-full bg-background text-foreground flex items-center justify-center p-4 font-sans selection:bg-primary selection:text-primary-foreground">
      <div className="w-full max-w-md">
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
              <p className="text-xs text-muted-foreground mt-0.5">Sign in to your account</p>
            </div>
          </div>

          <ClerkGatekeeperCard
            onSuccess={(profile) => {
              onAuthenticated(profile);
            }}
          />

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
