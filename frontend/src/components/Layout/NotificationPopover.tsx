import React from 'react';
import {
  Popover,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Typography,
  Box,
  IconButton,
  Divider,
  Button,
} from '@mui/material';
import {
  Info as InfoIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  CheckCircle as SuccessIcon,
  Close as CloseIcon,
  ClearAll as ClearAllIcon,
} from '@mui/icons-material';
import { formatDistanceToNow } from 'date-fns';
import { useAppDispatch, useAppSelector } from '../../store';
import { removeNotification, clearNotifications } from '../../store/slices/uiSlice';

interface NotificationPopoverProps {
  anchorEl: HTMLElement | null;
  open: boolean;
  onClose: () => void;
}

interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
  timestamp: number;
  read?: boolean;
}

const NotificationPopover: React.FC<NotificationPopoverProps> = ({
  anchorEl,
  open,
  onClose,
}) => {
  const dispatch = useAppDispatch();
  const { notifications } = useAppSelector((state) => state.ui);

  const getIcon = (type: Notification['type']) => {
    switch (type) {
      case 'success':
        return <SuccessIcon color="success" />;
      case 'error':
        return <ErrorIcon color="error" />;
      case 'warning':
        return <WarningIcon color="warning" />;
      case 'info':
      default:
        return <InfoIcon color="info" />;
    }
  };

  const handleRemove = (id: string) => {
    dispatch(removeNotification(id));
  };

  const handleClearAll = () => {
    dispatch(clearNotifications());
  };

  return (
    <Popover
      open={open}
      anchorEl={anchorEl}
      onClose={onClose}
      anchorOrigin={{
        vertical: 'bottom',
        horizontal: 'right',
      }}
      transformOrigin={{
        vertical: 'top',
        horizontal: 'right',
      }}
      PaperProps={{
        sx: { width: 350, maxHeight: 400 }
      }}
    >
      <Box sx={{ p: 2, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Typography variant="h6">Notifications</Typography>
        {notifications.length > 0 && (
          <Button
            size="small"
            startIcon={<ClearAllIcon />}
            onClick={handleClearAll}
          >
            Clear All
          </Button>
        )}
      </Box>
      <Divider />
      
      {notifications.length === 0 ? (
        <Box sx={{ p: 3, textAlign: 'center' }}>
          <Typography color="text.secondary">No notifications</Typography>
        </Box>
      ) : (
        <List sx={{ maxHeight: 300, overflow: 'auto' }}>
          {notifications.map((notification) => (
            <React.Fragment key={notification.id}>
              <ListItem
                secondaryAction={
                  <IconButton edge="end" onClick={() => handleRemove(notification.id)}>
                    <CloseIcon fontSize="small" />
                  </IconButton>
                }
                sx={{
                  backgroundColor: notification.read ? 'transparent' : 'action.hover',
                }}
              >
                <ListItemIcon>{getIcon(notification.type)}</ListItemIcon>
                <ListItemText
                  primary={notification.message}
                  secondary={formatDistanceToNow(notification.timestamp, { addSuffix: true })}
                  primaryTypographyProps={{
                    variant: 'body2',
                    sx: {
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      display: '-webkit-box',
                      WebkitLineClamp: 2,
                      WebkitBoxOrient: 'vertical',
                    }
                  }}
                />
              </ListItem>
              <Divider />
            </React.Fragment>
          ))}
        </List>
      )}
    </Popover>
  );
};

export default NotificationPopover;