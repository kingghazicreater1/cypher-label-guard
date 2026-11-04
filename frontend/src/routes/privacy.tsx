import { createFileRoute } from '@tanstack/react-router';
import { PrivacyScreen } from '@/components/guardian/screens';
import { pageHead } from '@/components/guardian/data';
export const Route = createFileRoute('/privacy')({ head: () => pageHead('Privacy Center', 'Inspect privacy safeguards, audit trails, lineage, and reconstruction tests.'), component: PrivacyScreen });
