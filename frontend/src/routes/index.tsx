import { createFileRoute } from '@tanstack/react-router';
import { DashboardScreen } from '@/components/guardian/dashboard';
import { pageHead } from '@/components/guardian/data';
export const Route = createFileRoute('/')({ head: () => pageHead('Dashboard', 'Privacy-first AI labeling operations, live agent consensus, and verifiable results.'), component: DashboardScreen });
