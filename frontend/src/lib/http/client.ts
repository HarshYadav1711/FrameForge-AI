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

interface ApiErrorPayload {
  detail?: string | { msg?: string }[];
  message?: string;
  error?: string;
  cause?: string;
}

async function parseErrorBody(
  res: Response,
): Promise<{ message: string; code?: string }> {
  try {
    const data = (await res.json()) as ApiErrorPayload;
    if (typeof data.detail === "string") {
      return { message: data.detail };
    }
    if (Array.isArray(data.detail)) {
      return {
        message: data.detail
          .map((d) => d.msg ?? "Validation error")
          .join("; "),
      };
    }
    let message = data.message ?? res.statusText ?? "Request failed";
    if (data.cause) {
      message = `${message} (${data.cause})`;
    }
    return {
      message,
      code: typeof data.error === "string" ? data.error : undefined,
    };
  } catch {
    return { message: res.statusText || "Request failed" };
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
    const { message, code } = await parseErrorBody(res);
    throw new ApiError(message, res.status, code);
  }

  if (res.status === 204) {
    return undefined as T;
  }

  return res.json() as Promise<T>;
}
