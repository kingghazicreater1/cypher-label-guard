import { createFileRoute } from '@tanstack/react-router';
import { ParliamentScreen } from '@/components/guardian/screens';
import { pageHead } from '@/components/guardian/data';
export const Route = createFileRoute('/parliament')({ head: () => pageHead('Parliament', 'Inspect independent AI agent votes, disagreements, and consensus.'), component: ParliamentScreen });
