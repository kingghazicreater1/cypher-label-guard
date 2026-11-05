// Bridges the Clerk session to the app's plain fetch() helpers.
//
// The backend authenticates every request with the Clerk session token (a short-lived
// RS256 JWT). Clerk's getToken() is only available inside React, so <ClerkSessionKeeper />
// registers it here and keeps the token fresh for getAuthHeaders().
//
// The token lives in memory plus sessionStorage (cleared when the tab closes and never shared
// across tabs), not localStorage, which shrinks how long a stolen token stays useful.

const TOKEN_KEY = 'cypher_auth_token';
const PROFILE_KEY = 'cypher_user_profile';

type TokenGetter = () => Promise<string | null>;
type SignOutFn = () => Promise<void>;

let memoryToken: string | null = null;
let inFlight: Promise<string | null> | null = null;
let lastRefreshAt = 0;
const MIN_REFRESH_INTERVAL_MS = 5_000;

export function getStoredToken(): string | null {
  if (typeof window === 'undefined') return null;
  if (memoryToken) return memoryToken;
  try {
    memoryToken = sessionStorage.getItem(TOKEN_KEY);
  } catch {
    /* storage unavailable: memory only */
  }
  return memoryToken;
}

function setStoredToken(token: string | null): void {
  memoryToken = token;
  if (typeof window === 'undefined') return;
  try {
    if (token) sessionStorage.setItem(TOKEN_KEY, token);
    else sessionStorage.removeItem(TOKEN_KEY);
    // Remove any token left behind in localStorage by older versions.
    localStorage.removeItem(TOKEN_KEY);
  } catch {
    /* storage unavailable: memory only */
  }
}

let tokenGetter: TokenGetter | null = null;
let signOutFn: SignOutFn | null = null;
let markReady: () => void = () => {};
const ready = new Promise<void>((resolve) => {
  markReady = resolve;
});

export function registerClerkSession(getter: TokenGetter, signOut: SignOutFn): void {
  tokenGetter = getter;
  signOutFn = signOut;
  markReady();
}

export function unregisterClerkSession(): void {
  tokenGetter = null;
  signOutFn = null;
}

/**
 * Fetches a fresh Clerk session token and stores it. Returns null if signed out.
 * Concurrent callers (interval, focus and visibility events) share one request, and calls made
 * within a few seconds of a successful refresh reuse the current token.
 */
export function refreshAuthToken(waitMs = 3000): Promise<string | null> {
  if (typeof window === 'undefined') return Promise.resolve(null);
  if (inFlight) return inFlight;
  if (memoryToken && Date.now() - lastRefreshAt < MIN_REFRESH_INTERVAL_MS) {
    return Promise.resolve(memoryToken);
  }
  inFlight = (async () => {
    if (!tokenGetter) {
      await Promise.race([ready, new Promise<void>((r) => setTimeout(r, waitMs))]);
    }
    if (!tokenGetter) return getStoredToken();
    try {
      const token = await tokenGetter();
      setStoredToken(token || null);
      if (token) lastRefreshAt = Date.now();
      return token;
    } catch {
      return getStoredToken();
    } finally {
      inFlight = null;
    }
  })();
  return inFlight;
}

export function clearStoredSession(): void {
  if (typeof window === 'undefined') return;
  setStoredToken(null);
  lastRefreshAt = 0;
  localStorage.removeItem(PROFILE_KEY);
}

/** Ends the Clerk session (if any) and wipes locally stored credentials. */
export async function signOutEverywhere(): Promise<void> {
  clearStoredSession();
  if (signOutFn) {
    try {
      await signOutFn();
    } catch {
      /* local state is already cleared */
    }
  }
}

