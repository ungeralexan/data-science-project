// src/config/index.ts
// Centralized configuration for the frontend application

import parameters from './parameters.json';

/*
    This module exports configuration values from parameters.json.
    
    All API endpoints and connection settings should be imported from here
    to ensure consistency across the application.
    
    Usage:
        import { API_BASE_URL, WS_PORT } from '../config';
*/

// Type assertion to allow access to all properties from parameters.json
const params = parameters as typeof parameters & {
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
