export interface User {
  id: string;
  email: string;
  username: string;
  display_name: string;
  timezone: string;
}

export interface TokenResponse {
  access_token: string;
  token_type?: string;
}

export interface LoginRequest {
  identifier: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  display_name: string;
  username: string;
}

export interface UserUpdateRequest {
  display_name?: string;
  timezone?: string;
}

export interface UsernameAvailability {
  username: string;
  available: boolean;
  reason: string | null;
}

export interface UsernameChangeRequest {
  username: string;
  reason?: string | null;
}

export interface PublicUser {
  username: string;
  display_name: string;
}

export interface UsernameHistoryEntry {
  id: string;
  old_username: string;
  new_username: string;
  changed_at: string;
  changed_by: string;
  reason: string | null;
}
