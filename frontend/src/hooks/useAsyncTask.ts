import { useState, useEffect, useCallback } from 'react';
import { useQuery, useMutation } from 'react-query';
import projectService from '../services/project.service';
import { AsyncTask } from '../types';
import { useAppDispatch } from '../store';
import { addNotification } from '../store/slices/uiSlice';

interface UseAsyncTaskOptions {
  pollingInterval?: number;
  onSuccess?: (task: AsyncTask) => void;
  onError?: (error: Error) => void;
}

export function useAsyncTask(
  taskId: string | null,
  options: UseAsyncTaskOptions = {}
) {
  const {
    pollingInterval = 2000,
    onSuccess,
    onError,
  } = options;

  const [isPolling, setIsPolling] = useState(false);
  const dispatch = useAppDispatch();

  const { data: task, refetch, error } = useQuery<AsyncTask, Error>(
    ['task', taskId],
    () => projectService.getTaskStatus(taskId!),
    {
      enabled: !!taskId && isPolling,
      refetchInterval: pollingInterval,
      onSuccess: (data) => {
        if (data.status === 'completed') {
          setIsPolling(false);
          dispatch(
            addNotification({
              type: 'success',
              message: 'Task completed successfully',
            })
          );
          onSuccess?.(data);
        } else if (data.status === 'failed') {
          setIsPolling(false);
          dispatch(
            addNotification({
              type: 'error',
              message: data.error || 'Task failed',
            })
          );
          onError?.(new Error(data.error || 'Task failed'));
        }
      },
      onError: (err) => {
        setIsPolling(false);
        dispatch(
          addNotification({
            type: 'error',
            message: err.message || 'Failed to check task status',
          })
        );
        onError?.(err);
      },
    }
  );

  const startPolling = useCallback(() => {
    if (taskId) {
      setIsPolling(true);
    }
  }, [taskId]);

  const stopPolling = useCallback(() => {
    setIsPolling(false);
  }, []);

  const cancelTask = useMutation(
    () => projectService.cancelTask(taskId!),
    {
      onSuccess: () => {
        setIsPolling(false);
        dispatch(
          addNotification({
            type: 'info',
            message: 'Task cancelled',
          })
        );
      },
      onError: (error: Error) => {
        dispatch(
          addNotification({
            type: 'error',
            message: error.message || 'Failed to cancel task',
          })
        );
      },
    }
  );

  useEffect(() => {
    return () => {
      setIsPolling(false);
    };
  }, []);

  return {
    task,
    error,
    isPolling,
    startPolling,
    stopPolling,
    cancelTask: cancelTask.mutate,
    refetch,
  };
}

// Hook for generating ROI
export function useGenerateROI() {
  const dispatch = useAppDispatch();
  const [taskId, setTaskId] = useState<string | null>(null);

  const generateMutation = useMutation<
    AsyncTask,
    Error,
    {
      projectId: string;
      options: {
        format?: 'docx' | 'pdf';
        include_appendices?: boolean;
        include_recommendations?: boolean;
      };
    }
  >(
    ({ projectId, options }) =>
      projectService.generateROI(projectId, options),
    {
      onSuccess: (task) => {
        setTaskId(task.task_id);
        dispatch(
          addNotification({
            type: 'info',
            message: 'ROI generation started',
          })
        );
      },
      onError: (error) => {
        dispatch(
          addNotification({
            type: 'error',
            message: error.message || 'Failed to start ROI generation',
          })
        );
      },
    }
  );

  const taskStatus = useAsyncTask(taskId, {
    onSuccess: (task) => {
      if (task.result?.download_url) {
        window.open(task.result.download_url, '_blank');
      }
    },
  });

  return {
    generate: generateMutation.mutate,
    isGenerating: generateMutation.isLoading,
    ...taskStatus,
  };
}

// Hook for exporting project
export function useExportProject() {
  const dispatch = useAppDispatch();
  const [taskId, setTaskId] = useState<string | null>(null);

  const exportMutation = useMutation<
    AsyncTask,
    Error,
    {
      projectId: string;
      format: 'json' | 'csv' | 'xlsx';
    }
  >(
    ({ projectId, format }) =>
      projectService.exportProject(projectId, format),
    {
      onSuccess: (task) => {
        setTaskId(task.task_id);
        dispatch(
          addNotification({
            type: 'info',
            message: 'Export started',
          })
        );
      },
      onError: (error) => {
        dispatch(
          addNotification({
            type: 'error',
            message: error.message || 'Failed to start export',
          })
        );
      },
    }
  );

  const taskStatus = useAsyncTask(taskId, {
    onSuccess: (task) => {
      if (task.result?.download_url) {
        window.open(task.result.download_url, '_blank');
      }
    },
  });

  return {
    export: exportMutation.mutate,
    isExporting: exportMutation.isLoading,
    ...taskStatus,
  };
}