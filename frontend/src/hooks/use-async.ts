"use client";

import { useCallback, useState } from "react";
import {
  type AsyncState,
  errorState,
  getErrorMessage,
  idleState,
  loadingState,
  successState,
} from "@/lib/async-state";

export function useAsync<T>(initialData: T | null = null) {
  const [state, setState] = useState<AsyncState<T>>(
    initialData ? successState(initialData) : idleState(),
  );

  const run = useCallback(async (fn: () => Promise<T>) => {
    setState(loadingState<T>());
    try {
      const data = await fn();
      setState(successState(data));
      return data;
    } catch (err) {
      const message = getErrorMessage(err);
      setState(errorState<T>(message));
      throw err;
    }
  }, []);

  const reset = useCallback(() => {
    setState(idleState());
  }, []);

  const setData = useCallback((data: T) => {
    setState(successState(data));
  }, []);

  return { ...state, run, reset, setData, setState };
}
