export type Role = "user" | "admin";

export type AuthResponse = {
  access_token: string;
  token_type: "bearer";
  user_id: number;
  username: string;
  role: Role;
  avatar_url?: string | null;
};

export type MeResponse = {
  user_id: number;
  username: string;
  role: Role;
  avatar_url?: string | null;
};

export type PredictionRecord = {
  id: number;
  stress_level: string;
  confidence: number;
  timestamp: string;
};

export type PredictResponse = {
  predicted_class: number;
  stress_label: string;
  confidence: number;
  probabilities: Record<string, number>;
  prediction_id?: number | null;
  timestamp: string;
};

export type AdminUser = {
  id: number;
  username: string;
  role: Role;
  created_at: string | null;
};

export type AdminPrediction = {
  id: number;
  user_id: number;
  username: string;
  stress_level: string;
  confidence: number;
  timestamp: string;
};

export type SecurityQuestionResponse = {
    username: string;
    security_question: string;
};
