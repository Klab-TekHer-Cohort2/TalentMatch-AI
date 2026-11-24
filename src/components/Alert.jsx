import { AlertCircle, CheckCircle2, Info, X } from "lucide-react";

const styles = {
  error: {
    wrapper: "border-neutral-200 bg-neutral-100 text-neutral-700",
    Icon: AlertCircle,
  },
  success: {
    wrapper: "border-neutral-200 bg-neutral-100 text-neutral-900",
    Icon: CheckCircle2,
  },
  info: {
    wrapper: "border-neutral-200 bg-neutral-100 text-black",
    Icon: Info,
  },
};

export default function Alert({ variant = "error", children, onClose, className = "" }) {
  const { wrapper, Icon } = styles[variant] || styles.error;
  return (
    <div
      role={variant === "error" ? "alert" : "status"}
      className={`flex items-start gap-3 rounded-xl border px-4 py-3 text-sm ${wrapper} ${className}`}
    >
      <Icon size={18} className="mt-0.5 shrink-0" />
      <div className="flex-1 leading-relaxed">{children}</div>
      {onClose ? (
        <button type="button" onClick={onClose} aria-label="Dismiss" className="opacity-60 hover:opacity-100">
          <X size={16} />
        </button>
      ) : null}
    </div>
  );
}
