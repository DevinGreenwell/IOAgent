import api from './api';
import {
  Project,
  ProjectFormData,
  ProjectFilters,
  PaginatedResponse,
  Evidence,
  TimelineEntry,
  TimelineFormData,
  CausalFactor,
  CausalFactorFormData,
  GeneratedDocument,
  AsyncTask,
} from '../types';

class ProjectService {
  // Projects
  async getProjects(filters?: ProjectFilters): Promise<PaginatedResponse<Project>> {
    const response = await api.get('/projects', { params: filters });
    return response.data;
  }

  async getProject(id: string): Promise<Project> {
    const response = await api.get(`/projects/${id}`);
    return response.data.project;
  }

  async createProject(data: ProjectFormData): Promise<Project> {
    const response = await api.post('/projects', data);
    return response.data.project;
  }

  async updateProject(id: string, data: Partial<ProjectFormData>): Promise<Project> {
    const response = await api.put(`/projects/${id}`, data);
    return response.data.project;
  }

  async deleteProject(id: string): Promise<void> {
    await api.delete(`/projects/${id}`);
  }

  // Evidence
  async getProjectEvidence(projectId: string): Promise<Evidence[]> {
    const response = await api.get(`/projects/${projectId}/evidence`);
    return response.data;
  }

  async uploadEvidence(projectId: string, file: File, data: { title: string; summary?: string }): Promise<Evidence> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', data.title);
    formData.append('project_id', projectId);
    if (data.summary) {
      formData.append('summary', data.summary);
    }

    const response = await api.post('/evidence/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  async deleteEvidence(id: number): Promise<void> {
    await api.delete(`/evidence/${id}`);
  }

  // Timeline
  async getProjectTimeline(projectId: string): Promise<TimelineEntry[]> {
    const response = await api.get(`/projects/${projectId}/timeline`);
    return response.data;
  }

  async createTimelineEntry(projectId: string, data: TimelineFormData): Promise<TimelineEntry> {
    const response = await api.post(`/projects/${projectId}/timeline`, data);
    return response.data;
  }

  async updateTimelineEntry(id: number, data: Partial<TimelineFormData>): Promise<TimelineEntry> {
    const response = await api.put(`/timeline/${id}`, data);
    return response.data;
  }

  async deleteTimelineEntry(id: number): Promise<void> {
    await api.delete(`/timeline/${id}`);
  }

  // Causal Factors
  async getProjectCausalFactors(projectId: string): Promise<CausalFactor[]> {
    const response = await api.get(`/projects/${projectId}/causal-factors`);
    return response.data;
  }

  async createCausalFactor(projectId: string, data: CausalFactorFormData): Promise<CausalFactor> {
    const response = await api.post(`/projects/${projectId}/causal-factors`, data);
    return response.data;
  }

  async updateCausalFactor(id: number, data: Partial<CausalFactorFormData>): Promise<CausalFactor> {
    const response = await api.put(`/causal-factors/${id}`, data);
    return response.data;
  }

  async deleteCausalFactor(id: number): Promise<void> {
    await api.delete(`/causal-factors/${id}`);
  }

  // AI Features
  async generateTimelineSuggestions(projectId: string, context?: string): Promise<any> {
    const response = await api.post(`/projects/${projectId}/timeline/suggest`, { context });
    return response.data;
  }

  async analyzeCausalChain(projectId: string, incidentType?: string): Promise<any> {
    const response = await api.post(`/projects/${projectId}/causal-analysis`, { incident_type: incidentType });
    return response.data;
  }

  // Document Generation
  async generateROI(projectId: string, options: {
    format?: 'docx' | 'pdf';
    include_appendices?: boolean;
    include_recommendations?: boolean;
  }): Promise<AsyncTask> {
    const response = await api.post(`/async/projects/${projectId}/generate-roi-async`, options);
    return response.data;
  }

  async exportProject(projectId: string, format: 'json' | 'csv' | 'xlsx'): Promise<AsyncTask> {
    const response = await api.post(`/async/projects/${projectId}/export-async`, { format });
    return response.data;
  }

  // Task Management
  async getTaskStatus(taskId: string): Promise<AsyncTask> {
    const response = await api.get(`/async/task/${taskId}/status`);
    return response.data;
  }

  async cancelTask(taskId: string): Promise<void> {
    await api.post(`/async/task/${taskId}/cancel`);
  }

  // Cached endpoints
  async getProjectSummary(projectId: string): Promise<any> {
    const response = await api.get(`/cached/projects/${projectId}/summary`);
    return response.data;
  }

  async getCachedTimeline(projectId: string): Promise<any> {
    const response = await api.get(`/cached/projects/${projectId}/timeline-cached`);
    return response.data;
  }

  async getCachedCausalAnalysis(projectId: string): Promise<any> {
    const response = await api.get(`/cached/projects/${projectId}/causal-analysis-cached`);
    return response.data;
  }
}

export default new ProjectService();