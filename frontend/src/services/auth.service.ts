import api from './api';
import { LoginCredentials, RegisterData, AuthTokens, User } from '../types';

class AuthService {
  async login(credentials: LoginCredentials): Promise<{ tokens: AuthTokens; user: User }> {
    const response = await api.post('/auth/login', credentials);
    return {
      tokens: {
        access_token: response.data.access_token,
        refresh_token: response.data.refresh_token,
      },
      user: response.data.user,
    };
  }

  async register(data: RegisterData): Promise<{ user: User }> {
    const response = await api.post('/auth/register', data);
    return response.data;
  }

  async logout(): Promise<void> {
    try {
      await api.post('/auth/logout');
    } catch (error) {
      // Ignore logout errors
    }
  }

  async refreshToken(refreshToken: string): Promise<AuthTokens> {
    const response = await api.post(
      '/auth/refresh',
      {},
      {
        headers: {
          Authorization: `Bearer ${refreshToken}`,
        },
      }
    );
    return {
      access_token: response.data.access_token,
      refresh_token: refreshToken, // Keep the same refresh token
    };
  }

  async getCurrentUser(): Promise<User> {
    const response = await api.get('/users/profile');
    return response.data;
  }

  async updateProfile(data: Partial<User>): Promise<User> {
    const response = await api.put('/users/profile', data);
    return response.data;
  }

  async changePassword(oldPassword: string, newPassword: string): Promise<void> {
    await api.put('/users/change-password', {
      old_password: oldPassword,
      new_password: newPassword,
    });
  }
}

export default new AuthService();