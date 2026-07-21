import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { CurrentUser } from '../api/client';

interface SessionState {
  token: string | null;
  user: CurrentUser | null;
  setToken: (token: string) => void;
  setUser: (user: CurrentUser) => void;
  clear: () => void;
}

export const useSessionStore = create<SessionState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      setToken: (token) => set({ token }),
      setUser: (user) => set({ user }),
      clear: () => set({ token: null, user: null }),
    }),
    {
      name: 'session-storage',
    }
  )
);

// ============================================
// HELPER FUNCTIONS
// ============================================

export function canAccessModule(user: CurrentUser | null, module: string): boolean {
  if (!user) return false;
  if (user.is_super_admin) return true;
  return user.modules?.includes(module) || false;
}

export function hasRole(user: CurrentUser | null, role: string): boolean {
  if (!user) return false;
  if (user.is_super_admin) return true;
  return user.roles?.includes(role) || false;
}
