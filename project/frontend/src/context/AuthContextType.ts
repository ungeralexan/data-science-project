// src/context/AuthContextType.ts
import { createContext } from 'react';
import type { User, LoginRequest, RegisterRequest, UpdateUserRequest } from '../types/User';

/*
    In this file, we define the context type for authentication.

    The AuthContextType includes:
    - user: The currently authenticated user or null if not authenticated.
    - token: The JWT access token or null if not authenticated.
    - isAuthenticated: A boolean indicating if the user is authenticated.
    - isLoading: A boolean indicating if authentication status is being checked.
    - login: A function to log in a user with email and password.
    - register: A function to register a new user.
    - logout: A function to log out the current user.
    - updateUser: A function to update the current user's information.
    - deleteAccount: A function to delete the current user's account.
*/

export interface AuthContextType {
    user: User | null; 
    token: string | null;
    isAuthenticated: boolean;
    isLoading: boolean;
    likedEventIds: number[];  // Array of event IDs that the user has liked
    login: (data: LoginRequest) => Promise<void>;
    register: (data: RegisterRequest) => Promise<void>;
    logout: () => void;
    updateUser: (data: UpdateUserRequest) => Promise<void>;
    deleteAccount: () => Promise<void>;
    toggleLike: (eventId: number) => Promise<{ like_count: number; isLiked: boolean }>;  // Toggle like status for an event
    isEventLiked: (eventId: number) => boolean;  // Check if an event is liked
}

/*
    Create the AuthContext with the defined type as React Context

    A react Context allows us to share state (like authentication info).
    It contains the AuthContext.Provider property.
    This is a component that provides values to its child components.

*/
export const AuthContext = createContext<AuthContextType | undefined>(undefined);
