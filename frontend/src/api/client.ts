/**
 * API Client for Mitsumi AI Platform
 * Complete version with all exports
 */

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

// ============================================
// TYPES
// ============================================

export interface User {
  id: string;
  email: string;
  name?: string;
  role?: string;
  roles?: string[];
  modules?: string[];
  is_super_admin?: boolean;
}

export interface CurrentUser extends User {
  roles: string[];
  modules: string[];
  is_super_admin: boolean;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user?: User;
}

// ============================================
// NOTIFICATION TYPES
// ============================================

export type NotificationKind = 'job' | 'task' | 'user' | 'system';

export interface NotificationRecord {
  id: string;
  title: string;
  body?: string;
  kind: NotificationKind;
  read: boolean;
  created_at: string;
  link?: string;
  updated_at?: string;
}

export interface NotificationListResponse {
  items: NotificationRecord[];
  total: number;
  unread: number;
}

// ============================================
// AUTH API
// ============================================

export async function directLogin(email: string, password: string): Promise<LoginResponse> {
  const response = await fetch(`${API_BASE}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || error.detail || 'Login failed');
  }

  return response.json();
}

export async function fetchMe(): Promise<CurrentUser> {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}/api/auth/me`, {
    headers: { 'Authorization': `Bearer ${token}` },
  });

  if (!response.ok) {
    throw new Error('Failed to fetch user');
  }

  const user = await response.json();
  return {
    ...user,
    roles: user.roles || ['user'],
    modules: user.modules || [],
    is_super_admin: user.is_super_admin || false,
  };
}

export async function registerUser(email: string, password: string, name?: string): Promise<LoginResponse> {
  const response = await fetch(`${API_BASE}/api/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password, name }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || 'Registration failed');
  }

  return response.json();
}

export function logout(): void {
  localStorage.removeItem('token');
  localStorage.removeItem('user');
}

// ============================================
// NOTIFICATIONS API
// ============================================

interface ListNotificationsParams {
  skip: number;
  limit: number;
  unread_only?: boolean;
  kind?: string;
}

export async function listNotifications(params: ListNotificationsParams): Promise<NotificationListResponse> {
  const token = localStorage.getItem('token');
  const url = new URL(`${API_BASE}/api/notifications`);
  url.searchParams.append('skip', String(params.skip));
  url.searchParams.append('limit', String(params.limit));
  if (params.unread_only) url.searchParams.append('unread_only', 'true');
  if (params.kind) url.searchParams.append('kind', params.kind);

  const response = await fetch(url.toString(), {
    headers: { 'Authorization': `Bearer ${token}` },
  });

  if (!response.ok) {
    throw new Error('Failed to fetch notifications');
  }

  const data = await response.json();
  
  if (data.items && Array.isArray(data.items)) {
    return data;
  }
  
  if (Array.isArray(data)) {
    return {
      items: data,
      total: data.length,
      unread: data.filter((n: NotificationRecord) => !n.read).length,
    };
  }
  
  return {
    items: data.items || [],
    total: data.total || 0,
    unread: data.unread || 0,
  };
}

export async function markNotificationRead(id: string): Promise<NotificationRecord> {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}/api/notifications/${id}/read`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
  });

  if (!response.ok) {
    throw new Error('Failed to mark notification as read');
  }

  return response.json();
}

export async function markAllNotificationsRead(): Promise<{ updated: number }> {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}/api/notifications/read-all`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
  });

  if (!response.ok) {
    throw new Error('Failed to mark all notifications as read');
  }

  return response.json();
}

export async function deleteNotification(id: string): Promise<void> {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}/api/notifications/${id}`, {
    method: 'DELETE',
    headers: { 'Authorization': `Bearer ${token}` },
  });

  if (!response.ok) {
    throw new Error('Failed to delete notification');
  }
}

// ============================================
// MENTION / SEARCH API
// ============================================

export interface MentionCandidate {
  id: string;
  email: string;
  name: string;
  avatar?: string;
}

export async function searchMentionCandidates(query: string): Promise<MentionCandidate[]> {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}/api/search/mentions?q=${encodeURIComponent(query)}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    return [];
  }

  return response.json();
}

export async function searchUsers(query: string): Promise<MentionCandidate[]> {
  return searchMentionCandidates(query);
}

// ============================================
// CHAT / AGENT API
// ============================================

export interface ChatMessage {
  id: string;
  content: string;
  role: 'user' | 'assistant' | 'system';
  created_at: string;
}

export interface ChatSession {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export async function listChatSessions(): Promise<ChatSession[]> {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}/api/chat/sessions`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error('Failed to fetch chat sessions');
  }

  return response.json();
}

export async function createChatSession(title?: string): Promise<ChatSession> {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}/api/chat/sessions`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ title }),
  });

  if (!response.ok) {
    throw new Error('Failed to create chat session');
  }

  return response.json();
}

export async function deleteChatSession(id: string): Promise<void> {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}/api/chat/sessions/${id}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error('Failed to delete chat session');
  }
}

// ============================================
// TOOLS API
// ============================================

export interface ToolResult {
  id: string;
  name: string;
  description?: string;
  created_at: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  result?: any;
}

export async function listRecentTools(): Promise<ToolResult[]> {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}/api/tools/recent`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    return [];
  }

  return response.json();
}

// ============================================
// CHAT API (AgentView)
// ============================================

export interface Chat {
  id: string;
  title: string;
  agent_name?: string;
  created_at: string;
  updated_at: string;
  pinned: boolean;
  message_count?: number;
}

export async function listChats(): Promise<Chat[]> {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}/api/chats`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error('Failed to fetch chats');
  }

  return response.json();
}

export async function getChat(id: string): Promise<Chat> {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}/api/chats/${id}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error('Failed to fetch chat');
  }

  return response.json();
}

export async function createChat(data: { title: string; agent_name?: string }): Promise<Chat> {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}/api/chats`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error('Failed to create chat');
  }

  return response.json();
}

export async function deleteChat(id: string): Promise<void> {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}/api/chats/${id}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error('Failed to delete chat');
  }
}

export async function renameChat(id: string, title: string): Promise<Chat> {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}/api/chats/${id}/rename`, {
    method: 'PATCH',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ title }),
  });

  if (!response.ok) {
    throw new Error('Failed to rename chat');
  }

  return response.json();
}

export async function pinChat(id: string, pinned: boolean): Promise<Chat> {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}/api/chats/${id}/pin`, {
    method: 'PATCH',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ pinned }),
  });

  if (!response.ok) {
    throw new Error('Failed to pin/unpin chat');
  }

  return response.json();
}

// ============================================
// DEPARTMENT API
// ============================================

export interface Region {
  id: string;
  name: string;
  code: string;
}

export async function fetchRegions(): Promise<Region[]> {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}/api/regions`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    return [];
  }

  return response.json();
}

export interface DepartmentOverview {
  department: string;
  agent_count: number;
  active_tasks: number;
  completed_tasks: number;
  total_tasks: number;
  metrics: {
    success_rate: number;
    avg_response_time: number;
  };
}

export async function fetchDepartmentOverview(departmentId: string): Promise<DepartmentOverview> {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}/api/departments/${departmentId}/overview`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error('Failed to fetch department overview');
  }

  return response.json();
}

// ============================================
// TASKS API
// ============================================

export interface Task {
  id: string;
  title: string;
  description?: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  priority: 'low' | 'medium' | 'high' | 'critical';
  agent_name: string;
  created_at: string;
  updated_at: string;
  assigned_to?: string;
}

export interface TaskMetrics {
  total: number;
  completed: number;
  in_progress: number;
  pending: number;
  failed: number;
  success_rate: number;
}

export async function listTasks(params?: { status?: string; agent?: string; limit?: number }): Promise<Task[]> {
  const token = localStorage.getItem('token');
  const url = new URL(`${API_BASE}/api/tasks`);
  if (params?.status) url.searchParams.append('status', params.status);
  if (params?.agent) url.searchParams.append('agent', params.agent);
  if (params?.limit) url.searchParams.append('limit', String(params.limit));

  const response = await fetch(url.toString(), {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error('Failed to fetch tasks');
  }

  return response.json();
}

export async function getTaskMetrics(): Promise<TaskMetrics> {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}/api/tasks/metrics`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error('Failed to fetch task metrics');
  }

  return response.json();
}

export async function createTask(data: { title: string; description?: string; agent_name: string; priority?: string }): Promise<Task> {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}/api/tasks`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error('Failed to create task');
  }

  return response.json();
}

export async function deleteTask(id: string): Promise<void> {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}/api/tasks/${id}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error('Failed to delete task');
  }
}

export async function runAgentTask(taskId: string): Promise<Task> {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}/api/tasks/${taskId}/run`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error('Failed to run agent task');
  }

  return response.json();
}

export async function cancelAgentTask(taskId: string): Promise<Task> {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}/api/tasks/${taskId}/cancel`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error('Failed to cancel agent task');
  }

  return response.json();
}

// ============================================
// USER PREFERENCES
// ============================================

export interface UserPreferences {
  theme: 'light' | 'dark' | 'system';
  language: string;
  notifications_enabled: boolean;
  email_notifications: boolean;
}

export async function updatePreferences(preferences: Partial<UserPreferences>): Promise<UserPreferences> {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}/api/user/preferences`, {
    method: 'PATCH',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(preferences),
  });

  if (!response.ok) {
    throw new Error('Failed to update preferences');
  }

  return response.json();
}

// ============================================
// AGENT TOOLS API
// ============================================

export interface AgentTool {
  id: string;
  name: string;
  description: string;
  parameters?: Record<string, any>;
}

export async function fetchAgentTools(agentName?: string): Promise<AgentTool[]> {
  const token = localStorage.getItem('token');
  const url = new URL(`${API_BASE}/api/agent/tools`);
  if (agentName) url.searchParams.append('agent', agentName);

  const response = await fetch(url.toString(), {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    return [];
  }

  return response.json();
}

// ============================================
// CHAT API (Extended)
// ============================================

export interface ChatNote {
  id: string;
  content: string;
  created_at: string;
  updated_at: string;
}

export interface ChatArtifact {
  id: string;
  type: string;
  content: string;
  created_at: string;
}

export async function uploadFileToChat(chatId: string, file: File): Promise<ChatArtifact> {
  const token = localStorage.getItem('token');
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE}/api/chats/${chatId}/upload`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
    body: formData,
  });

  if (!response.ok) {
    throw new Error('Failed to upload file');
  }

  return response.json();
}

export async function getChatContext(chatId: string): Promise<any> {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}/api/chats/${chatId}/context`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error('Failed to get chat context');
  }

  return response.json();
}

export async function apiFetch(endpoint: string, options?: RequestInit): Promise<any> {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'API request failed' }));
    throw new Error(error.message || 'API request failed');
  }

  return response.json();
}

export async function addChatNote(chatId: string, content: string): Promise<ChatNote> {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}/api/chats/${chatId}/notes`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ content }),
  });

  if (!response.ok) {
    throw new Error('Failed to add chat note');
  }

  return response.json();
}

export async function deleteChatNote(chatId: string, noteId: string): Promise<void> {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}/api/chats/${chatId}/notes/${noteId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error('Failed to delete chat note');
  }
}

export async function listChatArtifacts(chatId: string): Promise<ChatArtifact[]> {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}/api/chats/${chatId}/artifacts`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    return [];
  }

  return response.json();
}

export async function listChatNotes(chatId: string): Promise<ChatNote[]> {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}/api/chats/${chatId}/notes`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    return [];
  }

  return response.json();
}

// ============================================
// AGENT JOBS API
// ============================================

export interface AgentJob {
  id: string;
  kind: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  created_at: string;
  updated_at: string;
  result?: any;
  error?: string;
}

export interface AgentJobKind {
  name: string;
  description: string;
  parameters?: Record<string, any>;
}

export async function listAgentJobs(params?: { status?: string; kind?: string; limit?: number }): Promise<AgentJob[]> {
  const token = localStorage.getItem('token');
  const url = new URL(`${API_BASE}/api/agent/jobs`);
  if (params?.status) url.searchParams.append('status', params.status);
  if (params?.kind) url.searchParams.append('kind', params.kind);
  if (params?.limit) url.searchParams.append('limit', String(params.limit));

  const response = await fetch(url.toString(), {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error('Failed to fetch agent jobs');
  }

  return response.json();
}

export async function listAgentJobKinds(): Promise<AgentJobKind[]> {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}/api/agent/job-kinds`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    return [];
  }

  return response.json();
}

export async function enqueueAgentJob(kind: string, parameters?: any): Promise<AgentJob> {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}/api/agent/jobs`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ kind, parameters }),
  });

  if (!response.ok) {
    throw new Error('Failed to enqueue agent job');
  }

  return response.json();
}

export async function cancelAgentJob(jobId: string): Promise<AgentJob> {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}/api/agent/jobs/${jobId}/cancel`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error('Failed to cancel agent job');
  }

  return response.json();
}

export async function retryAgentJob(jobId: string): Promise<AgentJob> {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}/api/agent/jobs/${jobId}/retry`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error('Failed to retry agent job');
  }

  return response.json();
}

// ============================================
// TASKS EXTENDED API
// ============================================

export async function runTaskWithAgent(taskId: string, agentName: string): Promise<Task> {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}/api/tasks/${taskId}/run-agent`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ agent_name: agentName }),
  });

  if (!response.ok) {
    throw new Error('Failed to run task with agent');
  }

  return response.json();
}

export async function updateTask(id: string, data: Partial<Task>): Promise<Task> {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}/api/tasks/${id}`, {
    method: 'PATCH',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error('Failed to update task');
  }

  return response.json();
}

// ============================================
// AUDIT LOGS API
// ============================================

export interface AuditEntry {
  id: string;
  user_id: string;
  user_email: string;
  action: string;
  resource: string;
  details: Record<string, any>;
  created_at: string;
}

export async function listAuditEntries(params?: { limit?: number; offset?: number; user?: string }): Promise<AuditEntry[]> {
  const token = localStorage.getItem('token');
  const url = new URL(`${API_BASE}/api/audit`);
  if (params?.limit) url.searchParams.append('limit', String(params.limit));
  if (params?.offset) url.searchParams.append('offset', String(params.offset));
  if (params?.user) url.searchParams.append('user', params.user);

  const response = await fetch(url.toString(), {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error('Failed to fetch audit entries');
  }

  return response.json();
}

// ============================================
// MODEL CONFIG API
// ============================================

export interface ModelConfig {
  id: string;
  name: string;
  provider: string;
  model: string;
  temperature: number;
  max_tokens: number;
}

export async function fetchModelConfig(department: string): Promise<ModelConfig> {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}/api/models/config/${department}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error('Failed to fetch model config');
  }

  return response.json();
}

export async function setDepartmentModel(department: string, modelId: string): Promise<ModelConfig> {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}/api/models/config/${department}`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ model_id: modelId }),
  });

  if (!response.ok) {
    throw new Error('Failed to set department model');
  }

  return response.json();
}

// ============================================
// USER PREFERENCES EXTENDED
// ============================================

export async function fetchPreferences(): Promise<UserPreferences> {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}/api/user/preferences`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error('Failed to fetch preferences');
  }

  return response.json();
}

// ============================================
// REGIONS EXTENDED API
// ============================================

export interface Country {
  code: string;
  name: string;
  flag?: string;
}

export async function fetchCountryCatalog(): Promise<Country[]> {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}/api/countries`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    return [];
  }

  return response.json();
}

export async function createRegion(data: { name: string; code: string }): Promise<Region> {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}/api/regions`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error('Failed to create region');
  }

  return response.json();
}

export async function updateRegion(id: string, data: Partial<Region>): Promise<Region> {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}/api/regions/${id}`, {
    method: 'PATCH',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error('Failed to update region');
  }

  return response.json();
}

export async function deleteRegion(id: string): Promise<void> {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}/api/regions/${id}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error('Failed to delete region');
  }
}

export async function addRegionCountry(regionId: string, countryCode: string): Promise<Region> {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}/api/regions/${regionId}/countries/${countryCode}`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error('Failed to add country to region');
  }

  return response.json();
}

export async function removeRegionCountry(regionId: string, countryCode: string): Promise<Region> {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}/api/regions/${regionId}/countries/${countryCode}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error('Failed to remove country from region');
  }

  return response.json();
}

// ============================================
// ROLES API
// ============================================

export interface Role {
  id: string;
  name: string;
  description: string;
  permissions: string[];
}

export async function fetchRoles(): Promise<Role[]> {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}/api/roles`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    return [];
  }

  return response.json();
}

// ============================================
// USERS ADMIN API
// ============================================

export async function listUsers(): Promise<User[]> {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}/api/users`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error('Failed to fetch users');
  }

  return response.json();
}

export async function inviteUser(email: string, role: string): Promise<User> {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}/api/users/invite`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, role }),
  });

  if (!response.ok) {
    throw new Error('Failed to invite user');
  }

  return response.json();
}

export async function updateUser(id: string, data: Partial<User>): Promise<User> {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}/api/users/${id}`, {
    method: 'PATCH',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error('Failed to update user');
  }

  return response.json();
}

export async function deleteUser(id: string): Promise<void> {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}/api/users/${id}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error('Failed to delete user');
  }
}
