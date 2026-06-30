export interface User {
  id: string;
  email: string;
  display_name: string;
  timezone: string;
}

export interface TokenResponse {
  access_token: string;
  token_type?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  display_name: string;
}

export interface UserUpdateRequest {
  display_name?: string;
  timezone?: string;
}
