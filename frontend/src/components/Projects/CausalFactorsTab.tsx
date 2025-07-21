import React from 'react';
import { Box, Typography, Paper, Button, Alert } from '@mui/material';
import { Add as AddIcon } from '@mui/icons-material';

interface CausalFactorsTabProps {
  projectId: string;
}

const CausalFactorsTab: React.FC<CausalFactorsTabProps> = ({ projectId }) => {
  // TODO: Implement causal factors functionality for project: {projectId}
  // eslint-disable-next-line no-console
  console.log('Loading causal factors for project:', projectId);
  
  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h6">Causal Factors</Typography>
        <Button variant="contained" startIcon={<AddIcon />}>
          Add Causal Factor
        </Button>
      </Box>
      
      <Paper sx={{ p: 3 }}>
        <Alert severity="info">
          Causal factors analysis functionality coming soon for project {projectId}.
        </Alert>
      </Paper>
    </Box>
  );
};

export default CausalFactorsTab;