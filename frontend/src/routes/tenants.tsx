import { createFileRoute } from '@tanstack/react-router';
import { TenantsScreen } from '@/components/guardian/screens';
import { pageHead } from '@/components/guardian/data';
export const Route = createFileRoute('/tenants')({ head: () => pageHead('Tenants', 'Manage isolated labeling workspaces, quotas, and billing.'), component: TenantsScreen });
