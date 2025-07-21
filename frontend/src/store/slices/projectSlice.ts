import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { Project, Evidence, TimelineEntry, CausalFactor } from '../../types';

interface ProjectState {
  currentProject: Project | null;
  projects: Project[];
  evidence: Evidence[];
  timeline: TimelineEntry[];
  causalFactors: CausalFactor[];
  loading: boolean;
  error: string | null;
}

const initialState: ProjectState = {
  currentProject: null,
  projects: [],
  evidence: [],
  timeline: [],
  causalFactors: [],
  loading: false,
  error: null,
};

const projectSlice = createSlice({
  name: 'project',
  initialState,
  reducers: {
    setProjects: (state, action: PayloadAction<Project[]>) => {
      state.projects = action.payload;
    },
    setCurrentProject: (state, action: PayloadAction<Project | null>) => {
      state.currentProject = action.payload;
    },
    updateProject: (state, action: PayloadAction<Project>) => {
      const index = state.projects.findIndex((p) => p.id === action.payload.id);
      if (index !== -1) {
        state.projects[index] = action.payload;
      }
      if (state.currentProject?.id === action.payload.id) {
        state.currentProject = action.payload;
      }
    },
    removeProject: (state, action: PayloadAction<string>) => {
      state.projects = state.projects.filter((p) => p.id !== action.payload);
      if (state.currentProject?.id === action.payload) {
        state.currentProject = null;
      }
    },
    setEvidence: (state, action: PayloadAction<Evidence[]>) => {
      state.evidence = action.payload;
    },
    addEvidence: (state, action: PayloadAction<Evidence>) => {
      state.evidence.push(action.payload);
    },
    removeEvidence: (state, action: PayloadAction<number>) => {
      state.evidence = state.evidence.filter((e) => e.id !== action.payload);
    },
    setTimeline: (state, action: PayloadAction<TimelineEntry[]>) => {
      state.timeline = action.payload;
    },
    addTimelineEntry: (state, action: PayloadAction<TimelineEntry>) => {
      state.timeline.push(action.payload);
      // Sort by timestamp
      state.timeline.sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
    },
    updateTimelineEntry: (state, action: PayloadAction<TimelineEntry>) => {
      const index = state.timeline.findIndex((t) => t.id === action.payload.id);
      if (index !== -1) {
        state.timeline[index] = action.payload;
        // Re-sort by timestamp
        state.timeline.sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
      }
    },
    removeTimelineEntry: (state, action: PayloadAction<number>) => {
      state.timeline = state.timeline.filter((t) => t.id !== action.payload);
    },
    setCausalFactors: (state, action: PayloadAction<CausalFactor[]>) => {
      state.causalFactors = action.payload;
    },
    addCausalFactor: (state, action: PayloadAction<CausalFactor>) => {
      state.causalFactors.push(action.payload);
    },
    updateCausalFactor: (state, action: PayloadAction<CausalFactor>) => {
      const index = state.causalFactors.findIndex((c) => c.id === action.payload.id);
      if (index !== -1) {
        state.causalFactors[index] = action.payload;
      }
    },
    removeCausalFactor: (state, action: PayloadAction<number>) => {
      state.causalFactors = state.causalFactors.filter((c) => c.id !== action.payload);
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
    clearProjectData: (state) => {
      state.currentProject = null;
      state.evidence = [];
      state.timeline = [];
      state.causalFactors = [];
      state.error = null;
    },
  },
});

export const {
  setProjects,
  setCurrentProject,
  updateProject,
  removeProject,
  setEvidence,
  addEvidence,
  removeEvidence,
  setTimeline,
  addTimelineEntry,
  updateTimelineEntry,
  removeTimelineEntry,
  setCausalFactors,
  addCausalFactor,
  updateCausalFactor,
  removeCausalFactor,
  setLoading,
  setError,
  clearProjectData,
} = projectSlice.actions;

export default projectSlice.reducer;