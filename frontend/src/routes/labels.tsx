import { createFileRoute } from '@tanstack/react-router';
import { LabelsScreen } from '@/components/guardian/screens';
import { pageHead } from '@/components/guardian/data';
export const Route = createFileRoute('/labels')({ head: () => pageHead('Labels', 'Explore consensus-backed labels, confidence scores, and evidence chains.'), component: LabelsScreen });
