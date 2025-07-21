import React from 'react';
import { Box, Typography, Paper, Alert } from '@mui/material';

const Timeline: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Timeline Analysis
      </Typography>
      <Paper sx={{ p: 3 }}>
        <Alert severity="info">
          Timeline visualization coming soon. Access timeline features through individual projects.
        </Alert>
      </Paper>
    </Box>
  );
};

export default Timeline;