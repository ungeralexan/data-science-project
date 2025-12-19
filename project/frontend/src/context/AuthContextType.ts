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
    - toggleLike: A function to like or unlike an event.
    - isEventLiked: A function to check if an event is liked by the user.
    - triggerRecommendations: A function to trigger on-demand event recommendations.
    - isRecommendationLoading: A boolean indicating if recommendations are being generated.
    - recommendationCooldownRemaining: Seconds remaining before user can request recommendations again.
    - theme: The current theme ('light' or 'dark').
    - toggleTheme: A function to toggle between light and dark themes.
*/

// Theme type definition
export type Theme = 'light' | 'dark';

// Response from the recommendation API
export interface RecommendationResponse {
    success: boolean;
    message: string;
    has_events: boolean;
    recommended_event_ids: number[];
}

export interface AuthContextType {
    user: User | null; 
    token: string | null;
    isAuthenticated: boolean;
    isLoading: boolean;
    likedEventIds: string[];  // Array of event IDs that the user has liked
    goingEventIds: string[];
    login: (data: LoginRequest) => Promise<void>;
    register: (data: RegisterRequest) => Promise<void>;
    logout: () => void;
    updateUser: (data: UpdateUserRequest) => Promise<void>;
    deleteAccount: () => Promise<void>;
    toggleLike: (eventId: string, eventType?: "main_event" | "sub_event") => Promise<{ like_count: number; isLiked: boolean }>;  // Toggle like status for an event
    isEventLiked: (eventId: string) => boolean;  // Check if an event is liked
    toggleGoing: (eventId: string, eventType?: "main_event" | "sub_event") => Promise<{ going_count: number; isGoing: boolean }>;
    isEventGoing: (eventId: string) => boolean;
    triggerRecommendations: () => Promise<RecommendationResponse>;  // Trigger on-demand recommendations
    isRecommendationLoading: boolean;  // Whether recommendations are being generated
    recommendationCooldownRemaining: number;  // Seconds remaining in cooldown
    theme: Theme;  // Current theme ('light' or 'dark')
    toggleTheme: () => void;  // Toggle between light and dark themes
}

/*
    Create the AuthContext with the defined type as React Context

    A react Context allows us to share state (like authentication info).
    It contains the AuthContext.Provider property.
    This is a component that provides values to its child components.

*/
export const AuthContext = createContext<AuthContextType | undefined>(undefined);
