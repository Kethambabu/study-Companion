import React, { useEffect, useState } from 'react';
import { adminService, BackgroundJob } from '../../services/adminService';
import { Briefcase, CheckCircle2, XCircle, Clock, RotateCw } from 'lucide-react';

export const AdminJobsPage: React.FC = () => {
  const [jobs, setJobs] = useState<BackgroundJob[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchJobs = async () => {
      setLoading(true);
      try {
        const data = await adminService.getJobs(statusFilter || undefined);
        setJobs(data);
      } catch (err) {
        console.error('Failed to fetch background jobs:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchJobs();
  }, [statusFilter]);

  const handleRetryJob = (jobId: string) => {
    setJobs((prev) =>
      prev.map((j) =>
        j.id === jobId ? { ...j, status: 'RUNNING', attempts: j.attempts + 1, error_message: null } : j
      )
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Background Jobs</h1>
          <p className="text-xs text-slate-400">Monitor asynchronous PDF processing, quiz evaluation, retries, failure handling, and worker queue states.</p>
        </div>

        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded-lg border border-slate-800 bg-slate-900/60 py-2 px-3 text-xs text-white focus:border-indigo-500 focus:outline-none cursor-pointer"
        >
          <option value="">All Job Statuses</option>
          <option value="READY">READY</option>
          <option value="RUNNING">RUNNING</option>
          <option value="FAILED">FAILED</option>
          <option value="COMPLETE">COMPLETE</option>
        </select>
      </div>

      {loading ? (
        <div className="flex h-48 items-center justify-center">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-500 border-t-transparent" />
        </div>
      ) : jobs.length === 0 ? (
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-12 text-center">
          <Briefcase className="mx-auto h-10 w-10 text-slate-600" />
          <h3 className="mt-3 text-sm font-semibold text-slate-300">No Background Jobs Found</h3>
        </div>
      ) : (
        /* PRD Section 27 Background Jobs Table */
        <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900/60 backdrop-blur-md">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="border-b border-slate-800 bg-slate-900/80 uppercase text-slate-400 font-semibold">
              <tr>
                <th className="px-6 py-3.5">Job</th>
                <th className="px-6 py-3.5">Type</th>
                <th className="px-6 py-3.5">Status</th>
                <th className="px-6 py-3.5">Retries</th>
                <th className="px-6 py-3.5 text-right">Action / Recovery</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {jobs.map((j) => {
                const jobLabel = `#${j.id.slice(0, 8)}`;
                const upperStatus = j.status.toUpperCase();

                return (
                  <tr key={j.id} className="hover:bg-slate-800/30">
                    <td className="px-6 py-4 font-mono font-bold text-white">{jobLabel}</td>
                    <td className="px-6 py-4 font-semibold text-slate-200">{j.job_type}</td>
                    <td className="px-6 py-4">
                      {upperStatus === 'COMPLETE' || upperStatus === 'COMPLETED' ? (
                        <span className="inline-flex items-center gap-1 rounded-md bg-emerald-500/20 px-2.5 py-1 text-[11px] font-bold text-emerald-300 border border-emerald-500/30">
                          <CheckCircle2 className="h-3 w-3" /> COMPLETE
                        </span>
                      ) : upperStatus === 'FAILED' ? (
                        <span className="inline-flex items-center gap-1 rounded-md bg-rose-500/20 px-2.5 py-1 text-[11px] font-bold text-rose-300 border border-rose-500/30">
                          <XCircle className="h-3 w-3" /> FAILED
                        </span>
                      ) : upperStatus === 'RUNNING' ? (
                        <span className="inline-flex items-center gap-1 rounded-md bg-blue-500/20 px-2.5 py-1 text-[11px] font-bold text-blue-300 border border-blue-500/30">
                          <Clock className="h-3 w-3 animate-spin" /> RUNNING
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 rounded-md bg-amber-500/20 px-2.5 py-1 text-[11px] font-bold text-amber-300 border border-amber-500/30">
                          <Clock className="h-3 w-3" /> READY
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 font-mono text-slate-300 font-semibold">{j.attempts}</td>
                    <td className="px-6 py-4 text-right">
                      {upperStatus === 'FAILED' ? (
                        <button
                          onClick={() => handleRetryJob(j.id)}
                          className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/30 border border-indigo-500/40 px-3 py-1.5 text-xs font-semibold text-indigo-300 transition-colors"
                        >
                          <RotateCw className="h-3.5 w-3.5" /> Retry Job
                        </button>
                      ) : (
                        <span className="text-[11px] text-slate-500 font-medium">Automatic</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

