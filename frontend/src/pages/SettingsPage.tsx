import React from "react";
import { Shield, Database, Cpu } from "lucide-react";

export const SettingsPage: React.FC = () => {
  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-foreground">Settings</h2>
        <p className="text-sm text-muted-foreground mt-1">
          System configuration, security boundaries, and provider abstractions.
        </p>
      </div>

      <div className="space-y-4">
        <div className="glass-panel p-6 rounded-xl flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-primary/10 text-primary rounded-lg">
              <Cpu className="h-5 w-5" />
            </div>
            <div>
              <h3 className="font-semibold text-foreground">AI Provider Abstraction</h3>
              <p className="text-xs text-muted-foreground">Default: OpenAI (GPT-4o / Text-Embedding-3)</p>
            </div>
          </div>
          <span className="px-3 py-1 bg-emerald-500/10 text-emerald-400 text-xs font-semibold rounded-full border border-emerald-500/20">
            Active
          </span>
        </div>

        <div className="glass-panel p-6 rounded-xl flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-blue-500/10 text-blue-400 rounded-lg">
              <Database className="h-5 w-5" />
            </div>
            <div>
              <h3 className="font-semibold text-foreground">Vector Storage Engine</h3>
              <p className="text-xs text-muted-foreground">Default: Supabase Pgvector (Modular Interface)</p>
            </div>
          </div>
          <span className="px-3 py-1 bg-emerald-500/10 text-emerald-400 text-xs font-semibold rounded-full border border-emerald-500/20">
            Connected
          </span>
        </div>

        <div className="glass-panel p-6 rounded-xl flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-purple-500/10 text-purple-400 rounded-lg">
              <Shield className="h-5 w-5" />
            </div>
            <div>
              <h3 className="font-semibold text-foreground">Multi-Tenant Row-Level Security</h3>
              <p className="text-xs text-muted-foreground">Enforced via Supabase RLS and Space ID context</p>
            </div>
          </div>
          <span className="px-3 py-1 bg-emerald-500/10 text-emerald-400 text-xs font-semibold rounded-full border border-emerald-500/20">
            Enforced
          </span>
        </div>
      </div>
    </div>
  );
};
