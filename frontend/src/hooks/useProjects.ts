import { useQuery, useMutation, useQueryClient } from 'react-query';
import projectService from '../services/project.service';
import { Project, ProjectFormData, ProjectFilters, PaginatedResponse } from '../types';
import { useAppDispatch } from '../store';
import { addNotification } from '../store/slices/uiSlice';

// Query key factory
const projectKeys = {
  all: ['projects'] as const,
  lists: () => [...projectKeys.all, 'list'] as const,
  list: (filters: ProjectFilters) => [...projectKeys.lists(), filters] as const,
  details: () => [...projectKeys.all, 'detail'] as const,
  detail: (id: string) => [...projectKeys.details(), id] as const,
};

// Get projects list
export function useProjects(filters?: ProjectFilters) {
  return useQuery<PaginatedResponse<Project>, Error>(
    projectKeys.list(filters || {}),
    () => projectService.getProjects(filters),
    {
      keepPreviousData: true,
      staleTime: 5 * 60 * 1000, // 5 minutes
    }
  );
}

// Get single project
export function useProject(id: string) {
  return useQuery<Project, Error>(
    projectKeys.detail(id),
    () => projectService.getProject(id),
    {
      enabled: !!id,
      staleTime: 5 * 60 * 1000,
    }
  );
}

// Create project
export function useCreateProject() {
  const queryClient = useQueryClient();
  const dispatch = useAppDispatch();

  return useMutation<Project, Error, ProjectFormData>(
    (data) => projectService.createProject(data),
    {
      onSuccess: (newProject) => {
        queryClient.invalidateQueries(projectKeys.lists());
        dispatch(
          addNotification({
            type: 'success',
            message: `Project "${newProject.name}" created successfully`,
          })
        );
      },
      onError: (error) => {
        dispatch(
          addNotification({
            type: 'error',
            message: error.message || 'Failed to create project',
          })
        );
      },
    }
  );
}

// Update project
export function useUpdateProject() {
  const queryClient = useQueryClient();
  const dispatch = useAppDispatch();

  return useMutation<
    Project,
    Error,
    { id: string; data: Partial<ProjectFormData> }
  >(
    ({ id, data }) => projectService.updateProject(id, data),
    {
      onSuccess: (updatedProject) => {
        queryClient.invalidateQueries(projectKeys.detail(updatedProject.id));
        queryClient.invalidateQueries(projectKeys.lists());
        dispatch(
          addNotification({
            type: 'success',
            message: 'Project updated successfully',
          })
        );
      },
      onError: (error) => {
        dispatch(
          addNotification({
            type: 'error',
            message: error.message || 'Failed to update project',
          })
        );
      },
    }
  );
}

// Delete project
export function useDeleteProject() {
  const queryClient = useQueryClient();
  const dispatch = useAppDispatch();

  return useMutation<void, Error, string>(
    (id) => projectService.deleteProject(id),
    {
      onSuccess: (_, deletedId) => {
        queryClient.invalidateQueries(projectKeys.lists());
        queryClient.removeQueries(projectKeys.detail(deletedId));
        dispatch(
          addNotification({
            type: 'success',
            message: 'Project deleted successfully',
          })
        );
      },
      onError: (error) => {
        dispatch(
          addNotification({
            type: 'error',
            message: error.message || 'Failed to delete project',
          })
        );
      },
    }
  );
}

export default useProjects;