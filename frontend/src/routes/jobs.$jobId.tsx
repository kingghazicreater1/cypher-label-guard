import { createFileRoute } from '@tanstack/react-router';
import { JobDetailScreen } from '@/components/guardian/jobs';
import { pageHead } from '@/components/guardian/data';
export const Route = createFileRoute('/jobs/$jobId')({ head: () => pageHead('Job details','Inspect labeling progress, consensus, evidence, and exports.'), component: JobPage });
function JobPage() { const { jobId } = Route.useParams(); return <JobDetailScreen jobId={jobId}/>; }
