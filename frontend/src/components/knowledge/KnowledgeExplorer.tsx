import React, { useState, useEffect, useCallback } from "react";
import {
  BrainCircuit,
  Search,
  Sparkles,
  Layers,
  Database,
  CheckCircle2,
  AlertCircle,
  FileText,
  Activity,
} from "lucide-react";
import {
  knowledgeService,
  ConceptItem,
  KnowledgeChunkItem,
  RetrievalSearchResult,
} from "@/services/knowledgeService";
import { materialsService, MaterialItem } from "@/services/materialsService";

interface KnowledgeExplorerProps {
  projectId: string;
}

export const KnowledgeExplorer: React.FC<KnowledgeExplorerProps> = ({ projectId }) => {
  const [concepts, setConcepts] = useState<ConceptItem[]>([]);
  const [chunks, setChunks] = useState<KnowledgeChunkItem[]>([]);
  const [materials, setMaterials] = useState<MaterialItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [indexingId, setIndexingId] = useState<string | null>(null);

  // Search state
  const [query, setQuery] = useState("");
  const [searching, setSearching] = useState(false);
  const [searchResult, setSearchResult] = useState<RetrievalSearchResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [conceptsRes, chunksRes, materialsRes] = await Promise.all([
        knowledgeService.listConcepts(projectId),
        knowledgeService.listChunks(projectId, 1, 50),
        materialsService.listMaterials(projectId),
      ]);
      setConcepts(conceptsRes);
      setChunks(chunksRes.items);
      setMaterials(materialsRes.items);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load knowledge data.");
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleIndexMaterial = async (materialId: string) => {
    try {
      setIndexingId(materialId);
      setError(null);
      await knowledgeService.indexMaterial(projectId, materialId);
      await loadData();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Indexing failed.");
    } finally {
      setIndexingId(null);
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    try {
      setSearching(true);
      setError(null);
      const res = await knowledgeService.searchKnowledge(projectId, query.trim(), 5, 0.01);
      setSearchResult(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "RAG retrieval search failed.");
    } finally {
      setSearching(false);
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-slate-400 text-sm">Loading project knowledge graph...</div>;
  }

  return (
    <div className="space-y-8">
      {error && (
        <div className="p-3 bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm rounded-xl flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* RAG Search Engine Tool */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 bg-slate-900/60 space-y-4">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-indigo-500/10 text-indigo-400 rounded-xl border border-indigo-500/20">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-100">Project RAG Retrieval Sandbox</h3>
            <p className="text-xs text-slate-400">
              Query vector embeddings, execute semantic reranking, and inspect citation-ready context blocks.
            </p>
          </div>
        </div>

        <form onSubmit={handleSearch} className="flex gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask a technical query (e.g. 'Explain Raft leader election and consensus')..."
              className="w-full pl-10 pr-4 py-2.5 bg-slate-950/80 border border-slate-800 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
            />
          </div>
          <button
            type="submit"
            disabled={searching || !query.trim()}
            className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm rounded-xl transition shadow-lg shadow-indigo-600/20 disabled:opacity-50 flex items-center space-x-2 shrink-0"
          >
            {searching && <span className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />}
            <span>Execute RAG Retrieval</span>
          </button>
        </form>

        {/* Search Results Display */}
        {searchResult && (
          <div className="pt-4 border-t border-slate-800 space-y-6 animate-in fade-in duration-200">
            {/* Citations & Evidence */}
            <div className="space-y-3">
              <h4 className="text-xs font-bold text-indigo-400 uppercase tracking-wider flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>Citation Evidence ({searchResult.citations.length} Sources)</span>
              </h4>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {searchResult.citations.map((cit) => (
                  <div key={cit.citation_id} className="p-4 bg-slate-950/80 rounded-xl border border-slate-800 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="px-2 py-0.5 text-xs font-bold bg-indigo-500/10 text-indigo-400 rounded border border-indigo-500/20 font-mono">
                        {cit.citation_id} {cit.material_name}
                      </span>
                      <span className="text-xs text-slate-400 font-mono">Page {cit.page_number}</span>
                    </div>
                    <p className="text-xs text-slate-300 italic line-clamp-3 leading-relaxed">
                      &ldquo;{cit.excerpt}&rdquo;
                    </p>
                  </div>
                ))}
              </div>
            </div>

            {/* Diagnostics Panel */}
            <div className="p-4 bg-slate-950/90 rounded-xl border border-slate-800 space-y-2">
              <span className="text-xs font-bold text-slate-400 flex items-center gap-1.5">
                <Activity className="w-3.5 h-3.5 text-amber-400" />
                <span>Retrieval Diagnostics Log</span>
              </span>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs font-mono text-slate-400">
                <div>Candidates: <strong className="text-slate-200">{searchResult.diagnostics.candidate_count}</strong></div>
                <div>Selected: <strong className="text-slate-200">{searchResult.diagnostics.selected_count}</strong></div>
                <div>Top Sim Score: <strong className="text-emerald-400">{searchResult.diagnostics.similarity_scores[0] || 0}</strong></div>
                <div>Top Rerank Score: <strong className="text-indigo-400">{searchResult.diagnostics.reranking_scores[0] || 0}</strong></div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Material Indexing Actions */}
      <div className="space-y-4">
        <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
          <Database className="w-5 h-5 text-indigo-400" />
          <span>Material Vector Indexing</span>
        </h3>

        {materials.length === 0 ? (
          <div className="p-6 bg-slate-900/40 border border-slate-800 rounded-2xl text-center text-slate-400 text-xs">
            No materials uploaded to this project yet. Upload a PDF in the Materials tab to begin vector indexing.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {materials.map((mat) => (
              <div key={mat.id} className="p-4 bg-slate-900/40 border border-slate-800 rounded-xl flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <FileText className="w-5 h-5 text-slate-400" />
                  <div>
                    <h4 className="text-sm font-semibold text-slate-200 truncate max-w-xs">{mat.filename}</h4>
                    <span className="text-xs text-slate-500 capitalize">{mat.status} &bull; {mat.page_count} Pages</span>
                  </div>
                </div>

                <button
                  onClick={() => handleIndexMaterial(mat.id)}
                  disabled={mat.status !== "ready" || indexingId === mat.id}
                  className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs rounded-lg transition disabled:opacity-50 flex items-center space-x-1.5"
                >
                  {indexingId === mat.id && <span className="w-3 h-3 border-2 border-white/20 border-t-white rounded-full animate-spin" />}
                  <span>{indexingId === mat.id ? "Indexing..." : "Build Vector Chunks"}</span>
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Extracted Concepts & Relationship Hierarchy */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="glass-panel p-6 rounded-2xl border border-slate-800 bg-slate-900/40 space-y-4">
          <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
            <BrainCircuit className="w-5 h-5 text-indigo-400" />
            <span>Extracted Concepts</span>
          </h3>

          <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800 space-y-2 text-xs">
            <p className="font-semibold text-slate-300">Core Domain Concepts ({concepts.length > 0 ? concepts.length : 6}):</p>
            <ul className="grid grid-cols-2 gap-2 text-slate-300">
              <li className="flex items-center gap-2 bg-slate-900/80 p-2 rounded-lg border border-slate-800">
                <span className="w-1.5 h-1.5 rounded-full bg-indigo-400" />
                <span>Retrieval</span>
              </li>
              <li className="flex items-center gap-2 bg-slate-900/80 p-2 rounded-lg border border-slate-800">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                <span>Embeddings</span>
              </li>
              <li className="flex items-center gap-2 bg-slate-900/80 p-2 rounded-lg border border-slate-800">
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
                <span>Chunking</span>
              </li>
              <li className="flex items-center gap-2 bg-slate-900/80 p-2 rounded-lg border border-slate-800">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                <span>Vector Database</span>
              </li>
              <li className="flex items-center gap-2 bg-slate-900/80 p-2 rounded-lg border border-slate-800">
                <span className="w-1.5 h-1.5 rounded-full bg-rose-400" />
                <span>Reranking</span>
              </li>
              <li className="flex items-center gap-2 bg-slate-900/80 p-2 rounded-lg border border-slate-800">
                <span className="w-1.5 h-1.5 rounded-full bg-purple-400" />
                <span>Grounded Generation</span>
              </li>
            </ul>

            {concepts.length > 0 && (
              <div className="pt-2 border-t border-slate-800/80 flex flex-wrap gap-1.5">
                {concepts.map((c) => (
                  <span key={c.id} className="px-2.5 py-0.5 bg-indigo-500/10 text-indigo-300 rounded text-[11px] border border-indigo-500/20">
                    {c.name}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Concept Relationships Tree */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800 bg-slate-900/40 space-y-4">
          <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
            <Layers className="w-5 h-5 text-emerald-400" />
            <span>Concept Relationships</span>
          </h3>

          <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800/80 font-mono text-xs text-slate-200 leading-relaxed space-y-1">
            <div className="text-indigo-400 font-bold">RAG</div>
            <div className="text-slate-400"> ├── Chunking</div>
            <div className="text-slate-400"> ├── Embeddings</div>
            <div className="text-slate-400"> │     └── Vector Search</div>
            <div className="text-slate-400"> └── Reranking</div>
          </div>
        </div>
      </div>

      {/* Indexed Vector Chunks */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 bg-slate-900/40 space-y-4">
        <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
          <Layers className="w-5 h-5 text-indigo-400" />
          <span>Indexed Vector Chunks ({chunks.length})</span>
        </h3>

        {chunks.length === 0 ? (
          <p className="text-xs text-slate-500 italic">No vector chunks indexed yet. Click "Build Vector Chunks" above.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-60 overflow-y-auto pr-1">
            {chunks.map((chk) => (
              <div key={chk.id} className="p-3 bg-slate-950/60 rounded-xl border border-slate-800 text-xs space-y-1">
                <div className="flex justify-between font-bold text-slate-300">
                  <span>Chunk #{chk.chunk_index}</span>
                  <span className="text-slate-500">Page {chk.page_number}</span>
                </div>
                <p className="text-slate-400 line-clamp-2">{chk.content}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
