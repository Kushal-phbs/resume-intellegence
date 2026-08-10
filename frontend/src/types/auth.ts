// Mirrors backend/app/schemas/auth.py and backend/app/enums/auth.py exactly.

export type UserRole = "user" | "admin";

export interface RegisterRequest {
  email: string;
  password: string; // 8-128 chars
  full_name: string; // 1-255 chars
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
}

export interface CurrentUserResponse {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}
