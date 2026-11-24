import { Compass } from "lucide-react";
import { Link } from "react-router-dom";
import Navbar from "../components/Navbar";

export default function NotFound() {
  return (
    <div className="min-h-screen bg-neutral-50">
      <Navbar />
      <main className="mx-auto flex min-h-[70vh] max-w-lg flex-col items-center justify-center gap-4 px-4 text-center">
        <span className="grid h-14 w-14 place-items-center rounded-2xl bg-neutral-100 text-neutral-900">
          <Compass size={26} />
        </span>
        <h1 className="text-2xl font-bold text-neutral-900">Page not found</h1>
        <p className="text-sm text-neutral-500">
          The page you are looking for does not exist or has moved.
        </p>
        <Link to="/" className="btn-primary">
          Back to home
        </Link>
      </main>
    </div>
  );
}
