// src/components/ProtectedRoute.tsx
import { Navigate, useLocation } from 'react-router-dom';
import { Spin } from 'antd';
import { useAuth } from '../hooks/useAuth';
import './css/ProtectedRoute.css';

interface ProtectedRouteProps {
    children: React.ReactNode;
}

/**
 * ProtectedRoute component that wraps routes requiring authentication.
 * If the user is not authenticated, they are redirected to the login page.
 * The original location is saved so the user can be redirected back after login.
 */
export default function ProtectedRoute({ children }: ProtectedRouteProps) {
    const { isAuthenticated, isLoading } = useAuth();
    const location = useLocation();

    // Show loading spinner while checking authentication status
    if (isLoading) {
        return (
            <div className="protected-route-loading">
                <Spin size="large" tip="Loading..." />
            </div>
        );
    }

    // Redirect to login if not authenticated
    if (!isAuthenticated) {
        // Save the attempted URL for redirecting after login
        return <Navigate to="/login" state={{ from: location }} replace />;
    }

    // Render the protected content
    return <>{children}</>;
}
