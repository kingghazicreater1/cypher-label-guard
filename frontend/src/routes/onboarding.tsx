import { createFileRoute } from '@tanstack/react-router';
import { OnboardingScreen } from '@/components/guardian/screens';
import { pageHead } from '@/components/guardian/data';
export const Route = createFileRoute('/onboarding')({ head: () => pageHead('Workspace setup', 'Set up providers, privacy preferences, and your first CypherLabelGuard job.'), component: OnboardingScreen });
