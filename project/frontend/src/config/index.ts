// src/config/index.ts
// Centralized configuration for the frontend application

import parameters from './parameters.json';

/*This module exports configuration values from parameters.json.*/

// Type assertion to allow access to all properties from parameters.json
const params = parameters as typeof parameters & {
    API_BASE_URL: string;
    WS_PORT: number;
    LOCAL: boolean;
    POSSIBLE_INTEREST_KEYWORDS: string[];
    POSSIBLE_LANGUAGE_OPTIONS: string[];
    STORAGE_KEYS: {
        AUTH_TOKEN: string;
        THEME: string;
        WELCOME_POPUP_SEEN: string;
        RECOMMENDATION_COOLDOWN_UNTIL: string;
    };
    TIMEOUTS: {
        PASSWORD_RESET_REDIRECT_MS: number;
        RECOMMENDATION_COOLDOWN_MS: number;
    };
    PAGINATION: { EVENTS_PER_PAGE: number };
};

export const API_BASE_URL: string = params.API_BASE_URL;
export const WS_PORT: number = params.WS_PORT;
export const POSSIBLE_INTEREST_KEYWORDS: string[] = params.POSSIBLE_INTEREST_KEYWORDS;
export const POSSIBLE_LANGUAGE_OPTIONS: string[] = params.POSSIBLE_LANGUAGE_OPTIONS;
export const LOCAL: boolean = params.LOCAL;

// Storage keys for localStorage
export const STORAGE_KEYS = params.STORAGE_KEYS;

// Timeouts and intervals (in milliseconds)
export const TIMEOUTS = params.TIMEOUTS;

// Pagination settings
export const PAGINATION = params.PAGINATION;
