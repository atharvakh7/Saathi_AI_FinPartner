import axios, { type AxiosAdapter, type AxiosRequestConfig, type AxiosResponse } from 'axios';

import { api, ApiError, configureClient, toApiError } from '@/api/client';

type Reply = { status: number; data: unknown; headers?: Record<string, string> };
type Handler = (cfg: AxiosRequestConfig) => Reply | Error;

function install(handler: Handler) {
  const calls: AxiosRequestConfig[] = [];
  const adapter: AxiosAdapter = async (cfg) => {
    calls.push(cfg);
    const out = handler(cfg);
    if (out instanceof Error) throw out;
    const res: AxiosResponse = {
      data: out.data, status: out.status, statusText: '', headers: out.headers ?? {}, config: cfg as never,
    };
    if (out.status >= 400) throw new axios.AxiosError('fail', undefined, cfg as never, null, res);
    return res;
  };
  api.defaults.adapter = adapter;
  axios.defaults.adapter = adapter; // the refresh call uses bare axios
  return calls;
}

let access = 'old-access';
const refreshed: string[] = [];
const expired = jest.fn();

beforeEach(() => {
  access = 'old-access';
  refreshed.length = 0;
  expired.mockReset();
  configureClient({
    getAccessToken: () => access,
    getRefreshToken: () => 'refresh-token-xxxxxxxxxxxxxxxxxxxx',
    getLanguage: () => 'mr',
    onTokensRefreshed: (t) => {
      access = t.access_token;
      refreshed.push(t.access_token);
    },
    onSessionExpired: expired,
  });
});

const expiredBody = { error: { code: 'TOKEN_EXPIRED', message: 'expired', details: null } };

test('sends bearer token and Accept-Language', async () => {
  const calls = install(() => ({ status: 200, data: { ok: true } }));
  await api.get('/me');
  expect(calls[0]!.headers!.Authorization).toBe('Bearer old-access');
  expect(calls[0]!.headers!['Accept-Language']).toBe('mr');
});

test('refreshes once for concurrent 401s, then retries with the new token', async () => {
  const calls = install((cfg) => {
    if (cfg.url?.endsWith('/auth/token/refresh')) {
      return { status: 200, data: { access_token: 'new-access', refresh_token: 'r2-xxxxxxxxxxxxxxxxxxxxxx', expires_in: 900 } };
    }
    return cfg.headers!.Authorization === 'Bearer new-access'
      ? { status: 200, data: { url: cfg.url } }
      : { status: 401, data: expiredBody };
  });
  const [a, b] = await Promise.all([api.get('/me'), api.get('/goals')]);
  expect(a.data).toEqual({ url: '/me' });
  expect(b.data).toEqual({ url: '/goals' });
  expect(calls.filter((c) => c.url?.endsWith('/auth/token/refresh'))).toHaveLength(1);
  expect(refreshed).toEqual(['new-access']);
  expect(expired).not.toHaveBeenCalled();
});

test('failed refresh ends the session and rejects with TOKEN_EXPIRED', async () => {
  install((cfg) => (cfg.url?.endsWith('/auth/token/refresh')
    ? { status: 401, data: { error: { code: 'UNAUTHENTICATED', message: 'no', details: null } } }
    : { status: 401, data: expiredBody }));
  await expect(api.get('/me')).rejects.toMatchObject({ code: 'TOKEN_EXPIRED', status: 401 });
  expect(expired).toHaveBeenCalledTimes(1);
});

test('revoked token (UNAUTHENTICATED) ends the session without a refresh', async () => {
  const calls = install(() => ({ status: 401, data: { error: { code: 'UNAUTHENTICATED', message: 'x', details: null } } }));
  await expect(api.get('/me')).rejects.toMatchObject({ code: 'UNAUTHENTICATED' });
  expect(calls).toHaveLength(1);
  expect(expired).toHaveBeenCalledTimes(1);
});

test('error envelope, field errors and Retry-After', async () => {
  install(() => ({
    status: 429,
    data: { error: { code: 'RATE_LIMITED', message: 'slow down', details: { retry_after_sec: 30 } } },
    headers: { 'retry-after': '30' },
  }));
  const err = await api.get('/x').catch((e: unknown) => e);
  expect(err).toBeInstanceOf(ApiError);
  expect(err).toMatchObject({ code: 'RATE_LIMITED', status: 429, retryAfterSec: 30 });
  const v = new ApiError('VALIDATION_ERROR', 'bad', 422, [{ field: 'age_years', issue: 'too young' }]);
  expect(v.fieldErrors()).toEqual({ age_years: 'too young' });
});

test('transport failures map to NETWORK / TIMEOUT', () => {
  expect(toApiError(new axios.AxiosError('Network Error', 'ERR_NETWORK')).code).toBe('NETWORK');
  expect(toApiError(new axios.AxiosError('timeout', 'ECONNABORTED')).code).toBe('TIMEOUT');
});
