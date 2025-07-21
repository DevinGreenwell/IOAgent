import React from 'react';
import { Box, Grid, Typography, Paper, Chip } from '@mui/material';
import { Project } from '../../types';
import { format } from 'date-fns';

interface ProjectOverviewProps {
  project: Project;
}

const ProjectOverview: React.FC<ProjectOverviewProps> = ({ project }) => {
  return (
    <Grid container spacing={3}>
      <Grid item xs={12} md={6}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Project Information
          </Typography>
          <Box sx={{ mt: 2 }}>
            <Typography variant="body2" color="text.secondary">
              Name
            </Typography>
            <Typography variant="body1" gutterBottom>
              {project.name}
            </Typography>
            
            <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
              Description
            </Typography>
            <Typography variant="body1" gutterBottom>
              {project.description || 'No description provided'}
            </Typography>
            
            <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
              Status
            </Typography>
            <Chip 
              label={project.status || 'active'} 
              color={project.status === 'active' ? 'success' : 'default'}
              size="small"
            />
          </Box>
        </Paper>
      </Grid>
      
      <Grid item xs={12} md={6}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Vessel Information
          </Typography>
          {project.vessel_info ? (
            <Box sx={{ mt: 2 }}>
              <Typography variant="body2" color="text.secondary">
                Vessel Name
              </Typography>
              <Typography variant="body1" gutterBottom>
                {project.vessel_info.vessel_name}
              </Typography>
              
              <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                IMO Number
              </Typography>
              <Typography variant="body1" gutterBottom>
                {project.vessel_info.imo_number || 'Not provided'}
              </Typography>
              
              <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                Vessel Type
              </Typography>
              <Typography variant="body1" gutterBottom>
                {project.vessel_info.vessel_type || 'Not specified'}
              </Typography>
              
              <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                Flag State
              </Typography>
              <Typography variant="body1" gutterBottom>
                {project.vessel_info.flag_state || 'Not specified'}
              </Typography>
            </Box>
          ) : (
            <Typography variant="body2" color="text.secondary">
              No vessel information available
            </Typography>
          )}
        </Paper>
      </Grid>
      
      <Grid item xs={12}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Incident Information
          </Typography>
          {project.incident_info ? (
            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid item xs={12} sm={6} md={3}>
                <Typography variant="body2" color="text.secondary">
                  Incident Date
                </Typography>
                <Typography variant="body1">
                  {project.incident_info.incident_date 
                    ? format(new Date(project.incident_info.incident_date), 'PPP')
                    : 'Not specified'}
                </Typography>
              </Grid>
              
              <Grid item xs={12} sm={6} md={3}>
                <Typography variant="body2" color="text.secondary">
                  Incident Type
                </Typography>
                <Typography variant="body1">
                  {project.incident_info.incident_type || 'Not specified'}
                </Typography>
              </Grid>
              
              <Grid item xs={12} sm={6} md={3}>
                <Typography variant="body2" color="text.secondary">
                  Location
                </Typography>
                <Typography variant="body1">
                  {project.incident_info.location || 'Not specified'}
                </Typography>
              </Grid>
              
              <Grid item xs={12} sm={6} md={3}>
                <Typography variant="body2" color="text.secondary">
                  Severity
                </Typography>
                <Chip 
                  label={project.incident_info.severity || 'unknown'} 
                  color={
                    project.incident_info.severity === 'catastrophic' ? 'error' :
                    project.incident_info.severity === 'major' ? 'warning' :
                    'default'
                  }
                  size="small"
                />
              </Grid>
              
              {((project.incident_info.injuries && project.incident_info.injuries > 0) || 
                (project.incident_info.fatalities && project.incident_info.fatalities > 0)) && (
                <>
                  <Grid item xs={12} sm={6} md={3}>
                    <Typography variant="body2" color="text.secondary">
                      Injuries
                    </Typography>
                    <Typography variant="body1">
                      {project.incident_info.injuries}
                    </Typography>
                  </Grid>
                  
                  <Grid item xs={12} sm={6} md={3}>
                    <Typography variant="body2" color="text.secondary">
                      Fatalities
                    </Typography>
                    <Typography variant="body1">
                      {project.incident_info.fatalities}
                    </Typography>
                  </Grid>
                </>
              )}
            </Grid>
          ) : (
            <Typography variant="body2" color="text.secondary">
              No incident information available
            </Typography>
          )}
        </Paper>
      </Grid>
    </Grid>
  );
};

export default ProjectOverview;