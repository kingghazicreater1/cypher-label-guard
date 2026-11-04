import { createFileRoute } from '@tanstack/react-router';
import { ReviewScreen } from '@/components/guardian/screens';
import { pageHead } from '@/components/guardian/data';
export const Route = createFileRoute('/review')({ head: () => pageHead('Human review', 'Review uncertain labels and resolve disagreements with human judgment.'), component: ReviewScreen });
