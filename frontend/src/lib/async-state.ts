export type AsyncStatus = "idle" | "loading" | "success" | "error";

export interface AsyncState<T> {
  status: AsyncStatus;
  data: T | null;
  error: string | null;
}

export function idleState<T>(): AsyncState<T> {
  return { status: "idle", data: null, error: null };
}

export function loadingState<T>(data: T | null = null): AsyncState<T> {
  return { status: "loading", data, error: null };
}

export function successState<T>(data: T): AsyncState<T> {
  return { status: "success", data, error: null };
}

export function errorState<T>(error: string, data: T | null = null): AsyncState<T> {
  return { status: "error", data, error };
}

export function isLoading<T>(state: AsyncState<T>): boolean {
  return state.status === "loading";
}

export function isError<T>(state: AsyncState<T>): boolean {
  return state.status === "error";
}

export function isSuccess<T>(state: AsyncState<T>): boolean {
  return state.status === "success";
}

export function getErrorMessage(err: unknown): string {
  if (err instanceof Error) return err.message;
  if (typeof err === "string") return err;
  return "Something went wrong";
}
