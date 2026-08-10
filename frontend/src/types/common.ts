/** Shape of every error response produced by the backend's global handlers
 *  (see backend/app/core/handlers.py::_base_error_content). */
export interface ApiErrorPayload {
  detail: string;
  error: {
    code: string;
    timestamp: string;
    path: string;
    method: string;
    request_id: string | null;
    errors?: Array<Record<string, unknown>>;
  };
}
