import { useState, useMemo, useCallback } from 'react';
import type { BracketData, StrategyBracket } from '../types';
import { applyOverrides } from '../lib/cascade';

export interface BracketState {
  activeVariantId: number;
  overrides: Map<string, string>;
  computedBracket: StrategyBracket;
  regionNames: string[];
  setVariant: (id: number) => void;
  addOverride: (matchupId: string, winner: string) => void;
  hasOverrides: boolean;
  /** kept for backward compat — derived from active variant */
  activeStrategy: string;
}

const DEFAULT_VARIANT_ID = 7;

export function useBracketState(data: BracketData): BracketState {
  const [activeVariantId, setActiveVariantId] = useState<number>(DEFAULT_VARIANT_ID);
  const [overrides, setOverrides] = useState<Map<string, string>>(new Map());

  const regionNames = useMemo(
    () => Object.keys(data.bracket.regions),
    [data.bracket.regions],
  );

  const hasVariants = Boolean(data.variants && data.variants.length > 0);

  const baseBracket: StrategyBracket = useMemo(() => {
    if (hasVariants && data.variants) {
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      return data.variants[activeVariantId] ?? data.variants[0]!;
    }
    // fallback: map variant id to old strategy keys
    if (activeVariantId < 5) return data.strategies.safe;
    if (activeVariantId < 10) return data.strategies.balanced;
    return data.strategies.risky;
  }, [hasVariants, data.variants, data.strategies, activeVariantId]);

  const computedBracket = useMemo(
    () => applyOverrides(baseBracket, overrides, data.probMatrix, regionNames),
    [baseBracket, overrides, data.probMatrix, regionNames],
  );

  const setVariant = useCallback(
    (id: number) => {
      if (id === activeVariantId) return;
      if (overrides.size > 0) {
        const confirmed = window.confirm(
          'Switching variants will reset your manual picks. Continue?',
        );
        if (!confirmed) return;
      }
      setOverrides(new Map());
      setActiveVariantId(id);
    },
    [activeVariantId, overrides.size],
  );

  const addOverride = useCallback((matchupId: string, winner: string) => {
    setOverrides((prev) => {
      const next = new Map(prev);
      next.set(matchupId, winner);
      return next;
    });
  }, []);

  const activeStrategy = hasVariants && data.variants
    ? (data.variants[activeVariantId]?.strategy ?? 'balanced')
    : activeVariantId < 5 ? 'safe' : activeVariantId < 10 ? 'balanced' : 'risky';

  return {
    activeVariantId,
    overrides,
    computedBracket,
    regionNames,
    setVariant,
    addOverride,
    hasOverrides: overrides.size > 0,
    activeStrategy,
  };
}
