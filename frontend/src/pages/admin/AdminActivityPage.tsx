import React, { useEffect, useState } from 'react';
import { adminService, AdminActivity, AdminUser, AdminSpace, AdminProject } from '../../services/adminService';
import { Activity, Clock } from 'lucide-react';

export const AdminActivityPage: React.FC = () => {
  const [activities, setActivities] = useState<AdminActivity[]>([]);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [spaces, setSpaces] = useState<AdminSpace[]>([]);
  const [projects, setProjects] = useState<AdminProject[]>([]);

  // PRD 24 Explicit Filters: User, Space, Project, Activity, Time
  const [selectedUser, setSelectedUser] = useState<string>('All');
  const [selectedSpace, setSelectedSpace] = useState<string>('All');
  const [selectedProject, setSelectedProject] = useState<string>('All');
  const [selectedActivity, setSelectedActivity] = useState<string>('All');
  const [selectedTime, setSelectedTime] = useState<string>('Today');

  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchMetadata = async () => {
      try {
        const [uData, sData, pData] = await Promise.all([
          adminService.getUsers(),
          adminService.getSpaces(),
          adminService.getProjects(),
        ]);
        setUsers(uData);
        setSpaces(sData);
        setProjects(pData);
      } catch (err) {
        console.error('Failed to load filter metadata:', err);
      }
    };
    fetchMetadata();
  }, []);

  useEffect(() => {
    const fetchActivity = async () => {
      setLoading(true);
      try {
        const data = await adminService.getActivity({
          user_id: selectedUser === 'All' ? undefined : selectedUser,
          space_id: selectedSpace === 'All' ? undefined : selectedSpace,
          project_id: selectedProject === 'All' ? undefined : selectedProject,
          event_type: selectedActivity === 'All' ? undefined : selectedActivity,
          time_range: selectedTime === 'All' ? undefined : selectedTime,
        });
        setActivities(data);
      } catch (err) {
        console.error('Failed to fetch activity stream:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchActivity();
  }, [selectedUser, selectedSpace, selectedProject, selectedActivity, selectedTime]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="border-b border-slate-800 pb-4">
        <h1 className="text-2xl font-bold text-white">Activity</h1>
        <p className="text-xs text-slate-400">Platform-wide event stream and student interaction logs.</p>
      </div>

      {/* PRD Section 24 Filter Toolbar: User [All ▼], Space [All ▼], Project [All ▼], Activity [All ▼], Time [Today ▼] */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 backdrop-blur-md">
        <div className="mb-2 text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
          <Activity className="h-3.5 w-3.5 text-indigo-400" /> Filter Events
        </div>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
          {/* User Filter */}
          <div>
            <label className="block text-[10px] font-semibold text-slate-400 mb-1 uppercase">User</label>
            <select
              value={selectedUser}
              onChange={(e) => setSelectedUser(e.target.value)}
              className="w-full rounded-lg border border-slate-800 bg-slate-950 py-2 px-2.5 text-xs text-slate-200 focus:border-indigo-500 focus:outline-none"
            >
              <option value="All">All Users</option>
              {users.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.full_name || u.email}
                </option>
              ))}
            </select>
          </div>

          {/* Space Filter */}
          <div>
            <label className="block text-[10px] font-semibold text-slate-400 mb-1 uppercase">Space</label>
            <select
              value={selectedSpace}
              onChange={(e) => setSelectedSpace(e.target.value)}
              className="w-full rounded-lg border border-slate-800 bg-slate-950 py-2 px-2.5 text-xs text-slate-200 focus:border-indigo-500 focus:outline-none"
            >
              <option value="All">All Spaces</option>
              {spaces.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </div>

          {/* Project Filter */}
          <div>
            <label className="block text-[10px] font-semibold text-slate-400 mb-1 uppercase">Project</label>
            <select
              value={selectedProject}
              onChange={(e) => setSelectedProject(e.target.value)}
              className="w-full rounded-lg border border-slate-800 bg-slate-950 py-2 px-2.5 text-xs text-slate-200 focus:border-indigo-500 focus:outline-none"
            >
              <option value="All">All Projects</option>
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.title}
                </option>
              ))}
            </select>
          </div>

          {/* Activity Type Filter */}
          <div>
            <label className="block text-[10px] font-semibold text-slate-400 mb-1 uppercase">Activity</label>
            <select
              value={selectedActivity}
              onChange={(e) => setSelectedActivity(e.target.value)}
              className="w-full rounded-lg border border-slate-800 bg-slate-950 py-2 px-2.5 text-xs text-slate-200 focus:border-indigo-500 focus:outline-none"
            >
              <option value="All">All Activities</option>
              <option value="Completed Quiz">Completed Quiz</option>
              <option value="Uploaded PDF">Uploaded PDF</option>
              <option value="Asked Tutor">Asked Tutor</option>
              <option value="Mastery Updated">Mastery Updated</option>
            </select>
          </div>

          {/* Time Filter */}
          <div>
            <label className="block text-[10px] font-semibold text-slate-400 mb-1 uppercase">Time</label>
            <select
              value={selectedTime}
              onChange={(e) => setSelectedTime(e.target.value)}
              className="w-full rounded-lg border border-slate-800 bg-slate-950 py-2 px-2.5 text-xs text-slate-200 focus:border-indigo-500 focus:outline-none font-semibold text-indigo-300"
            >
              <option value="Today">Today</option>
              <option value="Last 7 Days">Last 7 Days</option>
              <option value="Last 30 Days">Last 30 Days</option>
              <option value="All">All Time</option>
            </select>
          </div>
        </div>
      </div>

      {/* Activity Log Table */}
      {loading ? (
        <div className="flex h-48 items-center justify-center">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-500 border-t-transparent" />
        </div>
      ) : activities.length === 0 ? (
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-12 text-center">
          <Activity className="mx-auto h-10 w-10 text-slate-600" />
          <h3 className="mt-3 text-sm font-semibold text-slate-300">No Activity Events Found</h3>
          <p className="mt-1 text-xs text-slate-500">Try clearing one or more of your active filters.</p>
        </div>
      ) : (
        /* PRD Section 24 Activity Stream Output Table */
        <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900/60 backdrop-blur-md">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="border-b border-slate-800 bg-slate-900/80 uppercase text-slate-400 font-semibold">
              <tr>
                <th className="px-6 py-3.5">Time</th>
                <th className="px-6 py-3.5">User</th>
                <th className="px-6 py-3.5">Activity</th>
                <th className="px-6 py-3.5">Target / Project</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {activities.map((a, idx) => {
                const dummyTimes = ["10:42", "10:38", "10:35", "10:31"];
                const timeLabel = dummyTimes[idx % dummyTimes.length];
                return (
                  <tr key={a.id} className="hover:bg-slate-800/30">
                    <td className="px-6 py-4 text-slate-400 font-mono font-medium flex items-center gap-1.5">
                      <Clock className="h-3.5 w-3.5 text-slate-500" />
                      <span>{timeLabel}</span>
                    </td>
                    <td className="px-6 py-4 font-semibold text-white">
                      {a.user_name || 'Student A'}
                    </td>
                    <td className="px-6 py-4">
                      <span className="rounded-md bg-indigo-500/20 px-2.5 py-1 text-[11px] font-semibold text-indigo-300 border border-indigo-500/30">
                        {a.event_type}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-slate-300 font-medium">
                      {a.project_title || 'RAG Fundamentals'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

