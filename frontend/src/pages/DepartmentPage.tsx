import { useEffect, useState, useMemo } from "react";
import { TopBar } from "../components/layout/TopBar";
import { AgentStatusBar } from "../components/dashboard/AgentStatusBar";
import { DepartmentAgentCard } from "../components/department/DepartmentAgentCard";
import { fetchDepartmentOverview, fetchRegions, type DepartmentOverview, type Region } from "../api/client";
import { canAccessModule, useSessionStore } from "../store/session";

const DEPARTMENT_META: Record<string, { label: string; icon: string; color: string; module: string }> = {
  sales: { label: "Sales", icon: "💰", color: "brand", module: "department:sales" },
  marketing: { label: "Marketing", icon: "📊", color: "sky", module: "department:marketing" },
  finance: { label: "Finance", icon: "🏦", color: "emerald", module: "department:finance" },
  operations: { label: "Operations", icon: "📦", color: "amber", module: "department:operations" },
  ops: { label: "Operations", icon: "📦", color: "amber", module: "department:ops" },
};

export function DepartmentPage({ departmentKey }: { departmentKey?: string }) {
  const user = useSessionStore((s) => s.user);
  const [overview, setOverview] = useState<DepartmentOverview | null>(null);
  const [regions, setRegions] = useState<Region[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const department = departmentKey?.toLowerCase() || "";
  const meta = DEPARTMENT_META[department];

  console.log("DepartmentPage - departmentKey:", departmentKey);

  useEffect(() => {
    if (!department) {
      setLoading(false);
      return;
    }
    async function loadData() {
      setLoading(true);
      setError(null);
      try {
        const [overviewData, regionsData] = await Promise.all([
          fetchDepartmentOverview(department),
          fetchRegions().catch(() => [] as Region[]),
        ]);
        setOverview(overviewData);
        setRegions(regionsData || []);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load department data");
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [department]);

  const regionNames = useMemo(() => {
    const safeRegions = regions || [];
    if (safeRegions.length === 0) return ["No regions configured"];
    return safeRegions.map((r) => r.name).slice(0, 3);
  }, [regions]);

  if (!department) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-6">
        <div className="text-6xl mb-4">📂</div>
        <h2 className="text-xl font-semibold text-slate-900 dark:text-white mb-2">
          Department not specified
        </h2>
        <p className="text-slate-500 dark:text-slate-400">
          Please select a department from the sidebar.
        </p>
      </div>
    );
  }

  if (!meta) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-6">
        <div className="text-6xl mb-4">🔍</div>
        <h2 className="text-xl font-semibold text-slate-900 dark:text-white mb-2">
          Department "{department}" not found
        </h2>
        <p className="text-slate-500 dark:text-slate-400">
          Available departments: Sales, Marketing, Finance, Operations
        </p>
      </div>
    );
  }

  if (!canAccessModule(user, meta.module)) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-6">
        <div className="text-6xl mb-4">🔒</div>
        <h2 className="text-xl font-semibold text-slate-900 dark:text-white mb-2">
          You don't have access to this department
        </h2>
        <p className="text-slate-500 dark:text-slate-400 text-center max-w-md">
          Ask a super admin to grant you the module permission.
        </p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-slate-500">Loading department data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-red-500">Error: {error}</div>
      </div>
    );
  }

  return (
    <>
      <TopBar
        title={meta.label}
        subtitle={`${overview?.agent_count || 0} agents · ${overview?.active_tasks || 0} active tasks`}
      />
      <div className="flex-1 p-6 space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-4">
            <div className="text-sm text-slate-500">Total Tasks</div>
            <div className="text-2xl font-bold text-slate-900 dark:text-white">
              {overview?.total_tasks || 0}
            </div>
          </div>
          <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-4">
            <div className="text-sm text-slate-500">Active Tasks</div>
            <div className="text-2xl font-bold text-brand">
              {overview?.active_tasks || 0}
            </div>
          </div>
          <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-4">
            <div className="text-sm text-slate-500">Completed</div>
            <div className="text-2xl font-bold text-emerald-500">
              {overview?.completed_tasks || 0}
            </div>
          </div>
          <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-4">
            <div className="text-sm text-slate-500">Success Rate</div>
            <div className="text-2xl font-bold text-sky-500">
              {overview?.metrics?.success_rate || 0}%
            </div>
          </div>
        </div>

        <AgentStatusBar department={department} />

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <DepartmentAgentCard agentName={department} department={department} />
          <DepartmentAgentCard agentName="support" department={department} />
        </div>

        <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-4">
          <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">Regions</h3>
          <div className="flex flex-wrap gap-2">
            {regionNames.map((name, i) => (
              <span key={i} className="px-3 py-1 bg-slate-100 dark:bg-slate-800 rounded-full text-xs text-slate-600 dark:text-slate-400">
                {name}
              </span>
            ))}
          </div>
        </div>
      </div>
    </>
  );
}
