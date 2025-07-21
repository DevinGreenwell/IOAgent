import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Paper,
  Typography,
  Tabs,
  Tab,
  CircularProgress,
  Button,
  IconButton,
  Breadcrumbs,
  Link,
  Alert,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Edit as EditIcon,
  Download as DownloadIcon,
  Assessment as AssessmentIcon,
} from '@mui/icons-material';
import { useProject } from '../../hooks/useProjects';
import ProjectOverview from '../../components/Projects/ProjectOverview';
import EvidenceTab from '../../components/Projects/EvidenceTab';
import TimelineTab from '../../components/Projects/TimelineTab';
import CausalFactorsTab from '../../components/Projects/CausalFactorsTab';
import ReportsTab from '../../components/Projects/ReportsTab';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`project-tabpanel-${index}`}
      aria-labelledby={`project-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

const ProjectDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [tabValue, setTabValue] = React.useState(0);
  
  const { data: project, isLoading, error } = useProject(id!);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  if (error || !project) {
    return (
      <Box>
        <Alert severity="error" sx={{ mb: 3 }}>
          {error?.message || 'Project not found'}
        </Alert>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/projects')}
        >
          Back to Projects
        </Button>
      </Box>
    );
  }

  return (
    <Box>
      <Box mb={3}>
        <Breadcrumbs aria-label="breadcrumb">
          <Link
            underline="hover"
            color="inherit"
            href="#"
            onClick={(e) => {
              e.preventDefault();
              navigate('/dashboard');
            }}
          >
            Dashboard
          </Link>
          <Link
            underline="hover"
            color="inherit"
            href="#"
            onClick={(e) => {
              e.preventDefault();
              navigate('/projects');
            }}
          >
            Projects
          </Link>
          <Typography color="text.primary">{project.name}</Typography>
        </Breadcrumbs>
      </Box>

      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box display="flex" alignItems="center" gap={2}>
          <IconButton onClick={() => navigate('/projects')}>
            <ArrowBackIcon />
          </IconButton>
          <Typography variant="h4">{project.name}</Typography>
        </Box>
        <Box display="flex" gap={1}>
          <Button
            variant="outlined"
            startIcon={<EditIcon />}
            onClick={() => navigate(`/projects/${id}/edit`)}
          >
            Edit
          </Button>
          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
          >
            Export
          </Button>
          <Button
            variant="contained"
            startIcon={<AssessmentIcon />}
            onClick={() => navigate(`/projects/${id}/roi`)}
          >
            Generate ROI
          </Button>
        </Box>
      </Box>

      <Paper sx={{ width: '100%' }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={handleTabChange} aria-label="project tabs">
            <Tab label="Overview" />
            <Tab label="Evidence" />
            <Tab label="Timeline" />
            <Tab label="Causal Factors" />
            <Tab label="Reports" />
          </Tabs>
        </Box>

        <TabPanel value={tabValue} index={0}>
          <ProjectOverview project={project} />
        </TabPanel>
        <TabPanel value={tabValue} index={1}>
          <EvidenceTab projectId={project.id} />
        </TabPanel>
        <TabPanel value={tabValue} index={2}>
          <TimelineTab projectId={project.id} />
        </TabPanel>
        <TabPanel value={tabValue} index={3}>
          <CausalFactorsTab projectId={project.id} />
        </TabPanel>
        <TabPanel value={tabValue} index={4}>
          <ReportsTab projectId={project.id} />
        </TabPanel>
      </Paper>
    </Box>
  );
};

export default ProjectDetail;