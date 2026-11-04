import { createFileRoute } from '@tanstack/react-router';
import { SettingsScreen } from '@/components/guardian/screens';
import { pageHead } from '@/components/guardian/data';
export const Route = createFileRoute('/settings')({ head: () => pageHead('Settings', 'Configure labeling features, providers, thresholds, and workspace preferences.'), component: SettingsScreen });
