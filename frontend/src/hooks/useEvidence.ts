import { useQuery, useMutation, useQueryClient } from 'react-query';
import projectService from '../services/project.service';
import { Evidence } from '../types';
import { useAppDispatch } from '../store';
import { addNotification } from '../store/slices/uiSlice';

// Query key factory
const evidenceKeys = {
  all: ['evidence'] as const,
  lists: () => [...evidenceKeys.all, 'list'] as const,
  list: (projectId: string) => [...evidenceKeys.lists(), projectId] as const,
};

// Get project evidence
export function useProjectEvidence(projectId: string) {
  return useQuery<Evidence[], Error>(
    evidenceKeys.list(projectId),
    () => projectService.getProjectEvidence(projectId),
    {
      enabled: !!projectId,
      staleTime: 5 * 60 * 1000,
    }
  );
}

// Upload evidence
export function useUploadEvidence() {
  const queryClient = useQueryClient();
  const dispatch = useAppDispatch();

  return useMutation<
    Evidence,
    Error,
    {
      projectId: string;
      file: File;
      data: { title: string; summary?: string };
    }
  >(
    ({ projectId, file, data }) =>
      projectService.uploadEvidence(projectId, file, data),
    {
      onSuccess: (newEvidence, { projectId }) => {
        queryClient.invalidateQueries(evidenceKeys.list(projectId));
        dispatch(
          addNotification({
            type: 'success',
            message: 'Evidence uploaded successfully',
          })
        );
      },
      onError: (error) => {
        dispatch(
          addNotification({
            type: 'error',
            message: error.message || 'Failed to upload evidence',
          })
        );
      },
    }
  );
}

// Delete evidence
export function useDeleteEvidence() {
  const queryClient = useQueryClient();
  const dispatch = useAppDispatch();

  return useMutation<void, Error, { id: number; projectId: string }>(
    ({ id }) => projectService.deleteEvidence(id),
    {
      onSuccess: (_, { projectId }) => {
        queryClient.invalidateQueries(evidenceKeys.list(projectId));
        dispatch(
          addNotification({
            type: 'success',
            message: 'Evidence deleted successfully',
          })
        );
      },
      onError: (error) => {
        dispatch(
          addNotification({
            type: 'error',
            message: error.message || 'Failed to delete evidence',
          })
        );
      },
    }
  );
}

export default useProjectEvidence;