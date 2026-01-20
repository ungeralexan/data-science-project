// src/context/AuthContext.tsx
import { useState, useEffect, useRef, useCallback } from 'react';
import type { ReactNode } from 'react';
import type { User, LoginRequest, RegisterRequest, UpdateUserRequest, AuthResponse } from '../types/User';
import { AuthContext } from './AuthContextType';
import type { AuthContextType, RecommendationResponse, Theme } from './AuthContextType';
import { API_BASE_URL, STORAGE_KEYS, TIMEOUTS } from '../config';

// Theme storage key (from centralized config)
const THEME_KEY = STORAGE_KEYS.THEME;

/*
    In this file, we implement the AuthProvider component that uses React Context
    to manage authentication state across the application.

    Included Functions:

    - login: Authenticates a user and stores the token and user info.
    - register: Registers a new user and stores the token and user info.
    - logout: Clears the authentication token and user info.
    - updateUser: Updates the user's profile information.
    - deleteAccount: Deletes the user's account.
    - toggleLike: Toggles the like status for an event.
    - isEventLiked: Checks if an event is liked by the current user.
    - toggleGoing: Toggles the going status for an event.
    - isEventGoing: Checks if an event is marked as going by the current user.
    - toggleTheme: Switches between light and dark themes.
    - triggerRecommendations: Requests event recommendations from the backend.

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

// Token storage key (from centralized config)
const TOKEN_KEY = STORAGE_KEYS.AUTH_TOKEN;
const RECO_COOLDOWN_KEY = STORAGE_KEYS.RECOMMENDATION_COOLDOWN_UNTIL;

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
    
    // Recommendation-related state
    const [isRecommendationLoading, setIsRecommendationLoading] = useState(false);
    const [recommendationCooldownRemaining, setRecommendationCooldownRemaining] = useState(0);
    const cooldownIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

    // Theme state - initialize from localStorage or default to 'light'
    const [theme, setThemeState] = useState<Theme>(() => {
        const stored = localStorage.getItem(THEME_KEY);
        return (stored === 'dark' || stored === 'light') ? stored : 'light';
    });

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
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    // ------- Theme Management -------

    // Apply theme class to document body whenever theme changes
    useEffect(() => {
        document.body.classList.remove('theme-light', 'theme-dark');
        document.body.classList.add(`theme-${theme}`);
        localStorage.setItem(THEME_KEY, theme);
    }, [theme]);

    // Sync theme from user data when user logs in
    useEffect(() => {
        if (user) {
            const userTheme = (user.theme_preference === 'dark' || user.theme_preference === 'light') 
                ? user.theme_preference 
                : 'light';
            setThemeState(userTheme as Theme);
        }
    }, [user]);

    // Toggle theme and save to backend if logged in
    const toggleTheme = useCallback(async () => {
        const newTheme = theme === 'light' ? 'dark' : 'light';
        setThemeState(newTheme);
        
        // Keep user object in sync immediately to avoid future updates overwriting the theme
        setUser(prev => prev ? { ...prev, theme_preference: newTheme } : prev);
        
        // Save to backend if user is logged in
        if (token) {
            try {
                await fetch(`${API_BASE_URL}/api/auth/me`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`,
                    },

                    body: JSON.stringify({ theme_preference: newTheme }),
                });
            } catch (error) {
                console.error('Failed to save theme preference:', error);
            }
        }
    }, [theme, token]);

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

    // Toggle going status for an event
    const toggleGoing = async (
        eventId: string,
        eventType: "main_event" | "sub_event" = "main_event"
        ): Promise<{ going_count: number; isGoing: boolean }> => {
        
        // Ensure user is authenticated
        if (!token) throw new Error("Not authenticated");

        // Determine if the event is currently marked as going
        const currentlyGoing = goingEventIds.includes(eventId);

        // Set the appropriate endpoint based on current going status
        const endpoint = currentlyGoing
            ? `${API_BASE_URL}/api/events/${eventType}/${eventId}/ungoing`
            : `${API_BASE_URL}/api/events/${eventType}/${eventId}/going`;

        // Make the API request to toggle going status
        const response = await fetch(endpoint, {
            method: "POST",
            headers: { Authorization: `Bearer ${token}` },
        });

        // Handle non-OK responses
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || "Failed to toggle going");
        }

        const data = await response.json();
        const newIsGoing = !currentlyGoing;

        // Update local goingEventIds state
        setGoingEventIds((prev) =>
            newIsGoing ? [...prev, eventId] : prev.filter((id) => id !== eventId)
        );

        return { going_count: data.going_count, isGoing: newIsGoing };
    };

    const isEventGoing = (eventId: string) => goingEventIds.includes(eventId);


    // ------- Recommendation Functions -------

    // Start the cooldown timer and save expiry to localStorage to persist across page reloads
    const startCooldownTimer = useCallback((targetExpiryMs?: number) => {
        const now = Date.now();
        const target = targetExpiryMs ?? now + TIMEOUTS.RECOMMENDATION_COOLDOWN_MS;
        const remainingSeconds = Math.max(0, Math.ceil((target - now) / 1000));

        // Store expiry time in localStorage
        localStorage.setItem(RECO_COOLDOWN_KEY, String(target));
        setRecommendationCooldownRemaining(remainingSeconds);

        // If remaining time is zero or less, clear cooldown
        if (remainingSeconds <= 0) {
            localStorage.removeItem(RECO_COOLDOWN_KEY);
            return;
        }

        // Clear any existing interval
        if (cooldownIntervalRef.current) {
            clearInterval(cooldownIntervalRef.current);
        }

        // Set up interval to update remaining time every second
        cooldownIntervalRef.current = setInterval(() => {

            // Calculate seconds left
            const secondsLeft = Math.max(0, Math.ceil((target - Date.now()) / 1000));
            setRecommendationCooldownRemaining(secondsLeft);

            // If cooldown has expired, clear interval and localStorage
            if (secondsLeft <= 0) {
                if (cooldownIntervalRef.current) {
                    clearInterval(cooldownIntervalRef.current);
                    cooldownIntervalRef.current = null;
                }

                localStorage.removeItem(RECO_COOLDOWN_KEY);
            }
        }, 1000);
    }, []);

    // Restore recommendation cooldown from localStorage on mount
    useEffect(() => {
        const storedExpiry = localStorage.getItem(RECO_COOLDOWN_KEY);

        if (!storedExpiry) return;

        const parsed = Number.parseInt(storedExpiry, 10);

        if (Number.isNaN(parsed)) {
            localStorage.removeItem(RECO_COOLDOWN_KEY);
            return;
        }

        if (parsed > Date.now()) {
            startCooldownTimer(parsed);
        } else {
            localStorage.removeItem(RECO_COOLDOWN_KEY);
        }

    }, [startCooldownTimer]);

    // Cleanup cooldown timer on unmount
    useEffect(() => {
        return () => {
            if (cooldownIntervalRef.current) {
                clearInterval(cooldownIntervalRef.current);
            }
        };
    }, []);

    // Trigger on-demand event recommendations
    const triggerRecommendations = async (): Promise<RecommendationResponse> => {
        if (!token) {
            throw new Error('Not authenticated');
        }

        // Start the cooldown timer immediately
        startCooldownTimer();
        setIsRecommendationLoading(true);

        try {
            const response = await fetch(`${API_BASE_URL}/api/auth/generate-recommendations`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
            });

            const data: RecommendationResponse = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'Failed to generate recommendations');
            }

            // Update user's suggested_event_ids in state
            if (user) {
                setUser({
                    ...user,
                    suggested_event_ids: data.recommended_event_ids,
                });
            }

            return data;
        } catch (error) {
            console.error('Error generating recommendations:', error);
            throw error;
        } finally {
            setIsRecommendationLoading(false);
        }
    };

    // ------- Context Value -------

    // value = AuthContextType object to provide to children components
    const value: AuthContextType = {
        user,
        token,
        isAuthenticated: !!user && !!token,
        isLoading,
        likedEventIds,
        goingEventIds,
        login,
        register,
        logout,
        updateUser,
        deleteAccount,
        toggleLike,
        toggleGoing,
        toggleTheme,
        isEventLiked,
        isEventGoing,
        triggerRecommendations,
        isRecommendationLoading,
        recommendationCooldownRemaining,
        theme,
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
