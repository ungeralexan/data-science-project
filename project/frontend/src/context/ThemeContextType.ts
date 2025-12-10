// src/context/ThemeContextType.ts
import { createContext } from 'react';

/*
    Theme context type definition and context creation.
*/

export type Theme = 'light' | 'dark';

export interface ThemeContextType {
    theme: Theme;
    toggleTheme: () => void;
    setTheme: (theme: Theme) => void;
}

export const ThemeContext = createContext<ThemeContextType | undefined>(undefined);
