import axios from 'axios';

const TOKEN_KEY = 'streampulse.token';

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '',
});

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

// Attach the bearer token to every request.
api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// On 401, clear the token so the app falls back to the login screen.
api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401) {
      clearToken();
      // Let listeners (AuthContext) react to the change.
      window.dispatchEvent(new Event('streampulse:unauthorized'));
    }
    return Promise.reject(error);
  },
);

export async function login(email: string, password: string): Promise<string> {
  // OAuth2 password flow expects form-encoded username/password.
  const body = new URLSearchParams();
  body.append('username', email);
  body.append('password', password);
  const { data } = await api.post<{ access_token: string }>(
    '/api/v1/auth/login',
    body,
    { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } },
  );
  return data.access_token;
}
