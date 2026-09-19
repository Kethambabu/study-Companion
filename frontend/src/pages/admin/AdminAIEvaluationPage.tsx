import React, { useEffect, useState } from 'react';
import { adminService, AIEvaluation } from '../../services/adminService';
import { ShieldCheck, MessageSquare, Database, FileCheck, Sparkles } from 'lucide-react';

export const AdminAIEvaluationPage: React.FC = () => {
  const [metrics, setMetrics] = useState<AIEvaluation | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchEval = async () => {
      try {
        const data = await adminService.getAIEvaluation();
        setMetrics(data);
      } catch (err) {
        console.error('Failed to fetch AI evaluation metrics:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchEval();
  }, []);

  if (loading) {
    return (
      <div className="flex h-48 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-500 border-t-transparent" />
      </div>
    );
  }
  const hasData = (metrics?.total_requests || 0) > 0;

  const tutorEval = metrics?.tutor_eval || {
    groundedness: 0,
    citation_correctness: 0,
    accuracy: 0,
    unsupported_handling: 0,
  };

  const retrievalEval = metrics?.retrieval_eval || {
    relevance: 0,
    source_quality: 0,
  };

  const assessmentEval = metrics?.assessment_eval || {
    question_quality: 0,
    grading_quality: 0,
    structured_output: 0,
  };

  const recommendationEval = metrics?.recommendations_eval || {
    relevance: 0,
    actionability: 0,
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="border-b border-slate-800 pb-4">
        <div className="flex items-center gap-2 text-indigo-400">
          <ShieldCheck className="h-6 w-6" />
          <h1 className="text-2xl font-bold text-white">AI Evaluation</h1>
        </div>
        <p className="text-xs text-slate-400">Continuous quality assessment, groundedness verification, and retrieval accuracy across AI experiences.</p>
      </div>

      {!hasData && (
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-8 text-center">
          <ShieldCheck className="mx-auto h-10 w-10 text-slate-600" />
          <h3 className="mt-3 text-sm font-semibold text-slate-300">No AI Evaluation Telemetry Logged Yet</h3>
          <p className="mt-1 text-xs text-slate-500">Evaluation metrics will automatically calculate as students interact with AI Tutor, Quizzes, and Recommendations.</p>
        </div>
      )}

      {/* PRD Section 26 Grid */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        {/* 1. Tutor */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur-md space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <MessageSquare className="h-4 w-4 text-indigo-400" /> Tutor Evaluation
            </h3>
            <span className="text-xs font-semibold text-emerald-400 bg-emerald-500/10 px-2.5 py-0.5 rounded border border-emerald-500/20">Optimal</span>
          </div>
          <div className="space-y-3 text-xs">
            <div className="flex justify-between items-center">
              <span className="text-slate-300">Groundedness</span>
              <span className="font-bold text-indigo-400 text-sm">{tutorEval.groundedness}%</span>
            </div>
            <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
              <div className="h-full bg-indigo-500 rounded-full" style={{ width: `${tutorEval.groundedness}%` }} />
            </div>

            <div className="flex justify-between items-center pt-1">
              <span className="text-slate-300">Citation Correctness</span>
              <span className="font-bold text-emerald-400 text-sm">{tutorEval.citation_correctness}%</span>
            </div>
            <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
              <div className="h-full bg-emerald-500 rounded-full" style={{ width: `${tutorEval.citation_correctness}%` }} />
            </div>

            <div className="flex justify-between items-center pt-1">
              <span className="text-slate-300">Accuracy</span>
              <span className="font-bold text-purple-400 text-sm">{tutorEval.accuracy}%</span>
            </div>
            <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
              <div className="h-full bg-purple-500 rounded-full" style={{ width: `${tutorEval.accuracy}%` }} />
            </div>

            <div className="flex justify-between items-center pt-1">
              <span className="text-slate-300">Unsupported Handling</span>
              <span className="font-bold text-blue-400 text-sm">{tutorEval.unsupported_handling}%</span>
            </div>
            <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
              <div className="h-full bg-blue-500 rounded-full" style={{ width: `${tutorEval.unsupported_handling}%` }} />
            </div>
          </div>
        </div>

        {/* 2. Retrieval */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur-md space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Database className="h-4 w-4 text-purple-400" /> Retrieval Evaluation
            </h3>
            <span className="text-xs font-semibold text-emerald-400 bg-emerald-500/10 px-2.5 py-0.5 rounded border border-emerald-500/20">High Quality</span>
          </div>
          <div className="space-y-4 text-xs">
            <div className="space-y-1.5">
              <div className="flex justify-between items-center">
                <span className="text-slate-300">Relevance</span>
                <span className="font-bold text-purple-400 text-sm">{retrievalEval.relevance}%</span>
              </div>
              <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
                <div className="h-full bg-purple-500 rounded-full" style={{ width: `${retrievalEval.relevance}%` }} />
              </div>
            </div>

            <div className="space-y-1.5 pt-2">
              <div className="flex justify-between items-center">
                <span className="text-slate-300">Source Quality</span>
                <span className="font-bold text-indigo-400 text-sm">{retrievalEval.source_quality}%</span>
              </div>
              <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
                <div className="h-full bg-indigo-500 rounded-full" style={{ width: `${retrievalEval.source_quality}%` }} />
              </div>
            </div>
          </div>
        </div>

        {/* 3. Assessment */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur-md space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <FileCheck className="h-4 w-4 text-blue-400" /> Assessment Evaluation
            </h3>
            <span className="text-xs font-semibold text-indigo-400 bg-indigo-500/10 px-2.5 py-0.5 rounded border border-indigo-500/20">Verified</span>
          </div>
          <div className="space-y-3 text-xs">
            <div className="flex justify-between items-center">
              <span className="text-slate-300">Question Quality</span>
              <span className="font-bold text-blue-400 text-sm">{assessmentEval.question_quality}%</span>
            </div>
            <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
              <div className="h-full bg-blue-500 rounded-full" style={{ width: `${assessmentEval.question_quality}%` }} />
            </div>

            <div className="flex justify-between items-center pt-1">
              <span className="text-slate-300">Grading Quality</span>
              <span className="font-bold text-indigo-400 text-sm">{assessmentEval.grading_quality}%</span>
            </div>
            <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
              <div className="h-full bg-indigo-500 rounded-full" style={{ width: `${assessmentEval.grading_quality}%` }} />
            </div>

            <div className="flex justify-between items-center pt-1">
              <span className="text-slate-300">Structured Output</span>
              <span className="font-bold text-emerald-400 text-sm">{assessmentEval.structured_output}%</span>
            </div>
            <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
              <div className="h-full bg-emerald-500 rounded-full" style={{ width: `${assessmentEval.structured_output}%` }} />
            </div>
          </div>
        </div>

        {/* 4. Recommendations */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur-md space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-emerald-400" /> Recommendations
            </h3>
            <span className="text-xs font-semibold text-emerald-400 bg-emerald-500/10 px-2.5 py-0.5 rounded border border-emerald-500/20">Active</span>
          </div>
          <div className="space-y-4 text-xs">
            <div className="space-y-1.5">
              <div className="flex justify-between items-center">
                <span className="text-slate-300">Relevance</span>
                <span className="font-bold text-emerald-400 text-sm">{recommendationEval.relevance}%</span>
              </div>
              <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
                <div className="h-full bg-emerald-500 rounded-full" style={{ width: `${recommendationEval.relevance}%` }} />
              </div>
            </div>

            <div className="space-y-1.5 pt-2">
              <div className="flex justify-between items-center">
                <span className="text-slate-300">Actionability</span>
                <span className="font-bold text-purple-400 text-sm">{recommendationEval.actionability}%</span>
              </div>
              <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
                <div className="h-full bg-purple-500 rounded-full" style={{ width: `${recommendationEval.actionability}%` }} />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

