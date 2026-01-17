import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import 'antd/dist/reset.css';
import './index.css'; /* Global styles */
import App from './App';

/*
  main.tsx mainly sets up the React application by wrapping the App component with
  necessary providers for routing and theming, and then rendering it to the DOM.

  StrictMode: 
    StrictMode is a tool for highlighting potential problems in an application. 
    It activates additional checks and warnings for its descendants.
  
  BrowserRouter:
    BrowserRouter is a router implementation that uses the HTML5 history API 
    (pushState, replaceState and the popstate event) to keep the UI in sync with the URL.
  
  AuthProvider:
    AuthProvider is a context provider that manages authentication state and 
    provides authentication-related functions to the rest of the application.
*/
createRoot(document.getElementById('root')!).render(
  <StrictMode> 
    <BrowserRouter>
      <AuthProvider>
        <App />
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>
);
