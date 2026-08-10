import type { ToastMessage } from "@/components/common/Toast";

type Listener = (t: ToastMessage) => void;
export const toastListeners: Listener[] = [];

export const toast = {
  success: (message: string) => emit(message, "success"),
  error:   (message: string) => emit(message, "error"),
  info:    (message: string) => emit(message, "info"),
};

function emit(message: string, type: ToastMessage["type"]) {
  const id = `${Date.now()}-${Math.random()}`;
  toastListeners.forEach((l) => l({ id, message, type }));
}
