import React, { useEffect, useState } from 'react';
import { adminService, AdminProject } from '../../services/adminService';
import { FolderKanban, Search, BookOpen, BrainCircuit } from 'lucide-react';

export const AdminProjectsPage: React.FC = () => {
  const [projects, setProjects] = useState<AdminProject[]>([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchProjects = async () => {
      setLoading(true);
      try {
        const data = await adminService.getProjects(search);
        setProjects(data);
      } catch (err) {
        console.error('Failed to fetch projects:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchProjects();
  }, [search]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Project Governance</h1>
          <p className="text-sm text-slate-400">Inspect project containers, material indexing status, and mapped concept nodes.</p>
        </div>

        <div className="relative w-full sm:w-72">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search project title..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-lg border border-slate-800 bg-slate-900/60 py-2 pl-9 pr-4 text-xs text-white placeholder-slate-500 focus:border-indigo-500 focus:outline-none"
          />
        </div>
      </div>

      {loading ? (
        <div className="flex h-48 items-center justify-center">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-500 border-t-transparent" />
        </div>
      ) : projects.length === 0 ? (
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-12 text-center">
          <FolderKanban className="mx-auto h-10 w-10 text-slate-600" />
          <h3 className="mt-3 text-sm font-semibold text-slate-300">No Projects Found</h3>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {projects.map((pj) => (
            <div key={pj.id} className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur-md">
              <span className="rounded-md bg-indigo-500/20 px-2 py-0.5 text-[10px] font-semibold text-indigo-300 border border-indigo-500/30">
                Space: {pj.space_name}
              </span>
              <h3 className="mt-3 text-base font-bold text-white">{pj.title}</h3>

              <div className="mt-4 flex items-center justify-between border-t border-slate-800/80 pt-3 text-xs text-slate-400">
                <span className="flex items-center gap-1">
                  <BookOpen className="h-3.5 w-3.5 text-blue-400" />
                  {pj.material_count} Materials
                </span>
                <span className="flex items-center gap-1">
                  <BrainCircuit className="h-3.5 w-3.5 text-purple-400" />
                  {pj.concept_count} Concepts
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
