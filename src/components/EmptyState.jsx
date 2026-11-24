import { Inbox } from "lucide-react";

export default function EmptyState({ icon: Icon = Inbox, title, description, action }) {
  return (
    <div className="card flex flex-col items-center justify-center gap-3 px-6 py-14 text-center">
      <span className="grid h-12 w-12 place-items-center rounded-2xl bg-neutral-100 text-neutral-900">
        <Icon size={22} />
      </span>
      <div>
        <h3 className="text-base font-semibold text-neutral-900">{title}</h3>
        {description ? <p className="mx-auto mt-1 max-w-md text-sm text-neutral-500">{description}</p> : null}
      </div>
      {action}
    </div>
  );
}
