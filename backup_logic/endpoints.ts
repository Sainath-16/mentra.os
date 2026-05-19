import { apiRequest } from "@/lib/api/client";
import type {
  AuthResponse,
  AdminPrediction,
  AdminUser,
  MeResponse,
  PredictionRecord,
  PredictResponse,
  SecurityQuestionResponse,
} from "@/lib/api/types";

export const api = {
  health: () => apiRequest<{ status: string }>("/health"),

  register: (data: { username: string; email: string; password: string; security_question: string; security_answer: string }) =>
    apiRequest<AuthResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  login: (username: string, password: string) =>
    apiRequest<AuthResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    }),

  me: () => apiRequest<MeResponse>("/me"),

  myPredictions: () => apiRequest<PredictionRecord[]>("/me/predictions"),

  predict: (features: number[]) =>
    apiRequest<PredictResponse>("/predict", {
      method: "POST",
      body: JSON.stringify({ features }),
    }),

  adminUsers: () => apiRequest<AdminUser[]>("/admin/users"),
  adminPredictions: () => apiRequest<AdminPrediction[]>("/admin/predictions"),

  getSecurityQuestion: (username: string) => 
    apiRequest<SecurityQuestionResponse>(`/auth/security-question/${encodeURIComponent(username)}`),

  verifySecurityAnswer: (username: string, security_answer: string) =>
    apiRequest<{ status: string }>("/auth/verify-answer", {
        method: "POST",
        body: JSON.stringify({ username, security_answer }),
    }),

  resetPassword: (data: { username: string; security_answer: string; new_password: string }) =>
    apiRequest<{ status: string }>("/auth/reset-password", {
        method: "POST",
        body: JSON.stringify(data),
    }),

  updateAvatar: (avatar_base64: string) =>
    apiRequest<{ status: string }>("/me/avatar", {
        method: "POST",
        body: JSON.stringify({ avatar_base64 }),
    }),

  injectAdmin: (username: string) =>
    apiRequest<{ status: string }>(`/auth/inject-admin?username=${encodeURIComponent(username)}`, {
        method: "POST"
    }),
};
