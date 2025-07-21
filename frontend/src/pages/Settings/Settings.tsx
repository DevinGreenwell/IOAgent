import React from 'react';
import {
  Box,
  Typography,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Switch,
  Divider,
  Button,
  TextField,
  Grid,
} from '@mui/material';
import { useAppSelector, useAppDispatch } from '../../store';
import { toggleDarkMode } from '../../store/slices/uiSlice';

const Settings: React.FC = () => {
  const dispatch = useAppDispatch();
  const { darkMode } = useAppSelector((state) => state.ui);

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Settings
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ mb: 3 }}>
            <List>
              <ListItem>
                <ListItemText
                  primary="Dark Mode"
                  secondary="Toggle dark/light theme"
                />
                <ListItemSecondaryAction>
                  <Switch
                    edge="end"
                    checked={darkMode}
                    onChange={() => dispatch(toggleDarkMode())}
                  />
                </ListItemSecondaryAction>
              </ListItem>
              <Divider />
              <ListItem>
                <ListItemText
                  primary="Email Notifications"
                  secondary="Receive email updates about projects"
                />
                <ListItemSecondaryAction>
                  <Switch edge="end" defaultChecked />
                </ListItemSecondaryAction>
              </ListItem>
              <Divider />
              <ListItem>
                <ListItemText
                  primary="Auto-save"
                  secondary="Automatically save changes while editing"
                />
                <ListItemSecondaryAction>
                  <Switch edge="end" defaultChecked />
                </ListItemSecondaryAction>
              </ListItem>
            </List>
          </Paper>
          
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              API Configuration
            </Typography>
            <TextField
              fullWidth
              label="Anthropic API Key"
              type="password"
              helperText="Your API key is stored securely"
              sx={{ mb: 2 }}
            />
            <Button variant="contained">
              Update API Key
            </Button>
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Data Management
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Export your data or clear cache
            </Typography>
            <Box display="flex" gap={2}>
              <Button variant="outlined">
                Export Data
              </Button>
              <Button variant="outlined" color="warning">
                Clear Cache
              </Button>
            </Box>
          </Paper>
          
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              About IOAgent
            </Typography>
            <Typography variant="body2" paragraph>
              Version: 1.0.0
            </Typography>
            <Typography variant="body2" paragraph>
              IOAgent is a marine casualty investigation system designed for the U.S. Coast Guard.
            </Typography>
            <Typography variant="body2" color="text.secondary">
              © 2024 U.S. Coast Guard. All rights reserved.
            </Typography>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Settings;