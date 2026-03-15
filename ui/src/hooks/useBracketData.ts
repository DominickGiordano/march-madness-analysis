import { useState, useEffect } from 'react';
import type { BracketData } from '../types';

export function useBracketData() {
  const [data, setData] = useState<BracketData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch('/data/bracket-data.json')
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${String(res.status)}`);
        return res.json() as Promise<BracketData>;
      })
      .then((d) => {
        setData(d);
        setLoading(false);
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : 'Failed to load data');
        setLoading(false);
      });
  }, []);

  return { data, loading, error };
}
