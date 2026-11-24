export default function DashboardTabs({ items, active, onChange }) {
  return (
    <div className="flex gap-1 overflow-x-auto rounded-xl border border-neutral-200 bg-white p-1 shadow-sm">
      {items.map((item) => {
        const Icon = item.icon;
        const selected = active === item.key;
        return (
          <button
            key={item.key}
            type="button"
            onClick={() => onChange(item.key)}
            aria-current={selected ? "page" : undefined}
            className={`inline-flex flex-1 items-center justify-center gap-2 whitespace-nowrap rounded-lg px-3 py-2 text-sm font-medium transition ${
              selected
                ? "bg-neutral-900 text-white shadow-sm"
                : "text-neutral-600 hover:bg-neutral-50 hover:text-neutral-900"
            }`}
          >
            {Icon ? <Icon size={16} /> : null}
            {item.label}
            {item.count !== undefined ? (
              <span
                className={`rounded-full px-1.5 py-0.5 text-[10px] font-semibold ${
                  selected ? "bg-white/20 text-white" : "bg-neutral-100 text-neutral-500"
                }`}
              >
                {item.count}
              </span>
            ) : null}
          </button>
        );
      })}
    </div>
  );
}
