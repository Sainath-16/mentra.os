"use client";

import { useEffect, useState } from "react";
import type { MeResponse } from "@/lib/api/types";
import { api } from "@/lib/api/endpoints";
import { getErrorMessage } from "@/lib/api/errors";

export function useSession() {
  const [me, setMe] = useState<MeResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    try {
      const r = await api.me();
      setMe(r);
      setError(null);
    } catch (e: unknown) {
      setMe(null);
      setError(getErrorMessage(e, "Failed to load session"));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  return { me, loading, error, refresh: load };
}
