import React, { useEffect, useState } from 'react';
import { adminService, AILog } from '../../services/adminService';
import { CheckCircle2, XCircle, DollarSign, Zap, Activity } from 'lucide-react';

export const AdminAIUsagePage: React.FC = () => {
  const [logs, setLogs] = useState<AILog[]>([]);
  const [provider, setProvider] = useState<string>('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchUsage = async () => {
      setLoading(true);
      try {
        const data = await adminService.getAIUsage(provider || undefined);
        setLogs(data);
      } catch (err) {
        console.error('Failed to fetch AI usage:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchUsage();
  }, [provider]);

  const totalRequests = logs.length;
  const successful = logs.filter((l) => l.success === true).length;
  const failed = totalRequests - successful;
  const totalTokens = logs.reduce((sum, l) => sum + (l.tokens_used || 0), 0);
  const formattedTokens = totalTokens >= 1_000_000 ? `${(totalTokens / 1_000_000).toFixed(1)}M` : totalTokens >= 1000 ? `${(totalTokens / 1000).toFixed(1)}K` : `${totalTokens}`;
  const totalCost = logs.reduce((sum, l) => sum + (l.estimated_cost_usd || 0), 0).toFixed(2);
  const avgLatency = totalRequests > 0 ? (logs.reduce((sum, l) => sum + (l.latency_ms || 0), 0) / (totalRequests * 1000)).toFixed(1) : '0.0';

  const tutorCount = logs.filter((l) => (l.feature || '').toLowerCase().includes('tutor')).length;
  const quizCount = logs.filter((l) => (l.feature || '').toLowerCase().includes('quiz')).length;
  const assessmentCount = logs.filter((l) => (l.feature || '').toLowerCase().includes('assessment')).length;
  const recCount = logs.filter((l) => (l.feature || '').toLowerCase().includes('recommendation')).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold text-white">AI Usage</h1>
          <p className="text-xs text-slate-400">Track multi-model request latencies, token consumption, costs, and feature breakdown.</p>
        </div>

        <select
          value={provider}
          onChange={(e) => setProvider(e.target.value)}
          className="rounded-lg border border-slate-800 bg-slate-900/60 py-2 px-3 text-xs text-white focus:border-indigo-500 focus:outline-none"
        >
          <option value="">All Providers</option>
          <option value="groq">Groq Cloud (Llama 3.3 70B)</option>
          <option value="gemini">Google Gemini (Flash/Pro)</option>
        </select>
      </div>

      {/* PRD Section 25 Summary Telemetry Metrics */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 backdrop-blur-md">
          <span className="text-[11px] font-semibold text-slate-400">Total Requests</span>
          <p className="mt-1 text-2xl font-bold text-white">{totalRequests}</p>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 backdrop-blur-md">
          <span className="text-[11px] font-semibold text-slate-400">Successful</span>
          <p className="mt-1 text-2xl font-bold text-emerald-400 flex items-center gap-1">
            <CheckCircle2 className="h-4 w-4" /> {successful}
          </p>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 backdrop-blur-md">
          <span className="text-[11px] font-semibold text-slate-400">Failed</span>
          <p className="mt-1 text-2xl font-bold text-rose-400 flex items-center gap-1">
            <XCircle className="h-4 w-4" /> {failed}
          </p>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 backdrop-blur-md">
          <span className="text-[11px] font-semibold text-slate-400">Token Usage</span>
          <p className="mt-1 text-2xl font-bold text-indigo-300">{formattedTokens}</p>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 backdrop-blur-md">
          <span className="text-[11px] font-semibold text-slate-400">Estimated Cost</span>
          <p className="mt-1 text-2xl font-bold text-purple-300 flex items-center gap-0.5">
            <DollarSign className="h-4 w-4 text-purple-400" /> {totalCost}
          </p>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 backdrop-blur-md">
          <span className="text-[11px] font-semibold text-slate-400">Average Latency</span>
          <p className="mt-1 text-2xl font-bold text-amber-300 flex items-center gap-1">
            <Zap className="h-4 w-4 text-amber-400" /> {avgLatency}s
          </p>
        </div>
      </div>

      {/* PRD Section 25 By Feature Breakdown */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur-md space-y-4">
        <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
          <Activity className="h-4 w-4 text-indigo-400" /> By Feature
        </h3>
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <div className="rounded-lg bg-slate-950 p-4 border border-slate-800 flex justify-between items-center">
            <div>
              <span className="text-xs text-slate-400 block font-medium">Tutor</span>
              <span className="text-xl font-bold text-white">{tutorCount}</span>
            </div>
            <div className="h-2 w-12 bg-indigo-500 rounded-full" />
          </div>

          <div className="rounded-lg bg-slate-950 p-4 border border-slate-800 flex justify-between items-center">
            <div>
              <span className="text-xs text-slate-400 block font-medium">Quiz Generation</span>
              <span className="text-xl font-bold text-white">{quizCount}</span>
            </div>
            <div className="h-2 w-12 bg-purple-500 rounded-full" />
          </div>

          <div className="rounded-lg bg-slate-950 p-4 border border-slate-800 flex justify-between items-center">
            <div>
              <span className="text-xs text-slate-400 block font-medium">Assessment</span>
              <span className="text-xl font-bold text-white">{assessmentCount}</span>
            </div>
            <div className="h-2 w-12 bg-blue-500 rounded-full" />
          </div>

          <div className="rounded-lg bg-slate-950 p-4 border border-slate-800 flex justify-between items-center">
            <div>
              <span className="text-xs text-slate-400 block font-medium">Recommendation</span>
              <span className="text-xl font-bold text-white">{recCount}</span>
            </div>
            <div className="h-2 w-12 bg-emerald-500 rounded-full" />
          </div>
        </div>
      </div>

      {/* PRD Section 25 Recent AI Requests Table */}
      <div className="space-y-3">
        <h3 className="text-xs font-bold text-white uppercase tracking-wider">Recent AI Requests</h3>
        {loading ? (
          <div className="flex h-48 items-center justify-center">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-500 border-t-transparent" />
          </div>
        ) : (
          <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900/60 backdrop-blur-md">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="border-b border-slate-800 bg-slate-900/80 uppercase text-slate-400 font-semibold">
                <tr>
                  <th className="px-6 py-3.5">Feature</th>
                  <th className="px-6 py-3.5">Model</th>
                  <th className="px-6 py-3.5">Latency</th>
                  <th className="px-6 py-3.5">Tokens</th>
                  <th className="px-6 py-3.5 text-center">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {logs.map((l) => (
                  <tr key={l.id} className="hover:bg-slate-800/30">
                    <td className="px-6 py-4 font-semibold text-white capitalize">{l.feature}</td>
                    <td className="px-6 py-4 font-mono text-slate-300">{l.model}</td>
                    <td className="px-6 py-4 font-mono text-slate-300">
                      {l.latency_ms >= 1000 ? `${(l.latency_ms / 1000).toFixed(1)}s` : `${l.latency_ms}ms`}
                    </td>
                    <td className="px-6 py-4 font-mono text-slate-300">{l.tokens_used}</td>
                    <td className="px-6 py-4 text-center">
                      {l.success ? (
                        <span className="inline-flex items-center gap-1 font-bold text-emerald-400 text-sm">
                          ✓
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 font-bold text-rose-400 text-sm">
                          ✕
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

