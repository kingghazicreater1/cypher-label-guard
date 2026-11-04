import { createFileRoute } from '@tanstack/react-router';
import { NewJobScreen } from '@/components/guardian/jobs';
import { pageHead } from '@/components/guardian/data';
export const Route = createFileRoute('/jobs/new')({ head: () => pageHead('New job', 'Create a private multi-modal labeling workflow with configurable voting and privacy.'), component: NewJobScreen });
