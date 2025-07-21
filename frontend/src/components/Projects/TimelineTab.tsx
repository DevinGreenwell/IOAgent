import React from 'react';
import { Box, Typography, Paper, Button, Alert } from '@mui/material';
import { Add as AddIcon } from '@mui/icons-material';

interface TimelineTabProps {
  projectId: string;
}

const TimelineTab: React.FC<TimelineTabProps> = ({ projectId }) => {
  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h6">Timeline</Typography>
        <Button variant="contained" startIcon={<AddIcon />}>
          Add Timeline Entry
        </Button>
      </Box>
      
      <Paper sx={{ p: 3 }}>
        <Alert severity="info">
          Timeline functionality coming soon.
        </Alert>
      </Paper>
    </Box>
  );
};

export default TimelineTab;