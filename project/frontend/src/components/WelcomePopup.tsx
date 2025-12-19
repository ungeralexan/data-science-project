import React, { useCallback, useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { STORAGE_KEYS } from "../config";
import "./css/WelcomePopup.css";

type Props = {
  storageKey?: string;
};

// Default storage key from centralized config
const DEFAULT_STORAGE_KEY = STORAGE_KEYS.WELCOME_POPUP_SEEN;

export default function WelcomePopup({ storageKey = DEFAULT_STORAGE_KEY }: Props) {
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated, isLoading } = useAuth();

  const isAuthPage = useMemo(() => {
    return (
      location.pathname.startsWith("/login") ||
      location.pathname.startsWith("/register") ||
      location.pathname.startsWith("/forgot-password") ||
      location.pathname.startsWith("/reset-password")
    );
  }, [location.pathname]);

  const hasSeen = useMemo(() => {
    try {
      return localStorage.getItem(storageKey) === "true";
    } catch {
      return true;
    }
  }, [storageKey]);

  const shouldShow = !isLoading && !isAuthenticated && !isAuthPage && !hasSeen;

  const [open, setOpen] = useState<boolean>(false);

  useEffect(() => {
    setOpen(shouldShow);
  }, [shouldShow]);

  const markSeen = useCallback(() => {
    try {
      localStorage.setItem(storageKey, "true");
    } catch {
      // ignore
    }
  }, [storageKey]);

  const handleClose = useCallback(() => {
    markSeen();
    setOpen(false);
  }, [markSeen]);

  const onOverlayClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) handleClose();
  };

  const onKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === "Escape") handleClose();
    },
    [handleClose]
  );

  useEffect(() => {
    if (!open) return;

    document.addEventListener("keydown", onKeyDown);
    document.body.style.overflow = "hidden";

    return () => {
      document.removeEventListener("keydown", onKeyDown);
      document.body.style.overflow = "";
    };
  }, [open, onKeyDown]);

  if (!open) return null;

  return (
    <div className="tp-overlay" onClick={onOverlayClick} role="presentation">
      <div className="tp-modal" role="dialog" aria-modal="true" aria-label="Welcome to tuevent">
        <button className="tp-close" onClick={handleClose} aria-label="Close">
          ×
        </button>

        <h2 className="tp-title">Welcome to tuevent!</h2>

        <p className="tp-text">
          Discover lectures, workshops, culture, and student events in Tübingen – all in one place.
        </p>

        <p className="tp-text">
          Create an account to get personalized  event recommendations.
        </p>

        <div className="tp-actions">
          <button
            className="tp-primary"
            onClick={() => {
              handleClose();
              navigate("/register");
            }}
          >
            Create account
          </button>

          <button className="tp-link" onClick={handleClose}>
            Explore without account
          </button>
        </div>

        <div className="tp-footer">
          Already have an account?{" "}
          <button
            className="tp-inlineLink"
            onClick={() => {
              handleClose();
              navigate("/login");
            }}
          >
            Sign in
          </button>
        </div>
      </div>
    </div>
  );
}
