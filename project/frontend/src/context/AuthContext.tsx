// src/context/AuthContext.tsx
import { useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import type { User, LoginRequest, RegisterRequest, UpdateUserRequest, AuthResponse } from '../types/User';
import { AuthContext } from './AuthContextType';
import type { AuthContextType } from './AuthContextType';
import { API_BASE_URL } from '../config';

/*
    In this file, we implement the AuthProvider component that uses React Context
    to manage authentication state across the application.

    Included Functions:

    - fetchCurrentUser: Validates the token and fetches user info on app startup.
    - login: Authenticates the user and stores the token and user info.
    - register: Registers a new user and stores the token and user info.
    - logout: Clears the authentication state.
    - updateUser: Updates user profile information.
    - deleteAccount: Deletes the user account.

    The AuthProvider wraps the application and provides authentication context
    to all child components, allowing them to access user authentication state
    and functions.

    <---- localStorage ---->

    We use localStorage to persist the authentication token across page reloads.
    This allows users to remain logged in even if they refresh the browser.
    The token is stored in client-side data storage.

    Key localStorage methods used:

    localStorage.setItem(key, value): Stores a value under the specified key.
    localStorage.getItem(key): Retrieves the value for the specified key.
    localStorage.removeItem(key): Removes the specified key and its value.
    const value = localStorage.getItem('key'): Retrieves the value stored under 'key'.
*/

// Token storage key
const TOKEN_KEY = 'auth_token';

// A ReactNode can be anything (Strings, numbers, arrays, null, ....) 
// Children are the nested components inside AuthProvider (Routes, Pages, etc)
interface AuthProviderProps {
    children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {

    // STATE - user, token, loading (What we need to track for authentication)
    const [user, setUser] = useState<User | null>(null);
    const [token, setToken] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [likedEventIds, setLikedEventIds] = useState<string[]>([]);
    const [goingEventIds, setGoingEventIds] = useState<string[]>([]);

    // ------- Startup -------

    // useEffect runs after the component is added to the DOM
    // checks for existing token in localStorage on mount
    useEffect(() => {

        // Check localStorage for existing token
        const storedToken = localStorage.getItem(TOKEN_KEY);

        if (storedToken) {

            // Set token state from localStorage
            setToken(storedToken);
            // Validate token and get user info
            fetchCurrentUser(storedToken);
        } else {
            setIsLoading(false);
        }
    }, []);

    // ------- Auth Functions -------

    // Fetch liked events from the backend
    const fetchLikedEvents = async (authToken: string) => {
        try {
            const response = await fetch(`${API_BASE_URL}/api/auth/liked-events`, {
                method: 'GET',
                headers: { 'Authorization': `Bearer ${authToken}` },
            });

            if (response.ok) { 
                const likedIds: Array<string | number> = await response.json();
                setLikedEventIds(likedIds.map(String));
            }
        } catch (error) {
            console.error('Error fetching liked events:', error);
        }
    };

    // Fetch going events from the backend
    const fetchGoingEvents = async (authToken: string) => {
        try {
            const response = await fetch(`${API_BASE_URL}/api/auth/going-events`, {
            method: "GET",
            headers: { Authorization: `Bearer ${authToken}` },
            });
            if (response.ok) {
            const ids: Array<string | number> = await response.json();
            setGoingEventIds(ids.map(String));
            }
        } catch (e) {
            console.error("Error fetching going events:", e);
        }
    };

    
    // Validate current user info using the stored token
    // async function allows us to use await inside it
    
    const fetchCurrentUser = async (authToken: string) => {
        try {

            // Call the backend to get user info
            // fetch is browser built-in function to make HTTP requests
            const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
                method: 'GET',
                // We manually have to set the Authorization header to include the token
                // Otherwise, the backend won't know it. 
                headers: {'Authorization': `Bearer ${authToken}`,},
            });

            // If the response is OK, parse the user data
            if (response.ok) {

                // Response Format = User from User.ts
                const userData: User = await response.json();

                setUser(userData);
                setToken(authToken);

                // Fetch liked events after successful authentication
                await fetchLikedEvents(authToken);

                // Fetch going events
                await fetchGoingEvents(authToken);

            // If response not ok, clear invalid token
            } else {
                // Token is invalid or expired
                localStorage.removeItem(TOKEN_KEY);
                setToken(null);
                setUser(null);
                setLikedEventIds([]);
                setGoingEventIds([]);
            }
        } catch (error) {
            console.error('Error fetching current user:', error);
            localStorage.removeItem(TOKEN_KEY);
            setToken(null);
            setUser(null);
            setLikedEventIds([]);
            setGoingEventIds([]);
        } finally {
            setIsLoading(false);
        }
    };

    // Login function - authenticates user and stores token and user info
    const login = async (data: LoginRequest): Promise<void> => {

        // Call the backend login endpoint and pass the login data
        const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
            method: 'POST', //Sending data
            headers: {
                'Content-Type': 'application/json', //Tell backend we are sending JSON
            },

            body: JSON.stringify(data), // Convert data to JSON string
        });

        // If login fails, throw an error
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Login failed');
        }

        // If login successful, parse the auth response as type AuthResponse
        const authResponse: AuthResponse = await response.json();

        // Store the token in localStorage and update state
        localStorage.setItem(TOKEN_KEY, authResponse.access_token);

        setToken(authResponse.access_token);
        setUser(authResponse.user);

        // Fetch liked events after login
        await fetchLikedEvents(authResponse.access_token);
        
        // Fetch going events after login
        await fetchGoingEvents(authResponse.access_token);

    };

    // Register function - creates new user and stores token and user info
    const register = async (data: RegisterRequest): Promise<void> => {
        const response = await fetch(`${API_BASE_URL}/api/auth/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },

            body: JSON.stringify(data),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Registration failed');
        }

        const authResponse: AuthResponse = await response.json();

        localStorage.setItem(TOKEN_KEY, authResponse.access_token);

        setToken(authResponse.access_token);
        setUser(authResponse.user);

        // New user has no liked events yet
        setLikedEventIds([]);

        // New user has no going events yet
        setGoingEventIds([]);
    };

    // Logout function - clears token and user info
    const logout = () => {
        localStorage.removeItem(TOKEN_KEY);
        setToken(null);
        setUser(null);
        setLikedEventIds([]);
        setGoingEventIds([]);
    };

    // Update user profile information
    const updateUser = async (data: UpdateUserRequest): Promise<void> => {
        if (!token) {
            throw new Error('Not authenticated');
        }

        const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
            method: 'PUT',
            
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`,
            },

            body: JSON.stringify(data),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Update failed');
        }

        const updatedUser: User = await response.json();
        setUser(updatedUser);
    };

    // Delete user account
    const deleteAccount = async (): Promise<void> => {
        if (!token) {
            throw new Error('Not authenticated');
        }

        const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`,
            },
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Delete failed');
        }

        // Clear local state after successful deletion
        localStorage.removeItem(TOKEN_KEY);
        setToken(null);
        setUser(null);
        setLikedEventIds([]);
        setGoingEventIds([]);
    };

    // Toggle like status for an event
    const toggleLike = async (eventId: string, eventType: "main_event" | "sub_event" = "main_event"): Promise<{ like_count: number; isLiked: boolean }> => {
        if (!token) {
            throw new Error('Not authenticated');
        }

        // If event is currently liked, send unlike request, else send like request
        const currentlyLiked = likedEventIds.includes(eventId);

        const endpoint = currentlyLiked
            ? `${API_BASE_URL}/api/events/${eventType}/${eventId}/unlike`
            : `${API_BASE_URL}/api/events/${eventType}/${eventId}/like`;

        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
            },
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to toggle like');
        }

        const data = await response.json();
        const newIsLiked = !currentlyLiked;

        // Update local state
        if (newIsLiked) {
            setLikedEventIds(prev => [...prev, eventId]);
        } else {

            // Remove eventId from likedEventIds
            setLikedEventIds(prev => prev.filter(id => id !== eventId));
        }

        // Return updated like count and new like status
        return { like_count: data.like_count, isLiked: newIsLiked };
    };

    // Check if an event is liked by the current user
    const isEventLiked = (eventId: string): boolean => {
        return likedEventIds.includes(eventId);
    };

    const toggleGoing = async (
        eventId: string,
        eventType: "main_event" | "sub_event" = "main_event"
        ): Promise<{ going_count: number; isGoing: boolean }> => {
        if (!token) throw new Error("Not authenticated");

        const currentlyGoing = goingEventIds.includes(eventId);

        const endpoint = currentlyGoing
            ? `${API_BASE_URL}/api/events/${eventType}/${eventId}/ungoing`
            : `${API_BASE_URL}/api/events/${eventType}/${eventId}/going`;

        const response = await fetch(endpoint, {
            method: "POST",
            headers: { Authorization: `Bearer ${token}` },
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || "Failed to toggle going");
        }

        const data = await response.json();
        const newIsGoing = !currentlyGoing;

        setGoingEventIds((prev) =>
            newIsGoing ? [...prev, eventId] : prev.filter((id) => id !== eventId)
        );

        return { going_count: data.going_count, isGoing: newIsGoing };
    };

    const isEventGoing = (eventId: string) => goingEventIds.includes(eventId);


    // ------- Context Value -------

    // value = AuthContextType object to provide to children components
    const value: AuthContextType = {
        user,
        token,
        isAuthenticated: !!user && !!token,
        isLoading,
        likedEventIds,
        login,
        register,
        logout,
        updateUser,
        deleteAccount,
        toggleLike,
        isEventLiked,
        goingEventIds,
        toggleGoing,
        isEventGoing,
    };

    // ------- Render -------

    // Provide the AuthContext to child components with AuthContext.Provider
    // That way they can access the auth state and functions.
    return (
        <AuthContext.Provider value={value}>
            {children} {/* Render nested components (Routes, Pages, etc) */}
        </AuthContext.Provider>
    );
}
