import React, { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { LoadingState } from "@/components/ui/LoadingState";
import { projectsService, ProjectItem } from "@/services/projectsService";
import {
  masteryService,
  GrowthSummaryItem,
  GrowthSnapshotItem,
  MasteryExplanationItem,
} from "@/services/masteryService";
import {
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  Info,
  X,
  Sparkles,
  ArrowRight,
  BookOpen,
  Bot,
  BrainCircuit,
  History,
  Layers,
} from "lucide-react";

export const GrowthPage: React.FC = () => {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [summary, setSummary] = useState<GrowthSummaryItem | null>(null);
  const [snapshots, setSnapshots] = useState<GrowthSnapshotItem[]>([]);
  const [selectedConceptExplanation, setSelectedConceptExplanation] = useState<MasteryExplanationItem | null>(null);

  const fetchProjects = useCallback(async () => {
    try {
      setProjects((prev) => {
        if (prev.length === 0) setLoading(true);
        return prev;
      });
      const list = await projectsService.listProjects();
      const items = list.items || [];
      setProjects(items);
      if (items.length > 0) {
        setSelectedProjectId((prevId) => prevId || items[0].id);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load projects.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchGrowthData = useCallback(async (projId: string) => {
    if (!projId) return;
    try {
      setSnapshots((prev) => {
        if (prev.length === 0) setLoading(true);
        return prev;
      });
      setError(null);

      const [summaryData, snapshotData] = await Promise.all([
        masteryService.getGrowthSummary(projId).catch(() => null),
        masteryService.getGrowthSnapshots(projId).catch(() => []),
      ]);

      setSummary(summaryData);
      setSnapshots(snapshotData);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to fetch growth data.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  useEffect(() => {
    if (selectedProjectId) {
      fetchGrowthData(selectedProjectId);
    }
  }, [selectedProjectId, fetchGrowthData]);

  const handleOpenExplanation = async (conceptId: string) => {
    if (!selectedProjectId) return;
    try {
      const data = await masteryService.getExplanation(selectedProjectId, conceptId);
      setSelectedConceptExplanation(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load explanation.";
      setError(msg);
    }
  };

  if (loading && projects.length === 0) {
    return <LoadingState message="Loading Growth Analytics & Recommendation Engine..." />;
  }

  const masteriesList = summary
    ? [...summary.improving_concepts, ...summary.stable_concepts, ...summary.weak_concepts]
    : [];

  const improvingList = masteriesList.filter((m) => m.status === "improving");
  const stableList = masteriesList.filter((m) => m.status === "stable");
  const attentionList = masteriesList.filter((m) => m.status === "requiring_attention");

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-700/60 pb-5">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2.5">
            <TrendingUp className="w-7 h-7 text-emerald-400" />
            Growth & Trajectory Hub
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Longitudinal growth tracking, performance snapshots over time, concept trajectories, and AI-driven next actions.
          </p>
        </div>

        {/* Project Selector */}
        {projects.length > 0 && (
          <div className="flex items-center gap-3 bg-slate-900/80 p-2 rounded-xl border border-slate-800">
            <label className="text-xs text-slate-400 font-medium uppercase tracking-wider pl-2">Project:</label>
            <select
              value={selectedProjectId}
              onChange={(e) => setSelectedProjectId(e.target.value)}
              className="bg-slate-800 text-slate-200 border border-slate-700 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 font-medium"
            >
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-300 text-sm flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-rose-400 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {projects.length === 0 ? (
        <div className="p-12 text-center bg-slate-900/60 border border-slate-800 rounded-2xl space-y-3">
          <BrainCircuit className="w-12 h-12 text-slate-600 mx-auto" />
          <h3 className="text-lg font-bold text-slate-200">No Projects Created Yet</h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            Create a project and upload study materials to start tracking concept growth trajectories.
          </p>
          <button
            onClick={() => navigate("/projects")}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold rounded-xl transition"
          >
            Create First Project
          </button>
        </div>
      ) : (
        <>
          {/* KPI Growth Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-slate-900/70 border border-slate-800 p-5 rounded-2xl space-y-2 shadow-lg">
              <div className="flex items-center justify-between text-xs text-slate-400">
                <span className="uppercase tracking-wider font-semibold">Overall Mastery</span>
                <TrendingUp className="w-4 h-4 text-emerald-400" />
              </div>
              <div className="text-3xl font-extrabold text-emerald-400">
                {summary ? `${Math.round(summary.overall_mastery * 100)}%` : "0%"}
              </div>
              <p className="text-[11px] text-slate-400">Project overall learning index</p>
            </div>

            <div className="bg-slate-900/70 border border-slate-800 p-5 rounded-2xl space-y-2 shadow-lg">
              <div className="flex items-center justify-between text-xs text-slate-400">
                <span className="uppercase tracking-wider font-semibold">Improving (&uarr;)</span>
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              </div>
              <div className="text-3xl font-extrabold text-emerald-400">
                {summary ? summary.improving_count : 0}
              </div>
              <p className="text-[11px] text-slate-400">Upward trajectory concepts</p>
            </div>

            <div className="bg-slate-900/70 border border-slate-800 p-5 rounded-2xl space-y-2 shadow-lg">
              <div className="flex items-center justify-between text-xs text-slate-400">
                <span className="uppercase tracking-wider font-semibold">Stable (&rarr;)</span>
                <Info className="w-4 h-4 text-sky-400" />
              </div>
              <div className="text-3xl font-extrabold text-sky-400">
                {summary ? summary.stable_count : 0}
              </div>
              <p className="text-[11px] text-slate-400">Consistent knowledge score</p>
            </div>

            <div className="bg-slate-900/70 border border-slate-800 p-5 rounded-2xl space-y-2 shadow-lg">
              <div className="flex items-center justify-between text-xs text-slate-400">
                <span className="uppercase tracking-wider font-semibold">Attention Needed (&darr;)</span>
                <AlertTriangle className="w-4 h-4 text-rose-400" />
              </div>
              <div className="text-3xl font-extrabold text-rose-400">
                {summary ? summary.requiring_attention_count : 0}
              </div>
              <p className="text-[11px] text-slate-400">Requires targeted review</p>
            </div>
          </div>

          {/* Growth Snapshots Timeline */}
          {snapshots.length > 0 && (
            <div className="bg-slate-800/90 border border-slate-700/80 rounded-2xl p-6 shadow-2xl space-y-4">
              <div className="flex items-center justify-between border-b border-slate-700/60 pb-3">
                <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
                  <History className="w-5 h-5 text-emerald-400" />
                  <span>Growth Snapshot History</span>
                </h2>
                <span className="text-xs text-slate-400 font-mono">{snapshots.length} Snapshots</span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                {snapshots.slice(-6).map((snap, idx) => {
                  const avgPct = Math.round(snap.average_mastery * 100);
                  const dateStr = new Date(snap.snapshot_date).toLocaleDateString(undefined, {
                    month: "short",
                    day: "numeric",
                    hour: "2-digit",
                    minute: "2-digit",
                  });

                  return (
                    <div
                      key={snap.id || idx}
                      className="p-4 bg-slate-900/80 rounded-xl border border-slate-800 space-y-2 hover:border-slate-700 transition"
                    >
                      <div className="flex justify-between items-center text-xs font-mono">
                        <span className="text-slate-400">{dateStr}</span>
                        <span className="text-emerald-400 font-bold text-sm">{avgPct}% Avg</span>
                      </div>

                      <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-emerald-500 rounded-full"
                          style={{ width: `${avgPct}%` }}
                        />
                      </div>

                      <div className="flex items-center gap-2 text-[11px] text-slate-400 font-mono pt-1">
                        <span className="text-emerald-400">↑ {snap.status_counts?.improving || 0}</span>
                        <span className="text-sky-400">→ {snap.status_counts?.stable || 0}</span>
                        <span className="text-rose-400">↓ {snap.status_counts?.requiring_attention || 0}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Growth Trajectory Table */}
          <div className="bg-slate-800/90 border border-slate-700/80 rounded-2xl p-6 shadow-2xl space-y-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-700/60 pb-4">
              <div>
                <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-emerald-400" />
                  <span>Concept Growth Trajectories</span>
                </h2>
                <p className="text-xs text-slate-400 mt-1">
                  Comparative performance and current status across all evaluated concepts.
                </p>
              </div>

              {/* Action Button to Mastery Page */}
              <button
                onClick={() => navigate("/mastery")}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold rounded-xl transition flex items-center gap-2 self-start md:self-auto shadow-md shadow-indigo-600/20"
              >
                <Layers className="w-4 h-4" />
                <span>Go to Mastery Hub</span>
              </button>
            </div>

            {masteriesList.length === 0 ? (
              <div className="p-8 text-center bg-slate-900/40 border border-slate-800 rounded-xl space-y-2">
                <TrendingUp className="w-10 h-10 text-slate-500 mx-auto" />
                <p className="text-sm font-semibold text-slate-300">Not Enough Learning History to Determine a Trend</p>
                <p className="text-xs text-slate-400 max-w-sm mx-auto">
                  Continue learning and take quizzes over time to view concept growth trajectories and performance trends.
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs font-mono">
                  <thead>
                    <tr className="border-b border-slate-700/80 text-slate-400 uppercase tracking-wider text-[11px]">
                      <th className="py-3 px-4">Concept</th>
                      <th className="py-3 px-4">Mastery Score</th>
                      <th className="py-3 px-4">Trajectory Status</th>
                      <th className="py-3 px-4 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/80 text-slate-200">
                    {masteriesList.map((item, idx) => {
                      const scorePct = Math.round((item.mastery_score || 0) * 100);
                      const isImproving = item.status === "improving";
                      const isAttention = item.status === "requiring_attention";
                      return (
                        <tr key={idx} className="hover:bg-slate-900/40 transition">
                          <td className="py-3.5 px-4 font-semibold text-slate-100 font-sans">{item.concept_id}</td>
                          <td className="py-3.5 px-4 font-bold text-indigo-400">{scorePct}%</td>
                          <td
                            className={`py-3.5 px-4 font-bold ${
                              isImproving ? "text-emerald-400" : isAttention ? "text-rose-400" : "text-sky-400"
                            }`}
                          >
                            {isImproving ? "↑ Improving" : isAttention ? "↓ Attention" : "→ Stable"}
                          </td>
                          <td className="py-3.5 px-4 text-right font-sans">
                            <button
                              onClick={() => handleOpenExplanation(item.concept_id)}
                              className="text-indigo-400 hover:underline hover:text-indigo-300 font-semibold"
                            >
                              Why?
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* 3-Column Categorized Status Grid */}
          {masteriesList.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Improving */}
              <div className="bg-slate-800/90 border border-slate-700/80 rounded-2xl p-5 shadow-xl space-y-3">
                <h3 className="text-sm font-bold text-emerald-400 flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Areas Improving ({improvingList.length})</span>
                </h3>
                {improvingList.length === 0 ? (
                  <p className="text-xs text-slate-400 italic">No concepts improving yet.</p>
                ) : (
                  <ul className="space-y-2 text-xs text-slate-200">
                    {improvingList.map((m, idx) => (
                      <li key={idx} className="flex items-center gap-2 bg-slate-900/60 p-2.5 rounded-xl border border-slate-800">
                        <span className="text-emerald-400 font-bold">✓</span>
                        <span>{m.concept_id}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              {/* Stable */}
              <div className="bg-slate-800/90 border border-slate-700/80 rounded-2xl p-5 shadow-xl space-y-3">
                <h3 className="text-sm font-bold text-sky-400 flex items-center gap-2">
                  <Info className="w-4 h-4" />
                  <span>Stable Concepts ({stableList.length})</span>
                </h3>
                {stableList.length === 0 ? (
                  <p className="text-xs text-slate-400 italic">No stable concepts recorded.</p>
                ) : (
                  <ul className="space-y-2 text-xs text-slate-200">
                    {stableList.map((m, idx) => (
                      <li key={idx} className="flex items-center gap-2 bg-slate-900/60 p-2.5 rounded-xl border border-slate-800">
                        <span className="text-sky-400 font-bold">•</span>
                        <span>{m.concept_id}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              {/* Requires Attention */}
              <div className="bg-slate-800/90 border border-slate-700/80 rounded-2xl p-5 shadow-xl space-y-3">
                <h3 className="text-sm font-bold text-rose-400 flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4" />
                  <span>Requires Attention ({attentionList.length})</span>
                </h3>
                {attentionList.length === 0 ? (
                  <p className="text-xs text-slate-400 italic">No critical attention areas.</p>
                ) : (
                  <ul className="space-y-2 text-xs text-slate-200">
                    {attentionList.map((m, idx) => (
                      <li key={idx} className="flex items-center gap-2 bg-slate-900/60 p-2.5 rounded-xl border border-slate-800">
                        <span className="text-rose-400 font-bold">⚠</span>
                        <span>{m.concept_id}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          )}

          {/* Recommendation Engine Next Action Card */}
          <div className="bg-slate-800/90 border border-slate-700/80 rounded-2xl p-6 shadow-2xl space-y-6">
            <div className="border-b border-slate-700/60 pb-4">
              <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-amber-400" />
                <span>Recommended Next Action</span>
              </h2>
              <p className="text-xs text-slate-400 mt-1">
                The AI engine converts learning telemetry into a concrete, prioritized action answering: <em>&ldquo;What should I do next?&rdquo;</em>
              </p>
            </div>

            {attentionList.length === 0 && masteriesList.length === 0 ? (
              <div className="p-8 text-center bg-slate-950/90 border border-slate-800 rounded-2xl space-y-3">
                <Sparkles className="w-10 h-10 text-slate-500 mx-auto" />
                <p className="text-sm font-semibold text-slate-300">No Recommendations Available Yet</p>
                <p className="text-xs text-slate-400 max-w-sm mx-auto">
                  Complete learning activities or adaptive quizzes to generate personalized learning guidance and recommendations.
                </p>
              </div>
            ) : (
              <div className="p-6 bg-slate-950/90 border border-slate-700 rounded-2xl space-y-5 shadow-inner">
                <div className="flex items-center space-x-2 text-amber-400 font-bold text-base">
                  <AlertTriangle className="w-5 h-5" />
                  <span>
                    {attentionList.length > 0
                      ? `⚠ ${attentionList[0].concept_id} needs attention.`
                      : "✓ Solid understanding achieved on current concepts."}
                  </span>
                </div>

                <p className="text-sm text-slate-300 leading-relaxed">
                  {attentionList.length > 0
                    ? `Based on recent assessment signals, ${attentionList[0].concept_id} is identified as an area requiring focus.`
                    : "Continue taking adaptive quizzes to maintain retention and challenge your knowledge."}
                </p>

                <div className="space-y-3 pt-2">
                  <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Recommended Steps:</span>
                  <ol className="space-y-2 text-xs text-slate-200 font-mono">
                    <li className="flex items-center gap-2 bg-slate-900/80 p-3 rounded-xl border border-slate-800">
                      <BookOpen className="w-4 h-4 text-indigo-400" />
                      <span>1. Review project course materials</span>
                    </li>
                    <li className="flex items-center gap-2 bg-slate-900/80 p-3 rounded-xl border border-slate-800">
                      <Bot className="w-4 h-4 text-emerald-400" />
                      <span>2. Ask AI Tutor for an explanation with citations</span>
                    </li>
                    <li className="flex items-center gap-2 bg-slate-900/80 p-3 rounded-xl border border-slate-800">
                      <BrainCircuit className="w-4 h-4 text-amber-400" />
                      <span>3. Complete an adaptive quiz session</span>
                    </li>
                  </ol>
                </div>

                <div className="pt-4 flex justify-end">
                  <button
                    onClick={() => navigate("/assessment")}
                    className="px-6 py-3 bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-sm rounded-xl transition shadow-lg shadow-indigo-600/30 flex items-center space-x-2"
                  >
                    <span>Start Recommended Assessment</span>
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}
          </div>
        </>
      )}

      {/* EXPLAINABILITY DRAWER MODAL ("Why did this change?") */}
      {selectedConceptExplanation && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-xl w-full p-6 shadow-2xl space-y-5 animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between border-b border-slate-700 pb-3">
              <div className="flex items-center gap-2 text-emerald-400 font-bold text-base">
                <Sparkles className="w-5 h-5" /> Evidence Explainability Payload
              </div>
              <button
                onClick={() => setSelectedConceptExplanation(null)}
                className="text-slate-400 hover:text-slate-200"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <h3 className="text-xl font-bold text-slate-100">
                  {selectedConceptExplanation.concept_id}
                </h3>
                <div className="flex items-center gap-3 text-xs text-slate-400 mt-1">
                  <span>
                    Current Mastery:{" "}
                    <strong className="text-slate-200">
                      {(selectedConceptExplanation.current_mastery * 100).toFixed(0)}%
                    </strong>
                  </span>
                  <span>
                    Delta:{" "}
                    <strong
                      className={
                        selectedConceptExplanation.delta >= 0 ? "text-emerald-400" : "text-rose-400"
                      }
                    >
                      {selectedConceptExplanation.delta >= 0 ? "+" : ""}
                      {(selectedConceptExplanation.delta * 100).toFixed(1)}%
                    </strong>
                  </span>
                </div>
              </div>

              <div className="p-4 bg-slate-800/80 rounded-xl border border-slate-700 text-slate-200 text-sm leading-relaxed">
                {selectedConceptExplanation.explanation}
              </div>
            </div>

            <div className="pt-2 flex justify-end">
              <button
                onClick={() => setSelectedConceptExplanation(null)}
                className="bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium px-4 py-2 rounded-lg"
              >
                Close Explanation
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
