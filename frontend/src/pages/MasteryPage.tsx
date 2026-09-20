import React, { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { LoadingState } from "@/components/ui/LoadingState";
import { projectsService, ProjectItem } from "@/services/projectsService";
import {
  masteryService,
  ConceptMasteryItem,
  GrowthSummaryItem,
  MasteryExplanationItem,
} from "@/services/masteryService";
import {
  Layers,
  AlertTriangle,
  CheckCircle2,
  BrainCircuit,
  X,
  Sparkles,
  ArrowRight,
  Search,
  Filter,
  BarChart3,
  HelpCircle,
  TrendingUp,
} from "lucide-react";

export const MasteryPage: React.FC = () => {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [summary, setSummary] = useState<GrowthSummaryItem | null>(null);
  const [masteriesList, setMasteriesList] = useState<ConceptMasteryItem[]>([]);
  const [filterCategory, setFilterCategory] = useState<"all" | "mastered" | "developing" | "attention">("all");
  const [searchQuery, setSearchQuery] = useState<string>("");
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

  const fetchMasteryData = useCallback(async (projId: string) => {
    if (!projId) return;
    try {
      setMasteriesList((prev) => {
        if (prev.length === 0) setLoading(true);
        return prev;
      });
      setError(null);

      const [summaryRes, rawMasteries] = await Promise.all([
        masteryService.getGrowthSummary(projId).catch(() => null),
        masteryService.listMasteries(projId).catch(() => []),
      ]);

      setSummary(summaryRes);

      if (rawMasteries && rawMasteries.length > 0) {
        setMasteriesList(rawMasteries);
      } else if (summaryRes) {
        setMasteriesList([
          ...summaryRes.improving_concepts,
          ...summaryRes.stable_concepts,
          ...summaryRes.weak_concepts,
        ]);
      } else {
        setMasteriesList([]);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to fetch concept mastery data.";
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
      fetchMasteryData(selectedProjectId);
    }
  }, [selectedProjectId, fetchMasteryData]);

  const handleOpenExplanation = async (conceptId: string) => {
    if (!selectedProjectId) return;
    try {
      const data = await masteryService.getExplanation(selectedProjectId, conceptId);
      setSelectedConceptExplanation(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load explanation payload.";
      setError(msg);
    }
  };

  if (loading && projects.length === 0) {
    return <LoadingState message="Loading Concept Mastery Hub..." />;
  }

  // Calculate statistics
  const totalConcepts = masteriesList.length;
  const masteredCount = masteriesList.filter((m) => m.mastery_score >= 0.75).length;
  const developingCount = masteriesList.filter((m) => m.mastery_score >= 0.5 && m.mastery_score < 0.75).length;
  const attentionCount = masteriesList.filter((m) => m.mastery_score < 0.5 || m.status === "requiring_attention").length;

  const filteredMasteries = masteriesList.filter((item) => {
    const matchesSearch = item.concept_id.toLowerCase().includes(searchQuery.toLowerCase());
    if (!matchesSearch) return false;

    if (filterCategory === "mastered") return item.mastery_score >= 0.75;
    if (filterCategory === "developing") return item.mastery_score >= 0.5 && item.mastery_score < 0.75;
    if (filterCategory === "attention") return item.mastery_score < 0.5 || item.status === "requiring_attention";
    return true;
  });

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-700/60 pb-5">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2.5">
            <Layers className="w-7 h-7 text-indigo-400" />
            Concept Mastery Hub
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Real-time estimation of student concept mastery derived continuously from quiz responses and study signals.
          </p>
        </div>

        {/* Project Selector */}
        {projects.length > 0 && (
          <div className="flex items-center gap-3 bg-slate-900/80 p-2 rounded-xl border border-slate-800">
            <label className="text-xs text-slate-400 font-medium uppercase tracking-wider pl-2">Project:</label>
            <select
              value={selectedProjectId}
              onChange={(e) => setSelectedProjectId(e.target.value)}
              className="bg-slate-800 text-slate-200 border border-slate-700 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 font-medium"
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
          <h3 className="text-lg font-bold text-slate-200">No Projects Found</h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            Create a project and start solving quizzes to track your concept mastery scores.
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
          {/* KPI Summary Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-slate-900/70 border border-slate-800 p-5 rounded-2xl space-y-2 shadow-lg">
              <div className="flex items-center justify-between text-xs text-slate-400">
                <span className="uppercase tracking-wider font-semibold">Overall Mastery</span>
                <BarChart3 className="w-4 h-4 text-indigo-400" />
              </div>
              <div className="text-3xl font-extrabold text-indigo-400">
                {summary ? `${Math.round(summary.overall_mastery * 100)}%` : totalConcepts > 0 ? `${Math.round((masteredCount / totalConcepts) * 100)}%` : "0%"}
              </div>
              <p className="text-[11px] text-slate-400">Continuous Bayesian estimation</p>
            </div>

            <div className="bg-slate-900/70 border border-slate-800 p-5 rounded-2xl space-y-2 shadow-lg">
              <div className="flex items-center justify-between text-xs text-slate-400">
                <span className="uppercase tracking-wider font-semibold">Mastered (&ge; 75%)</span>
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              </div>
              <div className="text-3xl font-extrabold text-emerald-400">{masteredCount}</div>
              <p className="text-[11px] text-slate-400">Concepts with high retention</p>
            </div>

            <div className="bg-slate-900/70 border border-slate-800 p-5 rounded-2xl space-y-2 shadow-lg">
              <div className="flex items-center justify-between text-xs text-slate-400">
                <span className="uppercase tracking-wider font-semibold">Developing (50-74%)</span>
                <TrendingUp className="w-4 h-4 text-sky-400" />
              </div>
              <div className="text-3xl font-extrabold text-sky-400">{developingCount}</div>
              <p className="text-[11px] text-slate-400">Steady progress tracked</p>
            </div>

            <div className="bg-slate-900/70 border border-slate-800 p-5 rounded-2xl space-y-2 shadow-lg">
              <div className="flex items-center justify-between text-xs text-slate-400">
                <span className="uppercase tracking-wider font-semibold">Needs Focus (&lt; 50%)</span>
                <AlertTriangle className="w-4 h-4 text-rose-400" />
              </div>
              <div className="text-3xl font-extrabold text-rose-400">{attentionCount}</div>
              <p className="text-[11px] text-slate-400">Requires targeted practice</p>
            </div>
          </div>

          {/* Main Mastery Card */}
          <div className="bg-slate-800/90 border border-slate-700/80 rounded-2xl p-6 shadow-2xl space-y-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-700/60 pb-4">
              <div>
                <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
                  <Layers className="w-5 h-5 text-indigo-400" />
                  <span>Concept Scores &amp; Evidence</span>
                </h2>
                <p className="text-xs text-slate-400 mt-1">
                  Individual concept proficiency and explainable mastery signals.
                </p>
              </div>

              {/* Action Button to Growth page */}
              <button
                onClick={() => navigate("/growth")}
                className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 text-xs font-semibold rounded-xl transition flex items-center gap-2 self-start md:self-auto"
              >
                <span>View Growth Trajectories</span>
                <ArrowRight className="w-4 h-4 text-emerald-400" />
              </button>
            </div>

            {/* Filter and Search Bar */}
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
              {/* Search */}
              <div className="relative w-full sm:w-64">
                <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                <input
                  type="text"
                  placeholder="Search concept..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl pl-9 pr-3 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              {/* Filters */}
              <div className="flex items-center gap-1.5 overflow-x-auto w-full sm:w-auto pb-1 sm:pb-0">
                <Filter className="w-3.5 h-3.5 text-slate-400 mr-1 hidden sm:inline" />
                {[
                  { id: "all", label: `All (${totalConcepts})` },
                  { id: "mastered", label: `Mastered (${masteredCount})` },
                  { id: "developing", label: `Developing (${developingCount})` },
                  { id: "attention", label: `Needs Focus (${attentionCount})` },
                ].map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setFilterCategory(tab.id as typeof filterCategory)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                      filterCategory === tab.id
                        ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30 font-bold"
                        : "bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800"
                    }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Content List */}
            {filteredMasteries.length === 0 ? (
              <div className="p-10 text-center bg-slate-900/40 border border-slate-800 rounded-xl space-y-3">
                <HelpCircle className="w-10 h-10 text-slate-500 mx-auto" />
                <p className="text-sm font-semibold text-slate-300">
                  {totalConcepts === 0
                    ? "No Concept Mastery Data Available"
                    : "No Concepts Match Current Filter"}
                </p>
                <p className="text-xs text-slate-400 max-w-sm mx-auto">
                  {totalConcepts === 0
                    ? "Complete an adaptive quiz session to start generating dynamic evidence and tracking concept masteries."
                    : "Try selecting a different filter category or search term above."}
                </p>
                {totalConcepts === 0 && (
                  <button
                    onClick={() => navigate("/assessment")}
                    className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold rounded-xl transition shadow-md shadow-indigo-600/20"
                  >
                    Start Adaptive Quiz
                  </button>
                )}
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {filteredMasteries.map((item, idx) => {
                  const scorePct = Math.round((item.mastery_score || 0) * 100);
                  const isHigh = scorePct >= 75;
                  const isMedium = scorePct >= 50 && scorePct < 75;

                  return (
                    <div
                      key={idx}
                      className="p-4 bg-slate-900/80 rounded-xl border border-slate-800 space-y-3 hover:border-slate-700 transition"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-slate-100 text-sm">{item.concept_id}</span>
                        <div className="flex items-center gap-2">
                          <span
                            className={`text-xs px-2 py-0.5 rounded-full font-bold uppercase tracking-wider ${
                              isHigh
                                ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                                : isMedium
                                ? "bg-sky-500/10 text-sky-400 border border-sky-500/30"
                                : "bg-rose-500/10 text-rose-400 border border-rose-500/30"
                            }`}
                          >
                            {isHigh ? "Mastered" : isMedium ? "Developing" : "Needs Focus"}
                          </span>
                          <span className="font-mono text-base font-bold text-indigo-400">{scorePct}%</span>
                        </div>
                      </div>

                      {/* Progress Bar */}
                      <div className="w-full h-2.5 bg-slate-800 rounded-full overflow-hidden p-0.5 border border-slate-700/50">
                        <div
                          className={`h-full rounded-full transition-all duration-500 ${
                            isHigh ? "bg-emerald-500" : isMedium ? "bg-sky-500" : "bg-rose-500"
                          }`}
                          style={{ width: `${scorePct}%` }}
                        />
                      </div>

                      <div className="flex items-center justify-between text-xs pt-1 text-slate-400">
                        <span>
                          Confidence:{" "}
                          <strong className="text-slate-200">
                            {item.confidence ? `${Math.round(item.confidence * 100)}%` : "Normal"}
                          </strong>
                        </span>
                        <button
                          onClick={() => handleOpenExplanation(item.concept_id)}
                          className="text-indigo-400 hover:text-indigo-300 font-semibold hover:underline flex items-center gap-1"
                        >
                          <Sparkles className="w-3.5 h-3.5" />
                          <span>Why did this change?</span>
                        </button>
                      </div>
                    </div>
                  );
                })}
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

              {selectedConceptExplanation.evidence_breakdown &&
                selectedConceptExplanation.evidence_breakdown.length > 0 && (
                  <div className="space-y-2">
                    <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                      Evidence Trail:
                    </span>
                    <div className="space-y-2 max-h-40 overflow-y-auto pr-1">
                      {selectedConceptExplanation.evidence_breakdown.map((ev, i) => (
                        <div
                          key={i}
                          className="p-2.5 bg-slate-950/80 rounded-lg border border-slate-800 text-xs flex justify-between items-center"
                        >
                          <span className="font-mono text-slate-300 capitalize">{ev.event_type}</span>
                          <span
                            className={
                              ev.delta >= 0 ? "text-emerald-400 font-bold" : "text-rose-400 font-bold"
                            }
                          >
                            {ev.delta >= 0 ? "+" : ""}
                            {(ev.delta * 100).toFixed(1)}%
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
            </div>

            <div className="pt-2 flex justify-end">
              <button
                onClick={() => setSelectedConceptExplanation(null)}
                className="bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium px-4 py-2 rounded-lg"
              >
                Close Payload
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
