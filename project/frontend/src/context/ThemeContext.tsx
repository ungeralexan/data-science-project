// src/context/ThemeContext.tsx
import { useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import { ThemeContext } from './ThemeContextType';
import type { Theme } from './ThemeContextType';

/*
    ThemeProvider provides dark mode functionality across the application.
    
    - Stores theme preference in localStorage for persistence
    - Applies theme class to document body
    - Provides toggle function for switching themes
*/

const THEME_KEY = 'app_theme';

interface ThemeProviderProps {
    children: ReactNode;
}

export function ThemeProvider({ children }: ThemeProviderProps) {
    // Initialize theme from localStorage or default to 'light'
    const [theme, setThemeState] = useState<Theme>(() => {
        const stored = localStorage.getItem(THEME_KEY);
        return (stored === 'dark' || stored === 'light') ? stored : 'light';
    });

    // Apply theme class to document body whenever theme changes
    useEffect(() => {
        document.body.classList.remove('theme-light', 'theme-dark');
        document.body.classList.add(`theme-${theme}`);
        localStorage.setItem(THEME_KEY, theme);
    }, [theme]);

    const toggleTheme = () => {
        setThemeState(prev => prev === 'light' ? 'dark' : 'light');
    };

    const setTheme = (newTheme: Theme) => {
        setThemeState(newTheme);
    };

    return (
        <ThemeContext.Provider value={{ theme, toggleTheme, setTheme }}>
            {children}
        </ThemeContext.Provider>
    );
}
