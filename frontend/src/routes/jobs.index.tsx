import { createFileRoute } from '@tanstack/react-router';
import { JobsScreen } from '@/components/guardian/jobs';
import { pageHead } from '@/components/guardian/data';
export const Route = createFileRoute('/jobs/')({ head: () => pageHead('Jobs', 'Manage private multi-modal labeling jobs and inspect verifiable results.'), component: JobsScreen });