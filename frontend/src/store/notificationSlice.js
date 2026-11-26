import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  unreadCount: 0,
  notifications: [],
  loading: false,
};

const notificationSlice = createSlice({
  name: 'notifications',
  initialState,
  reducers: {
    setUnreadCount: (state, action) => {
      state.unreadCount = action.payload;
    },
    decrementUnreadCount: (state) => {
      state.unreadCount = Math.max(0, state.unreadCount - 1);
    },
    clearUnreadCount: (state) => {
      state.unreadCount = 0;
    },
    setNotifications: (state, action) => {
      state.notifications = action.payload;
    },
    markNotificationAsRead: (state, action) => {
      const id = action.payload;
      const target = state.notifications.find((n) => n.id === id);
      if (target && !target.is_read) {
        target.is_read = true;
        state.unreadCount = Math.max(0, state.unreadCount - 1);
      }
    },
  },
});

export const {
  setUnreadCount,
  decrementUnreadCount,
  clearUnreadCount,
  setNotifications,
  markNotificationAsRead,
} = notificationSlice.actions;

export default notificationSlice.reducer;
