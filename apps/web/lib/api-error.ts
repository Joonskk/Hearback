/** An error response from FastAPI: {"error": {"code", "message", "details?"}}. */
export class ApiError extends Error {
  status: number;
  code: string;
  details: unknown;

  constructor(
    status: number,
    code: string,
    message: string,
    details?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

/** Returns the JSON body of a 2xx response; throws ApiError for anything else. */
export async function readResponse<T>(response: Response): Promise<T> {
  if (response.status === 204) {
    return undefined as T;
  }
  const body = await response.json().catch(() => null);
  if (response.ok) {
    return body as T;
  }
  const error = body?.error;
  if (error === undefined) {
    throw new ApiError(response.status, "unknown_error", response.statusText);
  }
  throw new ApiError(response.status, error.code, error.message, error.details);
}
