import { X } from "lucide-react";
import { useEffect } from "react";

export default function Modal({ open, onClose, title, description, children, footer, wide = false }) {
  useEffect(() => {
    if (!open) return undefined;
    function onKey(event) {
      if (event.key === "Escape") onClose?.();
    }
    document.addEventListener("keydown", onKey);
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = previous;
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-neutral-900/50 p-4 backdrop-blur-sm sm:items-center"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose?.();
      }}
      role="dialog"
      aria-modal="true"
      aria-label={title}
    >
      <div
        className={`max-h-[90vh] w-full ${wide ? "max-w-3xl" : "max-w-lg"} overflow-y-auto rounded-2xl bg-white shadow-2xl animate-fade-in`}
      >
        <div className="flex items-start justify-between gap-4 border-b border-neutral-100 px-6 py-4">
          <div>
            <h2 className="text-lg font-semibold text-neutral-900">{title}</h2>
            {description ? <p className="mt-1 text-sm text-neutral-500">{description}</p> : null}
          </div>
          <button type="button" onClick={onClose} className="btn-ghost !p-2" aria-label="Close">
            <X size={18} />
          </button>
        </div>
        <div className="px-6 py-5">{children}</div>
        {footer ? <div className="border-t border-neutral-100 px-6 py-4">{footer}</div> : null}
      </div>
    </div>
  );
}
