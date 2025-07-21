import React, { useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Button,
  Chip,
  LinearProgress,
} from '@mui/material';
import {
  Folder as FolderIcon,
  Assessment as AssessmentIcon,
  Timeline as TimelineIcon,
  Security as SecurityIcon,
  Add as AddIcon,
  TrendingUp as TrendingUpIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAppSelector } from '../../store';
import { formatDistanceToNow } from 'date-fns';
import useProjects from '../../hooks/useProjects';

interface StatCard {
  title: string;
  value: number | string;
  icon: React.ReactNode;
  color: string;
  trend?: number;
}

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAppSelector((state) => state.auth);
  const { data: projectsData, isLoading } = useProjects({ page: 1, per_page: 5 });

  const stats: StatCard[] = [
    {
      title: 'Total Projects',
      value: projectsData?.pagination.total || 0,
      icon: <FolderIcon />,
      color: '#1976d2',
      trend: 12,
    },
    {
      title: 'Active Investigations',
      value: projectsData?.data.filter(p => p.status === 'active').length || 0,
      icon: <AssessmentIcon />,
      color: '#388e3c',
    },
    {
      title: 'Timeline Entries',
      value: '142',
      icon: <TimelineIcon />,
      color: '#f57c00',
      trend: -5,
    },
    {
      title: 'Risk Assessments',
      value: '28',
      icon: <SecurityIcon />,
      color: '#d32f2f',
      trend: 8,
    },
  ];

  return (
    <Box>
      <Box mb={4}>
        <Typography variant="h4" gutterBottom>
          Welcome back, {user?.first_name || 'Investigator'}
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Here's an overview of your marine casualty investigations
        </Typography>
      </Box>

      <Grid container spacing={3} mb={4}>
        {stats.map((stat, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" justifyContent="space-between">
                  <Box>
                    <Typography color="text.secondary" gutterBottom variant="body2">
                      {stat.title}
                    </Typography>
                    <Typography variant="h4" component="div">
                      {stat.value}
                    </Typography>
                    {stat.trend && (
                      <Box display="flex" alignItems="center" mt={1}>
                        <TrendingUpIcon
                          fontSize="small"
                          sx={{ color: stat.trend > 0 ? 'success.main' : 'error.main' }}
                        />
                        <Typography
                          variant="body2"
                          sx={{ color: stat.trend > 0 ? 'success.main' : 'error.main' }}
                        >
                          {Math.abs(stat.trend)}% from last month
                        </Typography>
                      </Box>
                    )}
                  </Box>
                  <Box
                    sx={{
                      backgroundColor: stat.color,
                      borderRadius: 2,
                      p: 1,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    {React.cloneElement(stat.icon as React.ReactElement, {
                      sx: { color: 'white', fontSize: 30 },
                    })}
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 2 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">Recent Projects</Typography>
              <Button
                startIcon={<AddIcon />}
                variant="contained"
                onClick={() => navigate('/projects/new')}
              >
                New Project
              </Button>
            </Box>
            {isLoading ? (
              <LinearProgress />
            ) : (
              <List>
                {projectsData?.data.map((project) => (
                  <ListItem
                    key={project.id}
                    button
                    onClick={() => navigate(`/projects/${project.id}`)}
                  >
                    <ListItemIcon>
                      <FolderIcon />
                    </ListItemIcon>
                    <ListItemText
                      primary={project.name}
                      secondary={
                        <Box component="span">
                          <Typography component="span" variant="body2" color="text.secondary">
                            {project.vessel_info?.vessel_name || 'Unknown Vessel'} •{' '}
                            {formatDistanceToNow(new Date(project.created_at), { addSuffix: true })}
                          </Typography>
                        </Box>
                      }
                    />
                    <Chip
                      label={project.status || 'active'}
                      size="small"
                      color={project.status === 'active' ? 'success' : 'default'}
                    />
                  </ListItem>
                ))}
              </List>
            )}
          </Paper>
        </Grid>

        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Recent Activity
            </Typography>
            <List dense>
              <ListItem>
                <ListItemText
                  primary="New evidence uploaded"
                  secondary="Project Alpha - 2 hours ago"
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="Timeline updated"
                  secondary="Project Beta - 5 hours ago"
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="ROI generated"
                  secondary="Project Gamma - 1 day ago"
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="Causal analysis completed"
                  secondary="Project Delta - 2 days ago"
                />
              </ListItem>
            </List>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;