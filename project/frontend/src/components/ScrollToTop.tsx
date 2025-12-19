// src/components/ScrollToTop.tsx
import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';

/*
  ScrollToTop Component
  
  This component automatically scrolls the window to the top whenever the route changes.
  It should be placed inside the Router component to listen for navigation changes.
  
  This fixes the issue where navigating between pages would keep the scroll position
  from the previous page instead of starting at the top.
*/

export default function ScrollToTop() {
  const { pathname } = useLocation();

  useEffect(() => {
    // Scroll to top when the pathname changes
    window.scrollTo(0, 0);
  }, [pathname]);

  return null; // This component doesn't render anything
}
