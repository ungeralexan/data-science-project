// src/context/ThemeContext.tsx
import { useState, useEffect, useRef, useCallback } from 'react';
import type { ReactNode } from 'react';
import { ThemeContext } from './ThemeContextType';
import type { Theme } from './ThemeContextType';
import { STORAGE_KEYS } from '../config';

/*
    ThemeProvider provides dark mode functionality across the application.
    
    - Stores theme preference in localStorage for persistence
    - Applies theme class to document body
    - Provides toggle function for switching themes
    - Supports saving theme to backend via optional callback (for cross-device sync)
*/

// Theme storage key (from centralized config)
const THEME_KEY = STORAGE_KEYS.THEME;

interface ThemeProviderProps {
    children: ReactNode;
}

export function ThemeProvider({ children }: ThemeProviderProps) {
    // Initialize theme from localStorage or default to 'light'
    const [theme, setThemeState] = useState<Theme>(() => {
        const stored = localStorage.getItem(THEME_KEY);
        return (stored === 'dark' || stored === 'light') ? stored : 'light';
    });

    // Callback for saving theme to backend (set by AuthContext when user is logged in)
    const saveCallbackRef = useRef<((theme: Theme) => Promise<void>) | null>(null);

    // Apply theme class to document body whenever theme changes
    useEffect(() => {
        document.body.classList.remove('theme-light', 'theme-dark');
        document.body.classList.add(`theme-${theme}`);
        localStorage.setItem(THEME_KEY, theme);
    }, [theme]);

    // Save theme to backend if callback is set
    const saveThemeToBackend = useCallback(async (newTheme: Theme) => {
        if (saveCallbackRef.current) {
            try {
                await saveCallbackRef.current(newTheme);
            } catch (error) {
                console.error('Failed to save theme to backend:', error);
            }
        }
    }, []);

    const toggleTheme = useCallback(() => {
        setThemeState(prev => {
            const newTheme = prev === 'light' ? 'dark' : 'light';
            saveThemeToBackend(newTheme);
            return newTheme;
        });
    }, [saveThemeToBackend]);

    const setTheme = useCallback((newTheme: Theme) => {
        setThemeState(newTheme);
        // Don't save to backend when setting theme from user data (to avoid redundant calls)
    }, []);

    const setSaveCallback = useCallback((callback: ((theme: Theme) => Promise<void>) | null) => {
        saveCallbackRef.current = callback;
    }, []);

    return (
        <ThemeContext.Provider value={{ theme, toggleTheme, setTheme, setSaveCallback }}>
            {children}
        </ThemeContext.Provider>
    );
}
