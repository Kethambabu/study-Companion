import React, { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import {
  recommendationService,
  NextActionCardData,
} from "@/services/recommendationService";
import {
  Sparkles,
  ArrowRight,
  CheckCircle2,
  BrainCircuit,
  BookOpen,
  MessageSquare,
  AlertCircle,
} from "lucide-react";

interface NextActionCardProps {
  projectId: string;
}

export const NextActionCard: React.FC<NextActionCardProps> = ({ projectId }) => {
  const navigate = useNavigate();
  const [data, setData] = useState<NextActionCardData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [completing, setCompleting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchNextAction = useCallback(async () => {
    if (!projectId) return;
    try {
      setLoading(true);
      setError(null);
      const res = await recommendationService.getNextActionCard(projectId);
      setData(res);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load Next Action.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    fetchNextAction();
  }, [fetchNextAction]);

  const handleMarkComplete = async () => {
    if (!data?.recommendation || !projectId) return;
    try {
      setCompleting(true);
      await recommendationService.completeRecommendation(projectId, data.recommendation.id);
      await fetchNextAction();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to complete action.";
      setError(msg);
    } finally {
      setCompleting(false);
    }
  };

  if (loading) {
    return (
      <div className="p-6 bg-slate-800/80 border border-slate-700/80 rounded-2xl animate-pulse space-y-3">
        <div className="h-4 bg-slate-700 w-1/4 rounded"></div>
        <div className="h-6 bg-slate-700 w-3/4 rounded"></div>
      </div>
    );
  }

  if (error || !data || !data.recommendation) {
    return null;
  }

  const rec = data.recommendation;

  const getActionIcon = (type: string) => {
    switch (type) {
      case "ask_tutor":
        return <MessageSquare className="w-5 h-5 text-indigo-400" />;
      case "review_material":
        return <BookOpen className="w-5 h-5 text-sky-400" />;
      default:
        return <BrainCircuit className="w-5 h-5 text-emerald-400" />;
    }
  };

  return (
    <div className="p-6 bg-gradient-to-r from-indigo-950/40 via-slate-900/90 to-slate-900 border border-indigo-500/30 rounded-2xl shadow-xl space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-indigo-400">
          <Sparkles className="w-4 h-4" />
          Recommended Next Action
        </div>
        <span className="text-xs px-2.5 py-0.5 rounded-full font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
          Priority: {(rec.priority_score * 100).toFixed(0)}%
        </span>
      </div>

      <div className="flex items-start gap-3">
        <div className="p-2.5 bg-slate-800 rounded-xl border border-slate-700 flex-shrink-0">
          {getActionIcon(rec.action_type)}
        </div>

        <div className="space-y-1">
          <h3 className="text-lg font-bold text-slate-100">{rec.title}</h3>
          <p className="text-sm text-slate-300 leading-relaxed">{rec.description}</p>
        </div>
      </div>

      {/* Rationale & Evidence Traceability */}
      <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800/80 text-xs text-slate-400 flex items-start gap-2">
        <AlertCircle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
        <div>
          <strong className="text-slate-300">Why this action:</strong> {data.reason}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex items-center justify-end gap-3 pt-2">
        <button
          onClick={handleMarkComplete}
          disabled={completing}
          className="text-xs text-slate-400 hover:text-emerald-400 flex items-center gap-1 font-medium transition-colors"
        >
          <CheckCircle2 className="w-4 h-4" /> Mark Complete
        </button>

        <button
          onClick={() => navigate(data.cta_path)}
          className="bg-indigo-600 hover:bg-indigo-500 text-white font-medium px-5 py-2 rounded-xl text-sm flex items-center gap-2 shadow-lg shadow-indigo-600/30 transition-all"
        >
          {data.cta_label} <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
