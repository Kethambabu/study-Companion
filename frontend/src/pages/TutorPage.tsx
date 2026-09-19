import React, { useEffect, useState, useCallback, useRef } from "react";

import { projectsService, ProjectItem } from "@/services/projectsService";
import {
  tutorService,
  ConversationItem,
  ConversationMessageItem,
} from "@/services/tutorService";
import {
  Bot,
  User,
  Send,
  Plus,
  MessageSquare,
  Sparkles,
  HelpCircle,
  FileCode,
  BookOpen,
  AlertTriangle,
  RotateCcw,
} from "lucide-react";

export const TutorPage: React.FC = () => {
  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");

  const [conversations, setConversations] = useState<ConversationItem[]>([]);
  const [activeConvId, setActiveConvId] = useState<string>("");
  const [messages, setMessages] = useState<ConversationMessageItem[]>([]);

  const [inputContent, setInputContent] = useState("");
  const [sending, setSending] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sourceModal, setSourceModal] = useState<{ title: string; page: number; excerpt: string } | null>(null);
  const [showLearningContext, setShowLearningContext] = useState<boolean>(false);
  const [learningContextText, setLearningContextText] = useState<string>("");
  const [selectedMode, setSelectedMode] = useState<"default" | "explain_simpler" | "give_example" | "test_me">("default");

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // 1. Fetch available projects on mount
  useEffect(() => {
    let isMounted = true;
    projectsService
      .listProjects(undefined, "active", undefined, 1, 100)
      .then((res) => {
        if (!isMounted) return;
        setProjects(res.items);
        if (res.items.length > 0) {
          setSelectedProjectId((prev) => prev || res.items[0].id);
        } else {
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (!isMounted) return;
        setError(err instanceof Error ? err.message : "Failed to load projects.");
        setLoading(false);
      });
    return () => {
      isMounted = false;
    };
  }, []);

  // 2. Fetch conversations when selected project changes
  const fetchConversations = useCallback(async () => {
    if (!selectedProjectId) return;
    setLoading(true);
    setError(null);
    setActiveConvId("");
    setMessages([]);
    try {
      const list = await tutorService.listConversations(selectedProjectId);
      setConversations(list);
      if (list.length > 0) {
        setActiveConvId(list[0].id);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load conversations.");
    } finally {
      setLoading(false);
    }
  }, [selectedProjectId]);

  useEffect(() => {
    fetchConversations();
  }, [fetchConversations]);

  // 3. Fetch messages when active conversation changes
  const fetchMessages = useCallback(async () => {
    if (!selectedProjectId || !activeConvId) return;
    // Verify activeConvId belongs to currently loaded project conversations
    if (conversations.length > 0 && !conversations.some((c) => c.id === activeConvId)) {
      return;
    }
    try {
      const res = await tutorService.getMessages(selectedProjectId, activeConvId);
      setMessages(res.items);
      setTimeout(scrollToBottom, 100);
    } catch {
      // Soft error
    }
  }, [selectedProjectId, activeConvId, conversations]);

  useEffect(() => {
    fetchMessages();
  }, [fetchMessages]);

  const handleCreateNewConv = async () => {
    if (!selectedProjectId) return;
    try {
      const newConv = await tutorService.createConversation(selectedProjectId, "New Study Session");
      setConversations((prev) => [newConv, ...prev]);
      setActiveConvId(newConv.id);
      setMessages([]);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create new conversation.");
    }
  };

  const openLearningContextModal = async () => {
    setShowLearningContext(true);
    if (selectedProjectId) {
      try {
        const text = await tutorService.getLearningContext(selectedProjectId);
        setLearningContextText(text);
      } catch {
        setLearningContextText("Learner Context: Target mastery goals and active course practice.");
      }
    }
  };

  const handleSendMessage = async (
    overrideContent?: string,
    overrideMode?: "default" | "explain_simpler" | "give_example" | "test_me"
  ) => {
    const messageText = overrideContent || inputContent;
    const mode = overrideMode || selectedMode;
    if (!selectedProjectId || !activeConvId || !messageText.trim() || sending) return;

    const userMessageText = messageText.trim();
    if (!overrideContent) setInputContent("");

    // 1. Render Optimistic User Message
    const tempUserMsg: ConversationMessageItem = {
      id: `user-${Date.now()}`,
      conversation_id: activeConvId,
      sender: "user",
      content: userMessageText,
      created_at: new Date().toISOString(),
    };

    // 2. Render Optimistic Assistant Placeholder for Real-Time Streaming
    const tempAsstId = `asst-stream-${Date.now()}`;
    const tempAsstMsg: ConversationMessageItem = {
      id: tempAsstId,
      conversation_id: activeConvId,
      sender: "assistant",
      content: "",
      created_at: new Date().toISOString(),
      metadata_json: { confidence_status: "grounded" },
    };

    setMessages((prev) => [...prev, tempUserMsg, tempAsstMsg]);
    setTimeout(scrollToBottom, 50);

    try {
      setSending(true);
      setError(null);

      // Try SSE Token Streaming
      await tutorService.streamMessage(
        selectedProjectId,
        activeConvId,
        userMessageText,
        mode,
        (metadata) => {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === tempAsstId
                ? {
                    ...msg,
                    citations: (metadata.citations as ConversationMessageItem["citations"]) || [],
                    metadata_json: {
                      ...(msg.metadata_json || {}),
                      confidence_status: String(metadata.confidence_status || "grounded"),
                      suggested_followups: (metadata.suggested_followups as string[]) || [],
                    },
                  }
                : msg
            )
          );
        },
        (token) => {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === tempAsstId ? { ...msg, content: msg.content + token } : msg
            )
          );
          scrollToBottom();
        },
        () => {
          fetchMessages();
        }
      );
    } catch (streamErr) {
      console.warn("SSE Streaming failed, falling back to REST sendMessage:", streamErr);
      try {
        await tutorService.sendMessage(selectedProjectId, activeConvId, userMessageText, mode);
        await fetchMessages();
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed to get AI Tutor response.");
      }
    } finally {
      setSending(false);
    }
  };

  return (

    <div className="h-[calc(100vh-6rem)] flex flex-col md:flex-row gap-6">
      {/* Sidebar - Projects & Conversations List */}
      <div className="w-full md:w-80 glass-panel border border-slate-800 rounded-2xl p-4 flex flex-col justify-between shrink-0">
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1">Target Study Project</label>
            <select
              value={selectedProjectId}
              onChange={(e) => setSelectedProjectId(e.target.value)}
              className="w-full px-3 py-2 bg-slate-950/80 border border-slate-800 rounded-xl text-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 font-medium"
            >
              {projects.map((pj) => (
                <option key={pj.id} value={pj.id}>
                  {pj.name}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center justify-between pt-2">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
              Conversations ({conversations.length})
            </span>
            <button
              onClick={handleCreateNewConv}
              className="p-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-medium flex items-center space-x-1 transition"
              title="New Chat Session"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>New</span>
            </button>
          </div>

          {/* Conversation Sessions List */}
          <div className="space-y-1.5 max-h-[calc(100vh-20rem)] overflow-y-auto pr-1">
            {loading ? (
              <div className="space-y-2 p-2">
                <div className="h-9 bg-slate-800/50 rounded-xl animate-pulse" />
                <div className="h-9 bg-slate-800/30 rounded-xl animate-pulse" />
              </div>
            ) : (
              conversations.map((c) => (
                <button
                  key={c.id}
                  onClick={() => setActiveConvId(c.id)}
                  className={`w-full p-3 rounded-xl text-left transition flex items-center space-x-3 ${
                    activeConvId === c.id
                      ? "bg-indigo-500/10 border border-indigo-500/30 text-slate-100"
                      : "text-slate-400 hover:bg-slate-800/40 hover:text-slate-200 border border-transparent"
                  }`}
                >
                  <MessageSquare className="w-4 h-4 text-indigo-400 shrink-0" />
                  <div className="truncate">
                    <p className="text-xs font-semibold truncate">{c.title}</p>
                    <p className="text-[10px] text-slate-500">{new Date(c.updated_at).toLocaleDateString()}</p>
                  </div>
                </button>
              ))
            )}
          </div>

        </div>

        <div className="pt-4 border-t border-slate-800 text-[11px] text-slate-500 flex items-center gap-1.5">
          <Bot className="w-3.5 h-3.5 text-emerald-400" />
          <span>Grounded RAG Evidence Enforcement Active</span>
        </div>
      </div>

      {/* Main Chat Panel */}
      <div className="flex-1 glass-panel border border-slate-800 rounded-2xl flex flex-col justify-between overflow-hidden relative">
        {/* Chat Header */}
        <div className="p-4 border-b border-slate-800 bg-slate-900/60 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-indigo-500/10 text-indigo-400 rounded-xl border border-indigo-500/20">
              <Bot className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                <span>{projects.find((p) => p.id === selectedProjectId)?.name || "RAG Fundamentals"} — AI Tutor</span>
                <span className="px-2 py-0.5 text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 rounded-full border border-emerald-500/20">
                  Grounded RAG
                </span>
              </h2>
              <p className="text-[11px] text-slate-400 mt-0.5">
                Current Conversation + Project Knowledge + Learning Context &rarr; Grounded Response
              </p>
            </div>
          </div>

          {/* Quick Action Mode Triggers */}
          <div className="hidden lg:flex items-center space-x-2">
            <button
              onClick={() => handleSendMessage("Explain the difference between semantic search and keyword search?", "default")}
              disabled={sending}
              className="px-3 py-1.5 text-xs font-semibold text-indigo-300 bg-indigo-500/10 hover:bg-indigo-500/20 border border-indigo-500/20 rounded-xl transition flex items-center space-x-1"
            >
              <BookOpen className="w-3.5 h-3.5" />
              <span>Semantic vs Keyword</span>
            </button>
            <button
              onClick={() => handleSendMessage("Give me a practical code or math example of vector search", "give_example")}
              disabled={sending}
              className="px-3 py-1.5 text-xs font-semibold text-emerald-300 bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/20 rounded-xl transition flex items-center space-x-1"
            >
              <FileCode className="w-3.5 h-3.5" />
              <span>Give Example</span>
            </button>
            <button
              onClick={() => handleSendMessage("Test me on reranking concepts", "test_me")}
              disabled={sending}
              className="px-3 py-1.5 text-xs font-semibold text-amber-300 bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/20 rounded-xl transition flex items-center space-x-1"
            >
              <HelpCircle className="w-3.5 h-3.5" />
              <span>Test Me</span>
            </button>
            <button
              onClick={openLearningContextModal}
              className="px-3 py-1.5 text-xs font-semibold text-sky-300 bg-sky-500/10 hover:bg-sky-500/20 border border-sky-500/20 rounded-xl transition flex items-center space-x-1"
            >
              <Sparkles className="w-3.5 h-3.5 text-sky-400" />
              <span>Learning Context</span>
            </button>
          </div>
        </div>

        {/* Message Stream View */}
        <div className="flex-1 p-6 overflow-y-auto space-y-6">
          {error && (
            <div className="p-3 bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm rounded-xl flex items-center justify-between">
              <span className="flex items-center space-x-2">
                <AlertTriangle className="w-4 h-4 shrink-0" />
                <span>{error}</span>
              </span>
              <button
                onClick={() => handleSendMessage()}
                className="text-xs font-bold underline hover:text-rose-300 flex items-center gap-1"
              >
                <RotateCcw className="w-3 h-3" /> Retry
              </button>
            </div>
          )}

          {messages.length === 0 ? (
            <div className="space-y-6">
              {/* Default Tutor Welcome Screen from Section 10 */}
              <div className="glass-panel p-6 rounded-2xl border border-slate-800 bg-slate-900/40 space-y-4 max-w-2xl">
                <div className="flex items-start space-x-3">
                  <div className="p-2.5 bg-indigo-500/10 text-indigo-400 rounded-xl border border-indigo-500/20 shrink-0">
                    <Bot className="w-5 h-5" />
                  </div>
                  <div className="space-y-2">
                    <h3 className="text-sm font-bold text-slate-100">🤖 AI Tutor</h3>
                    <p className="text-xs text-slate-300">
                      Ask me anything about this Project. Answers are strictly grounded in your project study materials.
                    </p>
                  </div>
                </div>

                {/* Sample Prompt Box */}
                <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800 space-y-3 text-xs">
                  <div>
                    <span className="font-semibold text-indigo-400">You:</span>
                    <p className="text-slate-200 mt-1">What is the difference between semantic search and keyword search?</p>
                  </div>

                  <div className="pt-3 border-t border-slate-800/80">
                    <span className="font-semibold text-emerald-400">Tutor:</span>
                    <p className="text-slate-300 mt-1 leading-relaxed">
                      Semantic search retrieves information based on meaning and vector embeddings, while keyword search relies primarily on exact token terms matching...
                    </p>
                  </div>

                  <div className="pt-2 border-t border-slate-800/80 space-y-1">
                    <span className="font-bold text-indigo-400 flex items-center gap-1">
                      📚 Sources
                    </span>
                    <div className="text-[11px] font-mono text-slate-300 bg-slate-900/80 p-2 rounded-lg border border-slate-800 space-y-1">
                      <div>&bull; RAG Notes — Page 14</div>
                      <div>&bull; Vector Database Notes — Page 7</div>
                    </div>
                  </div>
                </div>

                <button
                  onClick={() => handleSendMessage("What is the difference between semantic search and keyword search?")}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs rounded-xl transition shadow-lg shadow-indigo-600/20"
                >
                  Ask follow-up...
                </button>
              </div>
            </div>
          ) : (
            messages.map((m) => {
              const isUser = m.sender === "user";
              return (
                <div
                  key={m.id}
                  className={`flex items-start space-x-3 ${isUser ? "flex-row-reverse space-x-reverse" : ""}`}
                >
                  <div
                    className={`p-2.5 rounded-xl shrink-0 ${
                      isUser
                        ? "bg-indigo-600 text-white"
                        : "bg-slate-800 text-indigo-400 border border-slate-700"
                    }`}
                  >
                    {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                  </div>

                  <div className={`space-y-2 max-w-2xl ${isUser ? "items-end" : "items-start"}`}>
                    <div
                      className={`p-4 rounded-2xl text-sm leading-relaxed ${
                        isUser
                          ? "bg-indigo-600 text-white rounded-tr-none"
                          : "bg-slate-900 border border-slate-800 text-slate-100 rounded-tl-none shadow-lg"
                      }`}
                    >
                      <p className="whitespace-pre-wrap">
                        {m.content || (!isUser ? "Analyzing study materials..." : "")}
                      </p>
                    </div>

                    {/* Assistant Message Rendering */}
                    {!isUser && (
                      <div className="space-y-3">
                        {/* Confidence Status Badge */}
                        <div className="flex items-center gap-2">
                          <span
                            className={`px-2 py-0.5 text-[10px] font-semibold rounded-full border capitalize ${
                              (m.metadata_json?.confidence_status || "grounded") === "grounded"
                                ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                                : "bg-amber-500/10 text-amber-400 border-amber-500/20"
                            }`}
                          >
                            {(m.metadata_json?.confidence_status || "grounded") === "grounded"
                              ? "✓ Grounded in Study Material"
                              : "⚠️ Insufficient Evidence Disclaimer"}
                          </span>
                          {m.metadata_json?.latency_ms && (
                            <span className="text-[10px] text-slate-500 font-mono">
                              {m.metadata_json.latency_ms} ms • {m.metadata_json.model || "gemini"}
                            </span>
                          )}
                        </div>

                        {/* Citations Box for Assistant */}
                        {m.citations && m.citations.length > 0 && (
                          <div className="p-3 bg-slate-950/90 border border-slate-800 rounded-xl space-y-2 text-xs shadow-md">
                            <span className="font-bold text-indigo-400 flex items-center gap-1">
                              📚 Source Material Citations:
                            </span>
                            {m.citations.map((c, i) => {
                              const docTitle = String((c as Record<string, unknown>).file_name || (c as Record<string, unknown>).document_title || (c as Record<string, unknown>).material_name || "Project_Materials.pdf");
                              const pageNum = Number((c as Record<string, unknown>).page_number || (c as Record<string, unknown>).page || 1);
                              const excerptText = c.excerpt || "Course study notes context.";
                              const rawCitId = (c as Record<string, unknown>).citation_id;
                              const citTag = typeof rawCitId === "string" && rawCitId ? rawCitId : `[${i + 1}]`;

                              return (
                                <div key={i} className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 bg-slate-900/80 p-2.5 rounded-lg border border-slate-800 text-slate-200">
                                  <div className="font-semibold text-xs text-slate-200 font-mono flex items-center gap-2">
                                    <span className="px-1.5 py-0.5 bg-indigo-500/20 text-indigo-300 rounded text-[10px] font-bold">
                                      {citTag}
                                    </span>
                                    <span>{docTitle} — Page {pageNum}</span>
                                  </div>
                                  <button
                                    onClick={() =>
                                      setSourceModal({
                                        title: docTitle,
                                        page: pageNum,
                                        excerpt: excerptText,
                                      })
                                    }
                                    className="px-3 py-1 text-[11px] font-bold bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg transition shadow flex items-center gap-1 shrink-0"
                                  >
                                    <BookOpen className="w-3 h-3" />
                                    <span>View Excerpt</span>
                                  </button>
                                </div>
                              );
                            })}
                          </div>
                        )}

                        {/* Suggested Followups */}
                        {m.metadata_json?.suggested_followups && m.metadata_json.suggested_followups.length > 0 && (
                          <div className="flex flex-wrap gap-2 pt-1">
                            {m.metadata_json.suggested_followups.map((f, fi) => (
                              <button
                                key={fi}
                                onClick={() => handleSendMessage(f)}
                                disabled={sending}
                                className="px-2.5 py-1 text-[11px] font-medium bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white rounded-lg transition border border-slate-700"
                              >
                                &rarr; {f}
                              </button>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              );
            })
          )}

          {/* Typing Indicator */}
          {sending && (
            <div className="flex items-center space-x-3 animate-in fade-in duration-150">
              <div className="p-2.5 bg-slate-800 text-indigo-400 rounded-xl border border-slate-700">
                <Bot className="w-4 h-4 animate-spin" />
              </div>
              <div className="px-4 py-2 bg-slate-900 border border-slate-800 rounded-2xl text-xs text-slate-400 flex items-center space-x-2">
                <Sparkles className="w-3.5 h-3.5 text-indigo-400 animate-pulse" />
                <span>AI Tutor orchestrating grounded evidence context...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <div className="p-4 border-t border-slate-800 bg-slate-900/60 space-y-3">
          {/* Mode Selector Bar */}
          <div className="flex items-center gap-2 text-xs overflow-x-auto">
            <span className="text-slate-400 font-medium text-[11px] uppercase tracking-wider shrink-0">Mode:</span>
            {[
              { id: "default", label: "Default Tutor", icon: BookOpen },
              { id: "explain_simpler", label: "Explain Simpler", icon: Sparkles },
              { id: "give_example", label: "Give Example", icon: FileCode },
              { id: "test_me", label: "Test Me", icon: HelpCircle },
            ].map((m) => {
              const IconComp = m.icon;
              const isSelected = selectedMode === m.id;
              return (
                <button
                  key={m.id}
                  type="button"
                  onClick={() => setSelectedMode(m.id as typeof selectedMode)}
                  className={`px-3 py-1 rounded-lg text-xs font-semibold transition flex items-center gap-1.5 border shrink-0 ${
                    isSelected
                      ? "bg-indigo-500/20 text-indigo-300 border-indigo-500/40"
                      : "bg-slate-950/60 text-slate-400 hover:text-slate-200 border-slate-800"
                  }`}
                >
                  <IconComp className="w-3.5 h-3.5" />
                  <span>{m.label}</span>
                </button>
              );
            })}
          </div>

          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            className="flex items-center space-x-3"
          >
            <input
              type="text"
              value={inputContent}
              onChange={(e) => setInputContent(e.target.value)}
              placeholder={
                selectedMode === "explain_simpler"
                  ? "Ask for a beginner-friendly explanation..."
                  : selectedMode === "give_example"
                  ? "Request a practical code or math example..."
                  : selectedMode === "test_me"
                  ? "Ask to be tested on a concept..."
                  : "Ask a question grounded in your study project materials..."
              }
              disabled={sending || !selectedProjectId}
              className="flex-1 px-4 py-3 bg-slate-950/80 border border-slate-800 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
            />
            <button
              type="submit"
              disabled={sending || !inputContent.trim()}
              className="px-5 py-3 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm rounded-xl transition shadow-lg shadow-indigo-600/20 disabled:opacity-50 flex items-center space-x-2 shrink-0"
            >
              <Send className="w-4 h-4" />
              <span>Send</span>
            </button>
          </form>
        </div>
      </div>

      {/* Section 11: Source Material Document Preview Modal */}
      {sourceModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl p-6 max-w-xl w-full shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center space-x-2 text-indigo-400 font-bold">
                <BookOpen className="w-5 h-5" />
                <span>Source Material Preview</span>
              </div>
              <button
                onClick={() => setSourceModal(null)}
                className="px-2.5 py-1 text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition"
              >
                Close ✕
              </button>
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between text-xs text-slate-400 bg-slate-950/60 p-3 rounded-xl border border-slate-800 font-mono">
                <div>
                  Document: <strong className="text-slate-100">{sourceModal.title}</strong>
                </div>
                <div className="px-2 py-0.5 bg-indigo-500/20 text-indigo-300 rounded border border-indigo-500/30">
                  Page {sourceModal.page}
                </div>
              </div>

              <div className="p-4 bg-slate-950/90 rounded-xl border border-slate-800 text-xs text-slate-200 leading-relaxed font-mono whitespace-pre-wrap max-h-60 overflow-y-auto">
                {sourceModal.excerpt}
              </div>
            </div>

            <div className="pt-2 flex justify-end">
              <button
                onClick={() => setSourceModal(null)}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs rounded-xl transition"
              >
                Return to AI Tutor
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Section 20: Persistent Student Learning Context Modal */}
      {showLearningContext && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl p-6 max-w-lg w-full shadow-2xl space-y-5">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center space-x-2 text-indigo-400 font-bold">
                <Sparkles className="w-5 h-5 text-indigo-400" />
                <span>Persistent Learning Context</span>
              </div>
              <button
                onClick={() => setShowLearningContext(false)}
                className="px-2.5 py-1 text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition"
              >
                Close ✕
              </button>
            </div>

            <div className="space-y-4 text-xs font-mono text-slate-200">
              {learningContextText ? (
                <div className="p-4 bg-slate-950/90 rounded-xl border border-slate-800 text-slate-200 leading-relaxed font-mono whitespace-pre-wrap max-h-80 overflow-y-auto">
                  {learningContextText}
                </div>
              ) : (
                <div className="p-4 bg-slate-950/50 rounded-xl border border-slate-800 text-slate-400 text-center animate-pulse">
                  Loading persistent learner context...
                </div>
              )}
            </div>

            <div className="pt-2 flex justify-end">
              <button
                onClick={() => setShowLearningContext(false)}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs rounded-xl transition"
              >
                Close Context
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
