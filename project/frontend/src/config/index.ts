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

export const API_BASE_URL: string = parameters.API_BASE_URL;
export const WS_PORT: number = parameters.WS_PORT;
export const POSSIBLE_INTEREST_KEYWORDS: string[] = parameters.POSSIBLE_INTEREST_KEYWORDS;
export const LOCAL: boolean = parameters.LOCAL;
