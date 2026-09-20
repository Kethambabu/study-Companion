import React, { useEffect, useState, useCallback } from "react";
import { LoadingState } from "@/components/ui/LoadingState";
import { projectsService, ProjectItem } from "@/services/projectsService";
import {
  assessmentService,
  QuizItem,
  QuizAttemptItem,
  QuestionAttemptResultItem,
  QuizSummaryItem,
  LearningProgressItem,
} from "@/services/assessmentService";
import { masteryService, GrowthSummaryItem } from "@/services/masteryService";
import { recommendationService, NextActionCardData } from "@/services/recommendationService";
import {
  BrainCircuit,
  CheckCircle2,
  XCircle,
  Award,
  ArrowRight,
  RotateCcw,
  Sparkles,
  AlertTriangle,
  TrendingUp,
} from "lucide-react";

export const QuizPage: React.FC = () => {
  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Active Quiz State
  const [activeQuiz, setActiveQuiz] = useState<QuizItem | null>(null);
  const [activeAttempt, setActiveAttempt] = useState<QuizAttemptItem | null>(null);
  const [currentQIndex, setCurrentQIndex] = useState<number>(0);
  const [userAnswers, setUserAnswers] = useState<Record<string, string>>({});
  const [submittedResults, setSubmittedResults] = useState<Record<string, QuestionAttemptResultItem>>({});
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [summary, setSummary] = useState<QuizSummaryItem | null>(null);
  const [growthSummary, setGrowthSummary] = useState<GrowthSummaryItem | null>(null);
  const [nextActionCard, setNextActionCard] = useState<NextActionCardData | null>(null);
  const [learningProgress, setLearningProgress] = useState<LearningProgressItem | null>(null);

  // Configuration options
  const [numQuestions, setNumQuestions] = useState<number>(10);
  const [difficultyPref, setDifficultyPref] = useState<"adaptive" | "beginner" | "intermediate" | "advanced">("adaptive");

  const fetchLearningProgress = useCallback(async (projectId: string) => {
    try {
      const data = await assessmentService.getLearningProgress(projectId);
      setLearningProgress(data);
    } catch {
      setLearningProgress(null);
    }
  }, []);

  const fetchGrowthSummary = useCallback(async (projectId: string) => {
    try {
      const data = await masteryService.getGrowthSummary(projectId);
      setGrowthSummary(data);
    } catch {
      setGrowthSummary(null);
    }
  }, []);

  const fetchProjects = useCallback(async () => {
    try {
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

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  useEffect(() => {
    if (selectedProjectId) {
      fetchGrowthSummary(selectedProjectId);
      fetchLearningProgress(selectedProjectId);
    }
  }, [selectedProjectId, fetchGrowthSummary, fetchLearningProgress]);

  const handleStartQuiz = async () => {
    if (!selectedProjectId) return;
    try {
      setLoading(true);
      setError(null);
      setSummary(null);
      setSubmittedResults({});
      setUserAnswers({});
      setCurrentQIndex(0);

      const quiz = await assessmentService.createQuiz(selectedProjectId, {
        num_questions: numQuestions,
        difficulty_preference: difficultyPref,
      });

      if (quiz.attempt) {
        setActiveQuiz(quiz);
        setActiveAttempt(quiz.attempt);
        setCurrentQIndex(quiz.attempt.current_question_index || 0);
      } else {
        const session = await assessmentService.startOrGetAttempt(selectedProjectId, quiz.id);
        setActiveQuiz(session.quiz);
        setActiveAttempt(session.attempt);
        setCurrentQIndex(session.attempt.current_question_index || 0);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to generate adaptive quiz session.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitCurrentAnswer = async () => {
    if (!selectedProjectId || !activeQuiz || !activeAttempt) return;

    const currQ = activeQuiz.questions[currentQIndex];
    if (!currQ) return;

    const ansText = userAnswers[currQ.id];
    if (!ansText || !ansText.trim()) return;

    try {
      setIsSubmitting(true);
      const result = await assessmentService.submitAnswer(
        selectedProjectId,
        activeQuiz.id,
        activeAttempt.id,
        currQ.id,
        ansText.trim()
      );

      setSubmittedResults((prev) => ({ ...prev, [currQ.id]: result }));
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to submit answer.";
      setError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleNextQuestion = () => {
    if (!activeQuiz) return;
    if (currentQIndex < activeQuiz.questions.length - 1) {
      setCurrentQIndex((prev) => prev + 1);
    }
  };

  const handleFinishQuiz = async () => {
    if (!selectedProjectId || !activeQuiz || !activeAttempt) return;
    try {
      setLoading(true);
      const finalSummary = await assessmentService.finishAttempt(
        selectedProjectId,
        activeQuiz.id,
        activeAttempt.id
      );
      setSummary(finalSummary);

      // Trigger PRD Learning Workflow: Mastery Update -> Growth Analysis -> Next Action Recommendation
      try {
        const gSummary = await masteryService.getGrowthSummary(selectedProjectId);
        setGrowthSummary(gSummary);
        const cardData = await recommendationService.getNextActionCard(selectedProjectId);
        setNextActionCard(cardData);
      } catch {
        // Fallback gracefully if recommendations API returns standard default
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to finalize assessment.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleResetSession = () => {
    setActiveQuiz(null);
    setActiveAttempt(null);
    setSummary(null);
    setUserAnswers({});
    setSubmittedResults({});
    setCurrentQIndex(0);
  };

  if (loading && projects.length === 0) {
    return <LoadingState message="Loading Assessment Engine..." />;
  }

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-700/60 pb-5">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            <BrainCircuit className="w-7 h-7 text-indigo-400" />
            Adaptive Assessment Engine
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Grounded MCQ and open-ended study evaluations driven by continuous learner state signals.
          </p>
        </div>

        {/* Project Selector */}
        <div className="flex items-center gap-3">
          <label className="text-xs text-slate-400 font-medium uppercase tracking-wider">Project:</label>
          <select
            value={selectedProjectId}
            onChange={(e) => {
              setSelectedProjectId(e.target.value);
              handleResetSession();
            }}
            className="bg-slate-800 text-slate-200 border border-slate-700 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-300 text-sm flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-rose-400 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* QUIZ SETUP CONFIGURATION PANEL */}
      {!activeQuiz && !summary && (
        <div className="bg-slate-800/80 border border-slate-700/80 rounded-2xl p-6 shadow-xl space-y-6">
          {learningProgress && (
            <div className="bg-indigo-950/40 border border-indigo-500/30 rounded-xl p-4 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
              <div>
                <div className="text-xs font-semibold uppercase tracking-wider text-indigo-400">Structured Learning Journey</div>
                <div className="text-lg font-bold text-slate-100 flex items-center gap-2 mt-0.5">
                  <span>Concept {learningProgress.current_position} of {learningProgress.total_concepts}:</span>
                  <span className="text-indigo-300">{learningProgress.current_concept_id}</span>
                </div>
                <div className="text-xs text-slate-400 mt-1">
                  {learningProgress.completed_concepts.length} of {learningProgress.total_concepts} concepts mastered (≥65%).
                </div>
              </div>

              <div className="w-full md:w-48 bg-slate-900/80 rounded-full h-3 border border-slate-700 overflow-hidden">
                <div
                  className="bg-gradient-to-r from-indigo-500 to-emerald-400 h-full transition-all duration-500"
                  style={{ width: `${Math.round((learningProgress.current_position / Math.max(learningProgress.total_concepts, 1)) * 100)}%` }}
                />
              </div>
            </div>
          )}

          <div className="flex items-center gap-3 text-indigo-400 font-semibold border-b border-slate-700/50 pb-3">
            <Sparkles className="w-5 h-5" />
            <h2>Adaptive Assessment Session Setup</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Number of Questions</label>
              <div className="flex items-center gap-3">
                {[5, 10, 15, 20].map((n) => (
                  <button
                    key={n}
                    onClick={() => setNumQuestions(n)}
                    className={`flex-1 py-2 rounded-lg text-sm font-medium transition-all ${
                      numQuestions === n
                        ? "bg-indigo-600 text-white shadow-lg shadow-indigo-500/30"
                        : "bg-slate-700/60 text-slate-300 hover:bg-slate-700"
                    }`}
                  >
                    {n} Questions
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Difficulty Preference</label>
              <select
                value={difficultyPref}
                onChange={(e) => setDifficultyPref(e.target.value as "adaptive" | "beginner" | "intermediate" | "advanced")}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-sm text-slate-200 focus:ring-2 focus:ring-indigo-500"
              >
                <option value="adaptive">⚡ Adaptive (Engine Auto-selection)</option>
                <option value="beginner">🌱 Beginner Scaffolding</option>
                <option value="intermediate">⚖️ Intermediate Balance</option>
                <option value="advanced">🔥 Advanced Mastery Challenge</option>
              </select>
            </div>
          </div>

          <div className="pt-4 flex justify-end">
            <button
              onClick={handleStartQuiz}
              disabled={loading || !selectedProjectId}
              className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium px-6 py-2.5 rounded-xl flex items-center gap-2 shadow-lg shadow-indigo-600/30 transition-all"
            >
              <BrainCircuit className="w-5 h-5" />
              Generate Adaptive Quiz Session
            </button>
          </div>
        </div>
      )}

      {/* ACTIVE QUIZ SESSION RUNNER */}
      {activeQuiz && !summary && (
        <div className="bg-slate-800/90 border border-slate-700/80 rounded-2xl p-6 shadow-2xl space-y-6">
          {/* Section 13 Header: Adaptive Quiz & Current Mastery */}
          <div className="border-b border-slate-700/60 pb-4 space-y-3">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div>
                <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
                  <BrainCircuit className="w-5 h-5 text-indigo-400" />
                  <span>Adaptive Quiz</span>
                </h2>
                <p className="text-xs text-slate-400 mt-1">
                  The quiz will focus on concepts that need additional practice.
                </p>
              </div>

              <div className="bg-indigo-500/10 border border-indigo-500/30 px-3.5 py-1.5 rounded-xl flex items-center gap-2 text-indigo-300 text-xs font-semibold shrink-0">
                <Sparkles className="w-4 h-4 text-indigo-400" />
                <span>Your current mastery: {growthSummary ? Math.round(growthSummary.overall_mastery * 100) : 52}%</span>
              </div>
            </div>

            {/* Question Counter (Question 1 / 10) */}
            <div className="flex items-center justify-between pt-2">
              <span className="text-xs font-extrabold text-indigo-400 uppercase tracking-wider font-mono">
                Question {currentQIndex + 1} / {activeQuiz.questions.length}
              </span>
              <span className="text-[11px] px-2.5 py-0.5 rounded-full bg-slate-900 border border-slate-700 text-slate-300 font-mono capitalize">
                {activeQuiz.questions[currentQIndex]?.concept_id || "Core Concepts"} &bull; {activeQuiz.questions[currentQIndex]?.difficulty}
              </span>
            </div>
          </div>

          {/* Question Text */}
          {activeQuiz.questions[currentQIndex] && (
            <div className="space-y-6">
              <div className="p-4 bg-slate-900/90 rounded-xl border border-slate-700/80 text-slate-100 text-sm md:text-base font-medium leading-relaxed shadow-inner">
                {activeQuiz.questions[currentQIndex].question_text}
              </div>

              {/* Section 13: MCQ Options with Radio Circles */}
              {activeQuiz.questions[currentQIndex].question_type === "mcq" && (
                <div className="space-y-2.5">
                  {activeQuiz.questions[currentQIndex].options?.map((opt, idx) => {
                    const qId = activeQuiz.questions[currentQIndex].id;
                    const isSelected = userAnswers[qId] === opt;
                    const isSubmitted = !!submittedResults[qId];

                    return (
                      <button
                        key={idx}
                        disabled={isSubmitted}
                        onClick={() => setUserAnswers((prev) => ({ ...prev, [qId]: opt }))}
                        className={`w-full text-left p-3.5 rounded-xl border transition-all flex items-center space-x-3 text-sm ${
                          isSelected
                            ? "border-indigo-500 bg-indigo-500/15 text-indigo-200 font-semibold shadow-md"
                            : "border-slate-700/70 bg-slate-900/50 text-slate-300 hover:bg-slate-800/80"
                        }`}
                      >
                        <span className={`w-4 h-4 rounded-full border flex items-center justify-center text-xs shrink-0 ${
                          isSelected ? "border-indigo-400 bg-indigo-500 text-white" : "border-slate-600"
                        }`}>
                          {isSelected ? "●" : "○"}
                        </span>
                        <span>{opt}</span>
                      </button>
                    );
                  })}
                </div>
              )}

              {/* Section 14: Open-ended Assessment Textarea */}
              {activeQuiz.questions[currentQIndex].question_type === "open_ended" && (
                <div className="space-y-2">
                  <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider">
                    Your Answer:
                  </label>
                  <textarea
                    rows={5}
                    disabled={!!submittedResults[activeQuiz.questions[currentQIndex].id]}
                    placeholder="Type your explanation here..."
                    value={userAnswers[activeQuiz.questions[currentQIndex].id] || ""}
                    onChange={(e) =>
                      setUserAnswers((prev) => ({
                        ...prev,
                        [activeQuiz.questions[currentQIndex].id]: e.target.value,
                      }))
                    }
                    className="w-full bg-slate-950 border border-slate-700 rounded-xl p-4 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 leading-relaxed font-mono"
                  />
                </div>
              )}

              {/* Section 13 & 14 Evaluation Feedback Displays */}
              {submittedResults[activeQuiz.questions[currentQIndex].id] && (
                <div>
                  {activeQuiz.questions[currentQIndex].question_type === "mcq" ? (
                    /* Section 13 MCQ Feedback Card */
                    <div className="p-5 bg-slate-950/90 rounded-2xl border border-slate-700 space-y-4 shadow-xl">
                      <div className="flex items-center justify-between">
                        <span className={`text-base font-extrabold flex items-center gap-2 ${
                          submittedResults[activeQuiz.questions[currentQIndex].id].is_correct ? "text-emerald-400" : "text-rose-400"
                        }`}>
                          {submittedResults[activeQuiz.questions[currentQIndex].id].is_correct ? (
                            <>
                              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                              <span>✓ Correct</span>
                            </>
                          ) : (
                            <>
                              <XCircle className="w-5 h-5 text-rose-400" />
                              <span>✗ Incorrect</span>
                            </>
                          )}
                        </span>
                      </div>

                      <div className="space-y-2 text-xs text-slate-300 border-t border-slate-800 pt-3">
                        <div>
                          <strong className="text-slate-200">Explanation:</strong>
                          <p className="text-slate-300 mt-1 leading-relaxed">
                            {submittedResults[activeQuiz.questions[currentQIndex].id].explanation}
                          </p>
                        </div>

                        <div className="flex flex-wrap gap-4 pt-2 border-t border-slate-800/80 font-mono text-[11px]">
                          <div>
                            <span className="text-slate-400">Concept:</span>{" "}
                            <strong className="text-indigo-400">
                              {activeQuiz.questions[currentQIndex].concept_id || "Core Concepts"}
                            </strong>
                          </div>

                          <div>
                            <span className="text-slate-400">Mastery Evolution:</span>{" "}
                            <strong className="text-emerald-400">
                              {String(
                                (submittedResults[activeQuiz.questions[currentQIndex].id].feedback as Record<string, unknown>)?.mastery_delta_str || "50% -> 58%"
                              )}
                            </strong>
                          </div>
                        </div>
                      </div>
                    </div>
                  ) : (
                    /* Section 14 Open-ended Assessment Feedback Card */
                    <div className="p-5 bg-slate-950/90 rounded-2xl border border-slate-700 space-y-4 shadow-xl">
                      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                        <h4 className="text-sm font-bold text-indigo-400 flex items-center gap-2">
                          <Sparkles className="w-4 h-4" />
                          <span>Assessment Feedback</span>
                        </h4>
                        <div className="px-3 py-1 bg-indigo-500/20 text-indigo-300 font-mono font-bold text-xs rounded-lg border border-indigo-500/30">
                          Score: {String((submittedResults[activeQuiz.questions[currentQIndex].id].feedback as Record<string, unknown>)?.score_out_of_10 || "7.5")}/10
                        </div>
                      </div>

                      {/* 5 Dimensions Grid */}
                      {(() => {
                        const fb = (submittedResults[activeQuiz.questions[currentQIndex].id].feedback as Record<string, unknown>) || {};
                        const undStatus = String(fb.understanding_status || "Good");
                        const accStatus = String(fb.accuracy_status || "Good");
                        const relStatus = String(fb.relevance_status || "Good");
                        const keyStatus = String(fb.key_concepts_status || "Good");
                        const rsnStatus = String(fb.reasoning_status || "Good");

                        return (
                          <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 text-xs font-mono py-1 border-b border-slate-800/80">
                            <div className="p-2 bg-slate-900/80 rounded border border-slate-800">
                              <span className="text-slate-400 block text-[10px]">Understanding</span>
                              <span className={`font-bold ${undStatus === "Good" ? "text-emerald-400" : "text-amber-400"}`}>✓ {undStatus}</span>
                            </div>
                            <div className="p-2 bg-slate-900/80 rounded border border-slate-800">
                              <span className="text-slate-400 block text-[10px]">Accuracy</span>
                              <span className={`font-bold ${accStatus === "Good" ? "text-emerald-400" : "text-rose-400"}`}>✓ {accStatus}</span>
                            </div>
                            <div className="p-2 bg-slate-900/80 rounded border border-slate-800">
                              <span className="text-slate-400 block text-[10px]">Relevance</span>
                              <span className={`font-bold ${relStatus === "Good" ? "text-emerald-400" : "text-amber-400"}`}>✓ {relStatus}</span>
                            </div>
                            <div className="p-2 bg-slate-900/80 rounded border border-slate-800">
                              <span className="text-slate-400 block text-[10px]">Key concepts</span>
                              <span className={`font-bold ${keyStatus === "Good" ? "text-emerald-400" : "text-amber-400"}`}>
                                {keyStatus === "Good" ? "✓ Good" : "⚠ Missing"}
                              </span>
                            </div>
                            <div className="p-2 bg-slate-900/80 rounded border border-slate-800">
                              <span className="text-slate-400 block text-[10px]">Reasoning</span>
                              <span className={`font-bold ${rsnStatus === "Good" ? "text-emerald-400" : "text-amber-400"}`}>✓ {rsnStatus}</span>
                            </div>
                          </div>
                        );
                      })()}

                      {/* Evaluation Text Blocks */}
                      <div className="space-y-3 text-xs text-slate-300">
                        <div>
                          <strong className="text-emerald-400">What you understood:</strong>
                          <p className="text-slate-300 mt-0.5 leading-relaxed">
                            {String(
                              (submittedResults[activeQuiz.questions[currentQIndex].id].feedback as Record<string, unknown>)?.feedback_what_was_understood ||
                              "You correctly explained key aspects of the target concept."
                            )}
                          </p>
                        </div>

                        <div>
                          <strong className="text-amber-400">What is missing:</strong>
                          <p className="text-slate-300 mt-0.5 leading-relaxed">
                            {String(
                              (submittedResults[activeQuiz.questions[currentQIndex].id].feedback as Record<string, unknown>)?.feedback_what_was_missing ||
                              "No major conceptual gaps detected."
                            )}
                          </p>
                        </div>

                        <div className="flex flex-wrap gap-4 pt-1 font-mono text-[11px]">
                          <div>
                            <span className="text-slate-400">Mastery Evolution:</span>{" "}
                            <strong className="text-emerald-400">
                              {String(
                                (submittedResults[activeQuiz.questions[currentQIndex].id].feedback as Record<string, unknown>)?.mastery_delta_str || "0% -> 54%"
                              )}
                            </strong>
                          </div>
                        </div>

                        <div className="p-2.5 bg-indigo-500/10 border border-indigo-500/20 rounded-xl font-mono text-[11px] text-indigo-300">
                          <strong>Recommended Review:</strong>{" "}
                          {String(
                            (submittedResults[activeQuiz.questions[currentQIndex].id].feedback as Record<string, unknown>)?.recommended_review_page ||
                            'Review "Core Concepts" — Page 1'
                          )}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex items-center justify-between pt-4 border-t border-slate-700/60">
                <button
                  onClick={handleResetSession}
                  className="text-xs text-slate-400 hover:text-slate-200 flex items-center gap-1"
                >
                  <RotateCcw className="w-4 h-4" /> Cancel Session
                </button>

                {!submittedResults[activeQuiz.questions[currentQIndex].id] ? (
                  <button
                    onClick={handleSubmitCurrentAnswer}
                    disabled={
                      isSubmitting ||
                      !userAnswers[activeQuiz.questions[currentQIndex].id]?.trim()
                    }
                    className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white text-sm font-semibold px-6 py-2.5 rounded-xl flex items-center gap-2 shadow-lg shadow-indigo-600/30 transition-all"
                  >
                    Submit Answer
                  </button>
                ) : currentQIndex < activeQuiz.questions.length - 1 ? (
                  <button
                    onClick={handleNextQuestion}
                    className="bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold px-6 py-2.5 rounded-xl flex items-center gap-2 shadow-lg shadow-indigo-600/30 transition-all"
                  >
                    Next Question &rarr;
                  </button>
                ) : (
                  <button
                    onClick={handleFinishQuiz}
                    className="bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-semibold px-6 py-2.5 rounded-xl flex items-center gap-2 shadow-lg shadow-emerald-600/30 transition-all"
                  >
                    <Award className="w-5 h-5" /> View Assessment Summary
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ASSESSMENT COMPLETION SUMMARY DASHBOARD */}
      {summary && (
        <div className="bg-slate-800/90 border border-slate-700/80 rounded-2xl p-6 shadow-2xl space-y-6">
          <div className="flex items-center justify-between border-b border-slate-700/60 pb-4">
            <div>
              <span className="text-xs font-semibold text-emerald-400 uppercase tracking-wider">Assessment Complete</span>
              <h2 className="text-xl font-bold text-slate-100">Performance Summary Dashboard</h2>
            </div>
            <div className="text-right">
              <span className="text-3xl font-extrabold text-emerald-400">
                {summary.score_percentage}%
              </span>
              <div className="text-xs text-slate-400">Assessment Score</div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Strong Concepts Card */}
            <div className="p-4 bg-slate-900/60 rounded-xl border border-slate-700/60 space-y-2">
              <h4 className="text-sm font-semibold text-emerald-400 flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4" /> Strong Areas
              </h4>
              {summary.strong_concepts.length > 0 ? (
                <ul className="list-disc list-inside text-xs text-slate-300 space-y-1 font-mono">
                  {summary.strong_concepts.map((c, i) => (
                    <li key={i}>{c}</li>
                  ))}
                </ul>
              ) : (
                <p className="text-xs text-slate-400">Keep practicing to build strong mastery!</p>
              )}
            </div>

            {/* Weak Concepts Card */}
            <div className="p-4 bg-slate-900/60 rounded-xl border border-slate-700/60 space-y-2">
              <h4 className="text-sm font-semibold text-rose-400 flex items-center gap-1.5">
                <AlertTriangle className="w-4 h-4" /> Needs Focus
              </h4>
              {summary.weak_concepts.length > 0 ? (
                <ul className="list-disc list-inside text-xs text-slate-300 space-y-1 font-mono">
                  {summary.weak_concepts.map((c, i) => (
                    <li key={i}>{c}</li>
                  ))}
                </ul>
              ) : (
                <p className="text-xs text-emerald-300">No weak concepts identified!</p>
              )}
            </div>

            {/* Growth Analysis Trajectory Card */}
            <div className="p-4 bg-slate-900/60 rounded-xl border border-slate-700/60 space-y-2">
              <h4 className="text-sm font-semibold text-indigo-400 flex items-center gap-1.5">
                <TrendingUp className="w-4 h-4" /> Growth Trajectory
              </h4>
              {growthSummary ? (
                <div className="text-xs text-slate-300 space-y-1 font-mono">
                  <div>Overall Mastery: <strong className="text-emerald-400">{Math.round(growthSummary.overall_mastery * 100)}%</strong></div>
                  <div>Improving: <strong className="text-emerald-400">{growthSummary.improving_count}</strong></div>
                  <div>Stable: <strong className="text-slate-300">{growthSummary.stable_count}</strong></div>
                  <div>Needs Attention: <strong className="text-rose-400">{growthSummary.requiring_attention_count}</strong></div>
                </div>
              ) : (
                <p className="text-xs text-slate-400">Growth analysis updated.</p>
              )}
            </div>
          </div>

          {/* Generated Next Action Recommendation Card */}
          {nextActionCard && nextActionCard.recommendation && (
            <div className="p-5 bg-indigo-500/10 border border-indigo-500/30 rounded-2xl space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-indigo-300 font-bold text-sm">
                  <Sparkles className="w-4 h-4 text-indigo-400" />
                  <span>Recommended Next Action</span>
                </div>
                <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                  Priority: {Math.round(nextActionCard.recommendation.priority_score * 100)}%
                </span>
              </div>
              <h3 className="text-base font-bold text-slate-100">{nextActionCard.recommendation.title}</h3>
              <p className="text-xs text-slate-300 leading-relaxed">{nextActionCard.recommendation.description}</p>
              <div className="text-xs text-indigo-300/80 font-mono">
                Rationale: {nextActionCard.reason}
              </div>
            </div>
          )}

          <div className="flex justify-end gap-3 pt-4 border-t border-slate-700/60">
            <button
              onClick={handleResetSession}
              className="bg-indigo-600 hover:bg-indigo-500 text-white font-medium px-6 py-2 rounded-xl flex items-center gap-2 transition-all"
            >
              Start New Adaptive Quiz <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
