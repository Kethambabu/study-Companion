import React, { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { LoadingState } from "@/components/ui/LoadingState";
import { projectsService, ProjectItem } from "@/services/projectsService";
import {
  masteryService,
  GrowthSummaryItem,
  MasteryExplanationItem,
} from "@/services/masteryService";
import {
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  Info,
  Layers,
  X,
  Sparkles,
  ArrowRight,
  BookOpen,
  Bot,
  BrainCircuit,
} from "lucide-react";

interface GrowthPageProps {
  initialTab?: "growth" | "mastery" | "recommendations";
}

export const GrowthPage: React.FC<GrowthPageProps> = ({ initialTab = "growth" }) => {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [summary, setSummary] = useState<GrowthSummaryItem | null>(null);
  const [activeTab, setActiveTab] = useState<"growth" | "mastery" | "recommendations">(initialTab);
  const [selectedConceptExplanation, setSelectedConceptExplanation] = useState<MasteryExplanationItem | null>(null);

  const fetchProjects = useCallback(async () => {
    try {
      setLoading(true);
      const list = await projectsService.listProjects();
      const items = list.items || [];
      setProjects(items);
      if (items.length > 0) {
        setSelectedProjectId(items[0].id);
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
      setLoading(true);
      setError(null);
      const data = await masteryService.getGrowthSummary(projId);
      setSummary(data);
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
    return <LoadingState message="Loading Mastery, Growth & Recommendation Engine..." />;
  }

  // Purely dynamic concept list from real backend summary
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
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            <TrendingUp className="w-7 h-7 text-emerald-400" />
            Growth, Mastery & Recommendation Hub
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Dynamic learning evidence engine providing explainable mastery, growth trends, and next actions.
          </p>
        </div>

        {/* Project Selector */}
        {projects.length > 0 && (
          <div className="flex items-center gap-3">
            <label className="text-xs text-slate-400 font-medium uppercase tracking-wider">Project:</label>
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
            Create a project and upload study materials to start tracking concept mastery and growth trajectory.
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
          {/* Main Navigation Tabs */}
          <div className="flex items-center space-x-2 border-b border-slate-700/60 pb-2">
            <button
              onClick={() => setActiveTab("growth")}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center space-x-2 ${
                activeTab === "growth"
                  ? "bg-emerald-600 text-white shadow-lg shadow-emerald-600/30"
                  : "bg-slate-800 text-slate-400 hover:text-slate-200"
              }`}
            >
              <TrendingUp className="w-4 h-4" />
              <span>Section 16: Growth Interface</span>
            </button>

            <button
              onClick={() => setActiveTab("mastery")}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center space-x-2 ${
                activeTab === "mastery"
                  ? "bg-indigo-600 text-white shadow-lg shadow-indigo-600/30"
                  : "bg-slate-800 text-slate-400 hover:text-slate-200"
              }`}
            >
              <Layers className="w-4 h-4" />
              <span>Section 15: Mastery Interface</span>
            </button>

            <button
              onClick={() => setActiveTab("recommendations")}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center space-x-2 ${
                activeTab === "recommendations"
                  ? "bg-amber-600 text-white shadow-lg shadow-amber-600/30"
                  : "bg-slate-800 text-slate-400 hover:text-slate-200"
              }`}
            >
              <Sparkles className="w-4 h-4" />
              <span>Section 17: Recommendation Interface</span>
            </button>
          </div>

          {/* SECTION 15: MASTERY INTERFACE */}
          {activeTab === "mastery" && (
            <div className="bg-slate-800/90 border border-slate-700/80 rounded-2xl p-6 shadow-2xl space-y-6">
              <div className="border-b border-slate-700/60 pb-4">
                <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
                  <Layers className="w-5 h-5 text-indigo-400" />
                  <span>Concept Mastery</span>
                </h2>
                <p className="text-xs text-slate-400 mt-1">
                  Estimated mastery levels derived continuously from student quizzes, assessments, and learning activity.
                </p>
              </div>

              {masteriesList.length === 0 ? (
                <div className="p-8 text-center bg-slate-900/40 border border-slate-800 rounded-xl space-y-3">
                  <Layers className="w-10 h-10 text-slate-500 mx-auto" />
                  <p className="text-sm font-semibold text-slate-300">No Concept Mastery Data Available</p>
                  <p className="text-xs text-slate-400 max-w-sm mx-auto">
                    Complete an adaptive quiz or assessment to start generating dynamic evidence and tracking concept mastery scores.
                  </p>
                  <button
                    onClick={() => navigate("/assessment")}
                    className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold rounded-xl transition"
                  >
                    Start Adaptive Quiz
                  </button>
                </div>
              ) : (
                <>
                  <div className="p-4 bg-indigo-500/10 border border-indigo-500/30 rounded-xl text-xs text-indigo-300 leading-relaxed">
                    💡 <strong>Dynamic Evidence Estimation:</strong> The numbers below represent estimated mastery based on continuous assessment signals. They evolve dynamically as new evidence arrives from your study sessions.
                  </div>

                  <div className="space-y-4 font-mono">
                    {masteriesList.map((item, idx) => {
                      const scorePct = Math.round((item.mastery_score || 0) * 100);
                      const filledBlocks = Math.round((scorePct / 100) * 20);
                      const emptyBlocks = 20 - filledBlocks;
                      const barStr = "█".repeat(filledBlocks) + "░".repeat(emptyBlocks);

                      return (
                        <div key={idx} className="p-4 bg-slate-900/80 rounded-xl border border-slate-800 space-y-2">
                          <div className="flex items-center justify-between text-sm font-sans font-semibold">
                            <span className="text-slate-100">{item.concept_id}</span>
                            <span className="font-mono text-indigo-400 font-bold">{scorePct}%</span>
                          </div>

                          <div className="text-xs text-indigo-400 tracking-widest font-mono flex items-center justify-between">
                            <span className="truncate">{barStr}</span>
                            <span className="text-slate-400 font-sans text-xs ml-4 capitalize">
                              {item.status.replace("_", " ")}
                            </span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </>
              )}
            </div>
          )}

          {/* SECTION 16: GROWTH INTERFACE */}
          {activeTab === "growth" && (
            <div className="space-y-6">
              <div className="bg-slate-800/90 border border-slate-700/80 rounded-2xl p-6 shadow-2xl space-y-6">
                <div className="border-b border-slate-700/60 pb-4">
                  <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
                    <TrendingUp className="w-5 h-5 text-emerald-400" />
                    <span>Growth Analysis</span>
                  </h2>
                  <p className="text-xs text-slate-400 mt-1">
                    Comparative analysis of previous vs. current mastery score trends.
                  </p>
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
                          <th className="py-3 px-4">Mastery</th>
                          <th className="py-3 px-4">Status</th>
                          <th className="py-3 px-4 text-right">Action</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/80 text-slate-200">
                        {masteriesList.map((item, idx) => {
                          const scorePct = Math.round((item.mastery_score || 0) * 100);
                          const isImproving = item.status === "improving";
                          const isAttention = item.status === "requiring_attention";
                          return (
                            <tr key={idx} className="hover:bg-slate-900/40">
                              <td className="py-3.5 px-4 font-semibold text-slate-100 font-sans">{item.concept_id}</td>
                              <td className="py-3.5 px-4 font-bold text-indigo-400">{scorePct}%</td>
                              <td className={`py-3.5 px-4 font-bold ${isImproving ? "text-emerald-400" : isAttention ? "text-rose-400" : "text-sky-400"}`}>
                                {isImproving ? "↑ Improving" : isAttention ? "↓ Attention" : "→ Stable"}
                              </td>
                              <td className="py-3.5 px-4 text-right font-sans">
                                <button
                                  onClick={() => handleOpenExplanation(item.concept_id)}
                                  className="text-indigo-400 hover:underline"
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
                      <span>Stable ({stableList.length})</span>
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
            </div>
          )}

          {/* SECTION 17: RECOMMENDATION INTERFACE */}
          {activeTab === "recommendations" && (
            <div className="bg-slate-800/90 border border-slate-700/80 rounded-2xl p-6 shadow-2xl space-y-6">
              <div className="border-b border-slate-700/60 pb-4">
                <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-amber-400" />
                  <span>Recommended Next Action</span>
                </h2>
                <p className="text-xs text-slate-400 mt-1">
                  The system converts learning data into a concrete, prioritized action answering: <em>&ldquo;What should I do next?&rdquo;</em>
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
          )}
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
