/**
 * HTTP client (spec §4.1): Bearer token, Accept-Language = UI language, one refresh-and-retry on
 * 401 TOKEN_EXPIRED, and every failure turned into an ApiError with a code from §7.1 (plus NETWORK
 * and TIMEOUT for transport problems) so screens can show `errors.<code>`.
 *
 * The client doesn't import the stores (they import the client); the app wires it with
 * `configureClient` at start-up.
 */
import axios, { AxiosError, type AxiosInstance, type InternalAxiosRequestConfig } from 'axios';

import { config } from '@/config';
import type { ErrorEnvelope, TokenPair } from './types';

export class ApiError extends Error {
  constructor(
    public readonly code: string,
    message: string,
    public readonly status: number | null = null,
    public readonly details: unknown = null,
    public readonly retryAfterSec: number | null = null,
  ) {
    super(message);
    this.name = 'ApiError';
  }

  /** Field -> issue map for forms (VALIDATION_ERROR details are [{field, issue}]). */
  fieldErrors(): Record<string, string> {
    const out: Record<string, string> = {};
    if (Array.isArray(this.details)) {
      for (const d of this.details as { field?: string; issue?: string }[]) {
        if (d?.field) out[d.field] = d.issue ?? '';
      }
    }
    return out;
  }
}

export interface ClientHooks {
  getAccessToken: () => string | null;
  getRefreshToken: () => string | null;
  getLanguage: () => string;
  onTokensRefreshed: (tokens: TokenPair) => void | Promise<void>;
  onSessionExpired: () => void | Promise<void>;
}

let hooks: ClientHooks = {
  getAccessToken: () => null,
  getRefreshToken: () => null,
  getLanguage: () => 'en',
  onTokensRefreshed: () => undefined,
  onSessionExpired: () => undefined,
};

export function configureClient(h: ClientHooks): void {
  hooks = h;
}

export const api: AxiosInstance = axios.create({
  baseURL: config.apiBaseUrl,
  timeout: config.requestTimeoutMs,
  headers: { Accept: 'application/json' },
});

const REFRESH_PATH = '/auth/token/refresh';

api.interceptors.request.use((req) => {
  const token = hooks.getAccessToken();
  if (token && !req.headers.Authorization) req.headers.Authorization = `Bearer ${token}`;
  req.headers['Accept-Language'] = hooks.getLanguage();
  return req;
});

// One refresh at a time: concurrent 401s wait for the same promise.
let refreshing: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = hooks.getRefreshToken();
  if (!refreshToken) return null;
  try {
    // Bare axios call: must not go through the interceptors (no recursion, no stale bearer).
    const res = await axios.post<TokenPair>(`${config.apiBaseUrl}${REFRESH_PATH}`, { refresh_token: refreshToken }, {
      timeout: config.requestTimeoutMs,
      headers: { 'Accept-Language': hooks.getLanguage() },
    });
    await hooks.onTokensRefreshed(res.data);
    return res.data.access_token;
  } catch {
    return null;
  }
}

type RetriableConfig = InternalAxiosRequestConfig & { _retried?: boolean };

export function toApiError(err: unknown): ApiError {
  if (err instanceof ApiError) return err;
  if (axios.isAxiosError(err)) {
    const e = err as AxiosError<ErrorEnvelope>;
    if (e.response) {
      const body = e.response.data?.error;
      const retry = Number(e.response.headers?.['retry-after']);
      return new ApiError(
        body?.code ?? (e.response.status >= 500 ? 'INTERNAL' : 'VALIDATION_ERROR'),
        body?.message ?? e.message,
        e.response.status,
        body?.details ?? null,
        Number.isFinite(retry) && retry > 0 ? retry : null,
      );
    }
    if (e.code === 'ECONNABORTED' || e.code === 'ETIMEDOUT') return new ApiError('TIMEOUT', e.message);
    return new ApiError('NETWORK', e.message);
  }
  return new ApiError('INTERNAL', err instanceof Error ? err.message : String(err));
}

api.interceptors.response.use(
  (res) => res,
  async (err: unknown) => {
    const apiError = toApiError(err);
    const original = axios.isAxiosError(err) ? (err.config as RetriableConfig | undefined) : undefined;
    const expired = apiError.status === 401 && apiError.code === 'TOKEN_EXPIRED';
    if (expired && original && !original._retried && !original.url?.includes(REFRESH_PATH)) {
      original._retried = true;
      refreshing ??= refreshAccessToken().finally(() => {
        refreshing = null;
      });
      const token = await refreshing;
      if (token) {
        original.headers.Authorization = `Bearer ${token}`;
        return api.request(original);
      }
      await hooks.onSessionExpired();
    } else if (apiError.status === 401 && apiError.code === 'UNAUTHENTICATED' && hooks.getAccessToken()) {
      await hooks.onSessionExpired(); // token revoked or user deleted
    }
    throw apiError;
  },
);
