import React from 'react';
import { Box, Typography, Paper, Grid, TextField, Button, Avatar } from '@mui/material';
import { useAppSelector } from '../../store';

const Profile: React.FC = () => {
  const { user } = useAppSelector((state) => state.auth);

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Profile
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3, textAlign: 'center' }}>
            <Avatar
              sx={{ width: 120, height: 120, mx: 'auto', mb: 2 }}
              src={user?.avatar_url}
            >
              {user?.first_name?.[0]}{user?.last_name?.[0]}
            </Avatar>
            <Typography variant="h6">
              {user?.first_name} {user?.last_name}
            </Typography>
            <Typography color="text.secondary">
              @{user?.username}
            </Typography>
            {user?.rank && (
              <Typography variant="body2" sx={{ mt: 1 }}>
                {user.rank}
              </Typography>
            )}
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Profile Information
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="First Name"
                  value={user?.first_name || ''}
                  InputProps={{ readOnly: true }}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Last Name"
                  value={user?.last_name || ''}
                  InputProps={{ readOnly: true }}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Email"
                  value={user?.email || ''}
                  InputProps={{ readOnly: true }}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Rank"
                  value={user?.rank || ''}
                  InputProps={{ readOnly: true }}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Badge Number"
                  value={user?.badge_number || ''}
                  InputProps={{ readOnly: true }}
                />
              </Grid>
              <Grid item xs={12}>
                <Button variant="contained">
                  Edit Profile
                </Button>
              </Grid>
            </Grid>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Profile;