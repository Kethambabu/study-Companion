import React, { useEffect, useState } from 'react';
import { adminService, AdminSpace } from '../../services/adminService';
import { Layers, Search } from 'lucide-react';

export const AdminSpacesPage: React.FC = () => {
  const [spaces, setSpaces] = useState<AdminSpace[]>([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSpaces = async () => {
      setLoading(true);
      try {
        const data = await adminService.getSpaces(search);
        setSpaces(data);
      } catch (err) {
        console.error('Failed to fetch spaces:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchSpaces();
  }, [search]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Tenant Space Management</h1>
          <p className="text-sm text-slate-400">Inspect multi-tenant organization containers, ownership, and project counts.</p>
        </div>

        <div className="relative w-full sm:w-72">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search space name or slug..."
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
      ) : spaces.length === 0 ? (
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-12 text-center">
          <Layers className="mx-auto h-10 w-10 text-slate-600" />
          <h3 className="mt-3 text-sm font-semibold text-slate-300">No Spaces Found</h3>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {spaces.map((sp) => (
            <div key={sp.id} className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur-md">
              <div className="flex items-center justify-between">
                <span className="rounded-md bg-purple-500/20 px-2 py-0.5 text-[10px] font-semibold text-purple-300 border border-purple-500/30">
                  slug: {sp.slug}
                </span>
                <span className="text-[11px] text-slate-400">{sp.member_count} Members</span>
              </div>
              <h3 className="mt-3 text-base font-bold text-white">{sp.name}</h3>
              <p className="mt-1 text-xs text-slate-400">Owner: {sp.owner_email}</p>
              <div className="mt-4 flex items-center justify-between border-t border-slate-800/80 pt-3 text-xs text-slate-400">
                <span>Projects: <strong className="text-white">{sp.project_count}</strong></span>
                <span>Created {new Date(sp.created_at).toLocaleDateString()}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
