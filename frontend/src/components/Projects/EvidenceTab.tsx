import React from 'react';
import { Box, Typography, Paper, Button, Alert } from '@mui/material';
import { Add as AddIcon } from '@mui/icons-material';

interface EvidenceTabProps {
  projectId: string;
}

const EvidenceTab: React.FC<EvidenceTabProps> = ({ projectId }) => {
  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h6">Evidence Files</Typography>
        <Button variant="contained" startIcon={<AddIcon />}>
          Upload Evidence
        </Button>
      </Box>
      
      <Paper sx={{ p: 3 }}>
        <Alert severity="info">
          Evidence management functionality coming soon.
        </Alert>
      </Paper>
    </Box>
  );
};

export default EvidenceTab;