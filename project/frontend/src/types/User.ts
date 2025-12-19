/*
    In this file, we define TypeScript interfaces for user-related data structures.
    These include the User object, requests for login, registration, and user updates,
    as well as the authentication response from the backend.
*/

// A user object representing the authenticated user. 
// A user has an ID, email, name, and optional interests.
export interface User {
    user_id: number;
    email: string;
    first_name: string;
    last_name: string;
    interest_keys?: string[] | null;
    interest_text?: string | null;
    suggested_event_ids?: number[] | null;
    theme_preference: string;  // 'light' or 'dark'
}

// A login request requires email and password
export interface LoginRequest {
    email: string;
    password: string;
}

// A registration request requires email, password, first name, last name, and interests
export interface RegisterRequest {
    email: string;
    password: string;
    first_name: string;
    last_name: string;
    interest_keys: string[];
    interest_text?: string;
}

// A user update request may include any of the user fields, all optional
// This is needed for updating user profile information like name, password, and interests
export interface UpdateUserRequest {
    email?: string;
    password?: string;
    first_name?: string;
    last_name?: string;
    interest_keys?: string[];
    interest_text?: string;
    theme_preference?: string;  // 'light' or 'dark'
}

// Response from the backend upon successful authentication
// It includes the access token and the user data
export interface AuthResponse {
    access_token: string;
    token_type: string;
    user: User;
}
