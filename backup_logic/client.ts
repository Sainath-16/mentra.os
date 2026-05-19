import { env } from "@/lib/config/env";
import { clearToken, getToken } from "@/lib/auth/tokenStore";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function parseError(res: Response) {
  const text = await res.text();
  return text || `HTTP ${res.status}`;
}

export async function apiRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getToken();

  const res = await fetch(`${env.NEXT_PUBLIC_API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init.headers || {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });

  if (!res.ok) {
    if (res.status === 401) {
      clearToken();
    }
    throw new ApiError(res.status, await parseError(res));
  }

  return (await res.json()) as T;
}
