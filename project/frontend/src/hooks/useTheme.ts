// src/hooks/useTheme.ts
import { useContext } from 'react';
import { AuthContext } from '../context/AuthContextType';
import type { Theme } from '../context/AuthContextType';

/*
    Custom hook to access theme from auth context.
    Provides access to current theme and toggle function.
    
    Theme is now managed by AuthContext to:
    - Avoid duplicate state between ThemeContext and user.theme_preference
    - Automatically sync theme with backend for logged-in users
    - Still work for guest users via localStorage
*/

export interface ThemeContextType {
    theme: Theme;
    toggleTheme: () => void;
}

export function useTheme(): ThemeContextType {
    const context = useContext(AuthContext);
    
    if (context === undefined) {
        throw new Error('useTheme must be used within an AuthProvider');
    }

    return {
        theme: context.theme,
        toggleTheme: context.toggleTheme,
    };
}
