import { useQuery, useMutation, useQueryClient } from 'react-query';
import projectService from '../services/project.service';
import { CausalFactor, CausalFactorFormData } from '../types';
import { useAppDispatch } from '../store';
import { addNotification } from '../store/slices/uiSlice';

// Query key factory
const causalFactorKeys = {
  all: ['causalFactors'] as const,
  lists: () => [...causalFactorKeys.all, 'list'] as const,
  list: (projectId: string) => [...causalFactorKeys.lists(), projectId] as const,
};

// Get project causal factors
export function useProjectCausalFactors(projectId: string) {
  return useQuery<CausalFactor[], Error>(
    causalFactorKeys.list(projectId),
    () => projectService.getProjectCausalFactors(projectId),
    {
      enabled: !!projectId,
      staleTime: 5 * 60 * 1000,
    }
  );
}

// Create causal factor
export function useCreateCausalFactor() {
  const queryClient = useQueryClient();
  const dispatch = useAppDispatch();

  return useMutation<
    CausalFactor,
    Error,
    { projectId: string; data: CausalFactorFormData }
  >(
    ({ projectId, data }) =>
      projectService.createCausalFactor(projectId, data),
    {
      onSuccess: (_, { projectId }) => {
        queryClient.invalidateQueries(causalFactorKeys.list(projectId));
        dispatch(
          addNotification({
            type: 'success',
            message: 'Causal factor created successfully',
          })
        );
      },
      onError: (error) => {
        dispatch(
          addNotification({
            type: 'error',
            message: error.message || 'Failed to create causal factor',
          })
        );
      },
    }
  );
}

// Update causal factor
export function useUpdateCausalFactor() {
  const queryClient = useQueryClient();
  const dispatch = useAppDispatch();

  return useMutation<
    CausalFactor,
    Error,
    { id: number; projectId: string; data: Partial<CausalFactorFormData> }
  >(
    ({ id, data }) => projectService.updateCausalFactor(id, data),
    {
      onSuccess: (_, { projectId }) => {
        queryClient.invalidateQueries(causalFactorKeys.list(projectId));
        dispatch(
          addNotification({
            type: 'success',
            message: 'Causal factor updated successfully',
          })
        );
      },
      onError: (error) => {
        dispatch(
          addNotification({
            type: 'error',
            message: error.message || 'Failed to update causal factor',
          })
        );
      },
    }
  );
}

// Delete causal factor
export function useDeleteCausalFactor() {
  const queryClient = useQueryClient();
  const dispatch = useAppDispatch();

  return useMutation<void, Error, { id: number; projectId: string }>(
    ({ id }) => projectService.deleteCausalFactor(id),
    {
      onSuccess: (_, { projectId }) => {
        queryClient.invalidateQueries(causalFactorKeys.list(projectId));
        dispatch(
          addNotification({
            type: 'success',
            message: 'Causal factor deleted successfully',
          })
        );
      },
      onError: (error) => {
        dispatch(
          addNotification({
            type: 'error',
            message: error.message || 'Failed to delete causal factor',
          })
        );
      },
    }
  );
}

// Analyze causal chain
export function useAnalyzeCausalChain() {
  const dispatch = useAppDispatch();

  return useMutation<
    any,
    Error,
    { projectId: string; incidentType?: string }
  >(
    ({ projectId, incidentType }) =>
      projectService.analyzeCausalChain(projectId, incidentType),
    {
      onError: (error) => {
        dispatch(
          addNotification({
            type: 'error',
            message: error.message || 'Failed to analyze causal chain',
          })
        );
      },
    }
  );
}

export default useProjectCausalFactors;