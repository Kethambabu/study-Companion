import React, { useEffect, useState } from 'react';
import { adminService, AdminUser, UserLearningJourney } from '../../services/adminService';
import { Search, Shield, UserCheck, Filter, X, ChevronRight, BookOpen, Brain, Activity } from 'lucide-react';

export const AdminUsersPage: React.FC = () => {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState<'All' | 'Student' | 'Admin'>('All');
  const [loading, setLoading] = useState(true);

  // Section 23 Student Inspection State
  const [selectedUser, setSelectedUser] = useState<AdminUser | null>(null);
  const [journey, setJourney] = useState<UserLearningJourney | null>(null);
  const [journeyLoading, setJourneyLoading] = useState(false);

  useEffect(() => {
    const fetchUsers = async () => {
      setLoading(true);
      try {
        const data = await adminService.getUsers(search);
        setUsers(data);
      } catch (err) {
        console.error('Failed to fetch admin users:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchUsers();
  }, [search]);

  const handleInspectUser = async (user: AdminUser) => {
    setSelectedUser(user);
    setJourneyLoading(true);
    try {
      const data = await adminService.getUserJourney(user.id);
      setJourney(data);
    } catch (err) {
      console.error('Failed to load user journey:', err);
    } finally {
      setJourneyLoading(false);
    }
  };

  const filteredUsers = users.filter((u) => {
    if (roleFilter === 'Student') return !u.is_admin;
    if (roleFilter === 'Admin') return u.is_admin;
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Header & Controls */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Users</h1>
          <p className="text-xs text-slate-400">Inspect registered platform users, roles, and individual learning journeys.</p>
        </div>

        {/* PRD Section 22 Search users... + [Filter] */}
        <div className="flex items-center gap-3">
          <div className="relative w-full sm:w-64">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search users..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full rounded-lg border border-slate-800 bg-slate-900/60 py-2 pl-9 pr-4 text-xs text-white placeholder-slate-500 focus:border-indigo-500 focus:outline-none"
            />
          </div>

          <div className="flex items-center gap-1.5 bg-slate-900/60 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-300">
            <Filter className="h-3.5 w-3.5 text-slate-400" />
            <select
              value={roleFilter}
              onChange={(e) => setRoleFilter(e.target.value as 'All' | 'Student' | 'Admin')}
              className="bg-transparent border-none text-xs text-slate-200 focus:outline-none cursor-pointer"
            >
              <option value="All" className="bg-slate-900">All Roles</option>
              <option value="Student" className="bg-slate-900">Student</option>
              <option value="Admin" className="bg-slate-900">Admin</option>
            </select>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="flex h-48 items-center justify-center">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-500 border-t-transparent" />
        </div>
      ) : filteredUsers.length === 0 ? (
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-12 text-center">
          <UserCheck className="mx-auto h-10 w-10 text-slate-600" />
          <h3 className="mt-3 text-sm font-semibold text-slate-300">No Users Found</h3>
          <p className="mt-1 text-xs text-slate-500">No user accounts match your search filter.</p>
        </div>
      ) : (
        /* PRD Section 22 User Table */
        <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900/60 backdrop-blur-md">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="border-b border-slate-800 bg-slate-900/80 uppercase text-slate-400 font-semibold">
              <tr>
                <th className="px-6 py-3.5">User</th>
                <th className="px-6 py-3.5">Role</th>
                <th className="px-6 py-3.5">Projects</th>
                <th className="px-6 py-3.5">Last Active</th>
                <th className="px-6 py-3.5 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {filteredUsers.map((u) => (
                <tr
                  key={u.id}
                  onClick={() => handleInspectUser(u)}
                  className="hover:bg-slate-800/40 cursor-pointer transition-colors"
                >
                  <td className="px-6 py-4">
                    <p className="font-semibold text-white">{u.full_name || u.email.split('@')[0]}</p>
                    <p className="text-[11px] text-slate-400">{u.email}</p>
                  </td>
                  <td className="px-6 py-4">
                    {u.is_admin ? (
                      <span className="inline-flex items-center gap-1 rounded-md bg-purple-500/20 px-2.5 py-1 text-[11px] font-semibold text-purple-300 border border-purple-500/30">
                        <Shield className="h-3 w-3" /> Admin
                      </span>
                    ) : (
                      <span className="inline-flex items-center rounded-md bg-indigo-500/20 px-2.5 py-1 text-[11px] font-semibold text-indigo-300 border border-indigo-500/30">
                        Student
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 font-semibold text-slate-200">{u.projects_count ?? 0}</td>
                  <td className="px-6 py-4 text-slate-400">{u.last_active ?? 'Never'}</td>
                  <td className="px-6 py-4 text-right">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleInspectUser(u);
                      }}
                      className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-400 hover:text-indigo-300 hover:underline"
                    >
                      <span>Inspect</span>
                      <ChevronRight className="h-3.5 w-3.5" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* PRD Section 23 Student Inspection Drawer */}
      {selectedUser && (
        <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-xs">
          <div className="w-full max-w-xl bg-slate-900 border-l border-slate-800 h-full overflow-y-auto p-6 space-y-6 shadow-2xl">
            {/* Header */}
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <h2 className="text-xl font-bold text-white">{selectedUser.full_name || selectedUser.email.split('@')[0]}</h2>
                <p className="text-xs text-slate-400">{selectedUser.email} • Learning Journey</p>
              </div>
              <button
                onClick={() => setSelectedUser(null)}
                className="rounded-lg p-1 text-slate-400 hover:bg-slate-800 hover:text-white"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {journeyLoading ? (
              <div className="flex h-64 items-center justify-center">
                <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-500 border-t-transparent" />
              </div>
            ) : journey ? (
              <div className="space-y-6 text-xs text-slate-300">
                {/* Overview Section */}
                <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-5 space-y-4">
                  <h3 className="font-bold text-white uppercase tracking-wider text-[11px] text-indigo-400">Overview</h3>
                  <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
                    <div className="rounded-lg bg-slate-900 p-3 border border-slate-800">
                      <span className="text-[11px] text-slate-400">Projects</span>
                      <p className="text-lg font-bold text-white mt-0.5">{journey.total_projects}</p>
                    </div>
                    <div className="rounded-lg bg-slate-900 p-3 border border-slate-800">
                      <span className="text-[11px] text-slate-400">Active</span>
                      <p className="text-lg font-bold text-indigo-400 mt-0.5">{journey.active_projects}</p>
                    </div>
                    <div className="rounded-lg bg-slate-900 p-3 border border-slate-800">
                      <span className="text-[11px] text-slate-400">Assessments</span>
                      <p className="text-lg font-bold text-purple-400 mt-0.5">{journey.assessments_count}</p>
                    </div>
                    <div className="rounded-lg bg-slate-900 p-3 border border-slate-800">
                      <span className="text-[11px] text-slate-400">Quiz Attempts</span>
                      <p className="text-lg font-bold text-blue-400 mt-0.5">{journey.quiz_attempts_count}</p>
                    </div>
                    <div className="rounded-lg bg-slate-900 p-3 border border-slate-800 col-span-2 sm:col-span-2">
                      <span className="text-[11px] text-slate-400">Tutor Chats</span>
                      <p className="text-lg font-bold text-emerald-400 mt-0.5">{journey.tutor_chats_count}</p>
                    </div>
                  </div>

                  {/* Overall Progress Bar */}
                  <div className="mt-4 border-t border-slate-800/80 pt-4 space-y-2">
                    <div className="flex justify-between items-center font-bold">
                      <span className="text-slate-300">Overall Progress</span>
                      <span className="text-indigo-400">{journey.overall_progress}%</span>
                    </div>
                    <div className="h-3 w-full bg-slate-800 rounded-full overflow-hidden p-0.5 border border-slate-700/50">
                      <div
                        className="h-full bg-gradient-to-r from-indigo-500 to-emerald-400 rounded-full transition-all duration-500"
                        style={{ width: `${journey.overall_progress}%` }}
                      />
                    </div>
                  </div>
                </div>

                {/* Projects Breakdown */}
                <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-5 space-y-3">
                  <h3 className="font-bold text-white uppercase tracking-wider text-[11px] text-indigo-400 flex items-center gap-1.5">
                    <BookOpen className="h-3.5 w-3.5" /> Projects
                  </h3>
                  {journey.projects.length === 0 ? (
                    <p className="text-xs text-slate-500 py-2">No projects created yet for this user.</p>
                  ) : (
                    <div className="space-y-3">
                      {journey.projects.map((proj) => (
                        <div key={proj.id} className="space-y-1.5">
                          <div className="flex justify-between text-xs font-semibold">
                            <span className="text-slate-200">{proj.title}</span>
                            <span className="text-indigo-400 font-bold">{proj.progress_percentage}%</span>
                          </div>
                          <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-indigo-500 rounded-full"
                              style={{ width: `${proj.progress_percentage}%` }}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Recent Activity Feed */}
                <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-5 space-y-3">
                  <h3 className="font-bold text-white uppercase tracking-wider text-[11px] text-indigo-400 flex items-center gap-1.5">
                    <Activity className="h-3.5 w-3.5" /> Recent Activity
                  </h3>
                  {journey.recent_activity.length === 0 ? (
                    <p className="text-xs text-slate-500 py-2">No learning activity recorded yet.</p>
                  ) : (
                    <ul className="space-y-2.5">
                      {journey.recent_activity.map((act) => (
                        <li key={act.id} className="flex items-start gap-2 text-xs">
                          <span className="text-indigo-400 font-bold">•</span>
                          <div className="flex-1">
                            <span className="font-semibold text-white">{act.activity}</span>
                            <span className="text-slate-400 ml-1">in {act.project_title}</span>
                          </div>
                          <span className="text-[10px] text-slate-500">{act.timestamp}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>

                {/* AI Usage */}
                <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-5 space-y-3">
                  <h3 className="font-bold text-white uppercase tracking-wider text-[11px] text-indigo-400 flex items-center gap-1.5">
                    <Brain className="h-3.5 w-3.5" /> AI Usage
                  </h3>
                  <div className="grid grid-cols-3 gap-2 text-center">
                    <div className="p-3 bg-slate-900 border border-slate-800 rounded-lg">
                      <span className="text-[10px] text-slate-400 block">Tutor Requests</span>
                      <span className="text-base font-bold text-indigo-300">{journey.tutor_requests}</span>
                    </div>
                    <div className="p-3 bg-slate-900 border border-slate-800 rounded-lg">
                      <span className="text-[10px] text-slate-400 block">Quiz Generations</span>
                      <span className="text-base font-bold text-purple-300">{journey.quiz_generations}</span>
                    </div>
                    <div className="p-3 bg-slate-900 border border-slate-800 rounded-lg">
                      <span className="text-[10px] text-slate-400 block">AI Evaluation</span>
                      <span className="text-base font-bold text-emerald-300">{journey.ai_evaluations}</span>
                    </div>
                  </div>
                </div>
              </div>
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
};

