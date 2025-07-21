import { useQuery, useMutation, useQueryClient } from 'react-query';
import projectService from '../services/project.service';
import { TimelineEntry, TimelineFormData } from '../types';
import { useAppDispatch } from '../store';
import { addNotification } from '../store/slices/uiSlice';

// Query key factory
const timelineKeys = {
  all: ['timeline'] as const,
  lists: () => [...timelineKeys.all, 'list'] as const,
  list: (projectId: string) => [...timelineKeys.lists(), projectId] as const,
};

// Get project timeline
export function useProjectTimeline(projectId: string) {
  return useQuery<TimelineEntry[], Error>(
    timelineKeys.list(projectId),
    () => projectService.getProjectTimeline(projectId),
    {
      enabled: !!projectId,
      staleTime: 5 * 60 * 1000,
    }
  );
}

// Create timeline entry
export function useCreateTimelineEntry() {
  const queryClient = useQueryClient();
  const dispatch = useAppDispatch();

  return useMutation<
    TimelineEntry,
    Error,
    { projectId: string; data: TimelineFormData }
  >(
    ({ projectId, data }) =>
      projectService.createTimelineEntry(projectId, data),
    {
      onSuccess: (_, { projectId }) => {
        queryClient.invalidateQueries(timelineKeys.list(projectId));
        dispatch(
          addNotification({
            type: 'success',
            message: 'Timeline entry created successfully',
          })
        );
      },
      onError: (error) => {
        dispatch(
          addNotification({
            type: 'error',
            message: error.message || 'Failed to create timeline entry',
          })
        );
      },
    }
  );
}

// Update timeline entry
export function useUpdateTimelineEntry() {
  const queryClient = useQueryClient();
  const dispatch = useAppDispatch();

  return useMutation<
    TimelineEntry,
    Error,
    { id: number; projectId: string; data: Partial<TimelineFormData> }
  >(
    ({ id, data }) => projectService.updateTimelineEntry(id, data),
    {
      onSuccess: (_, { projectId }) => {
        queryClient.invalidateQueries(timelineKeys.list(projectId));
        dispatch(
          addNotification({
            type: 'success',
            message: 'Timeline entry updated successfully',
          })
        );
      },
      onError: (error) => {
        dispatch(
          addNotification({
            type: 'error',
            message: error.message || 'Failed to update timeline entry',
          })
        );
      },
    }
  );
}

// Delete timeline entry
export function useDeleteTimelineEntry() {
  const queryClient = useQueryClient();
  const dispatch = useAppDispatch();

  return useMutation<void, Error, { id: number; projectId: string }>(
    ({ id }) => projectService.deleteTimelineEntry(id),
    {
      onSuccess: (_, { projectId }) => {
        queryClient.invalidateQueries(timelineKeys.list(projectId));
        dispatch(
          addNotification({
            type: 'success',
            message: 'Timeline entry deleted successfully',
          })
        );
      },
      onError: (error) => {
        dispatch(
          addNotification({
            type: 'error',
            message: error.message || 'Failed to delete timeline entry',
          })
        );
      },
    }
  );
}

// Generate timeline suggestions
export function useTimelineSuggestions() {
  const dispatch = useAppDispatch();

  return useMutation<
    any,
    Error,
    { projectId: string; context?: string }
  >(
    ({ projectId, context }) =>
      projectService.generateTimelineSuggestions(projectId, context),
    {
      onError: (error) => {
        dispatch(
          addNotification({
            type: 'error',
            message: error.message || 'Failed to generate suggestions',
          })
        );
      },
    }
  );
}

export default useProjectTimeline;