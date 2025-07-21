// User types
export interface User {
  id: number;
  username: string;
  email: string;
  role: 'user' | 'admin';
  created_at: string;
  is_active: boolean;
}

// Auth types
export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterData {
  username: string;
  email: string;
  password: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
}

// Project types
export interface Project {
  id: string;
  name: string;
  description?: string;
  created_at: string;
  updated_at?: string;
  owner_id: number;
  vessel_info?: VesselInfo;
  incident_info?: IncidentInfo;
  metadata?: Record<string, any>;
}

export interface VesselInfo {
  name?: string;
  type?: string;
  imo?: string;
  flag?: string;
  gross_tonnage?: number;
}

export interface IncidentInfo {
  date?: string;
  location?: string;
  type?: string;
  weather?: string;
  sea_state?: string;
}

// Evidence types
export interface Evidence {
  id: number;
  project_id: string;
  title: string;
  file_name: string;
  file_path: string;
  file_type: string;
  file_size: number;
  uploaded_at: string;
  summary?: string;
  content?: string;
  metadata?: Record<string, any>;
}

// Timeline types
export interface TimelineEntry {
  id: number;
  project_id: string;
  timestamp: string;
  description: string;
  event_type?: string;
  location?: string;
  actors?: string;
  significance?: 'low' | 'medium' | 'high' | 'critical';
  evidence_ids?: number[];
  created_at: string;
}

// Causal factor types
export interface CausalFactor {
  id: number;
  project_id: string;
  category: string;
  description: string;
  barrier_type?: string;
  remedial_action?: string;
  evidence_ids?: number[];
  contributing_factors?: string[];
  created_at: string;
}

// Generated document types
export interface GeneratedDocument {
  id: number;
  project_id: string;
  document_type: 'roi' | 'summary' | 'export';
  file_name: string;
  file_path: string;
  generated_at: string;
  metadata?: Record<string, any>;
}

// API response types
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

// Task types for async operations
export interface AsyncTask {
  task_id: string;
  state: 'PENDING' | 'STARTED' | 'PROGRESS' | 'SUCCESS' | 'FAILURE' | 'RETRY' | 'REVOKED';
  current?: number;
  total?: number;
  status?: string;
  result?: any;
  error?: string;
}

// Form types
export interface ProjectFormData {
  name: string;
  description?: string;
  vessel_info?: VesselInfo;
  incident_info?: IncidentInfo;
}

export interface TimelineFormData {
  timestamp: Date | string;
  description: string;
  event_type?: string;
  location?: string;
  actors?: string;
  significance?: 'low' | 'medium' | 'high' | 'critical';
  evidence_ids?: number[];
}

export interface CausalFactorFormData {
  category: string;
  description: string;
  barrier_type?: string;
  remedial_action?: string;
  evidence_ids?: number[];
  contributing_factors?: string[];
}

// Filter and search types
export interface ProjectFilters {
  search?: string;
  status?: string;
  date_from?: string;
  date_to?: string;
  sort_by?: 'created_at' | 'updated_at' | 'name';
  sort_order?: 'asc' | 'desc';
}

// Statistics types
export interface ProjectStatistics {
  evidence_count: number;
  timeline_count: number;
  causal_count: number;
}

export interface UserStatistics {
  total_projects: number;
  total_evidence: number;
  total_timeline_entries: number;
  total_causal_factors: number;
}