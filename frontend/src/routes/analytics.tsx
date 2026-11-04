import { createFileRoute } from '@tanstack/react-router';
import { AnalyticsScreen } from '@/components/guardian/screens';
import { pageHead } from '@/components/guardian/data';
export const Route = createFileRoute('/analytics')({ head: () => pageHead('Analytics', 'Analyze labeling throughput, accuracy, provider costs, and service performance.'), component: AnalyticsScreen });
