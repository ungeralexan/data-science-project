// src/hooks/useTheme.ts
import { useContext } from 'react';
import { ThemeContext } from '../context/ThemeContextType';
import type { ThemeContextType } from '../context/ThemeContextType';

/*
    Custom hook to access theme context.
    Provides access to current theme and toggle function.
*/

export function useTheme(): ThemeContextType {
    const context = useContext(ThemeContext);
    if (context === undefined) {
        throw new Error('useTheme must be used within a ThemeProvider');
    }
    return context;
}
