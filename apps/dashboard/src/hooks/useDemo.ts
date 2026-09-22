/**
 * useDemo — fetches demo mode status from backend once on mount.
 * All components consume this hook to know if blur/upgrade UI should show.
 */
import { useState, useEffect } from "react";
import { api } from "../lib/api";

export interface DemoStatus {
  demo_mode:   boolean;
  buy_link:    string;
  demo_price:  string;
  seller_name: string;
  upgrade_msg: string;
}

const DEFAULT: DemoStatus = {
  demo_mode:   false,
  buy_link:    "",
  demo_price:  "$500",
  seller_name: "",
  upgrade_msg: "",
};

let _cached: DemoStatus | null = null;

export function useDemo(): DemoStatus {
  const [status, setStatus] = useState<DemoStatus>(_cached ?? DEFAULT);

  useEffect(() => {
    if (_cached) return;
    api.get<DemoStatus>("/demo/status")
      .then(d => { _cached = d; setStatus(d); })
      .catch(() => {});
  }, []);

  return status;
}
