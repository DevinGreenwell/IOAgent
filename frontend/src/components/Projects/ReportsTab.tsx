import React from 'react';
import { Box, Typography, Paper, Button, Alert } from '@mui/material';
import { Download as DownloadIcon, Assessment as AssessmentIcon } from '@mui/icons-material';

interface ReportsTabProps {
  projectId: string;
}

const ReportsTab: React.FC<ReportsTabProps> = ({ projectId }) => {
  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h6">Reports</Typography>
        <Box display="flex" gap={2}>
          <Button variant="outlined" startIcon={<DownloadIcon />}>
            Export Project
          </Button>
          <Button variant="contained" startIcon={<AssessmentIcon />}>
            Generate ROI
          </Button>
        </Box>
      </Box>
      
      <Paper sx={{ p: 3 }}>
        <Alert severity="info">
          Report generation functionality coming soon.
        </Alert>
      </Paper>
    </Box>
  );
};

export default ReportsTab;