import { env } from "@/config/env";

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly code?: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function parseErrorBody(res: Response): Promise<string> {
  try {
    const data = await res.json();
    if (typeof data.detail === "string") return data.detail;
    if (Array.isArray(data.detail)) {
      return data.detail.map((d: { msg?: string }) => d.msg ?? "Validation error").join("; ");
    }
    return data.message ?? data.error ?? res.statusText;
  } catch {
    return res.statusText || "Request failed";
  }
}

export interface RequestOptions extends Omit<RequestInit, "body"> {
  body?: BodyInit | Record<string, unknown> | null;
  params?: Record<string, string>;
}

export async function apiRequest<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const { body, params, headers, ...init } = options;

  const url = new URL(path.startsWith("http") ? path : `${env.apiUrl}${path}`);
  if (params) {
    Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));
  }

  const isFormData = body instanceof FormData;
  const resolvedHeaders = new Headers(headers);
  if (body && !isFormData && typeof body === "object") {
    resolvedHeaders.set("Content-Type", "application/json");
  }

  const res = await fetch(url.toString(), {
    ...init,
    headers: resolvedHeaders,
    body:
      body == null
        ? undefined
        : isFormData
          ? body
          : typeof body === "object"
            ? JSON.stringify(body)
            : body,
  });

  if (!res.ok) {
    throw new ApiError(await parseErrorBody(res), res.status);
  }

  if (res.status === 204) {
    return undefined as T;
  }

  return res.json() as Promise<T>;
}
