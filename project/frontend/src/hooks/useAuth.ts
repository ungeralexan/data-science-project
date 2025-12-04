// src/hooks/useAuth.ts
import { useContext } from 'react';
import { AuthContext } from '../context/AuthContextType';
import type { AuthContextType } from '../context/AuthContextType';

/*
    This file defines a custom React hook useAuth that provides easy access
    to the authentication context throughout the application.

    The useAuth hook utilizes the useContext hook from react to access the
    AuthContext, which contains authentication state and functions.

    By using this hook, components can easily retrieve the current user,
    authentication token, and functions for login, logout, registration,
    and user profile management.
*/

export function useAuth(): AuthContextType {
    const context = useContext(AuthContext);

    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    
    return context;
}
