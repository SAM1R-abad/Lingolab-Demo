import Link from "next/link";
import { BookOpenCheck } from "lucide-react";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4 py-12">
      <div className="w-full max-w-md">
        <Link
          href="/"
          className="mb-8 flex items-center justify-center gap-2 text-h4 font-semibold text-ku-dark-green"
        >
          <BookOpenCheck className="h-6 w-6 text-ku-green" aria-hidden="true" />
          LingoLab
        </Link>
        {children}
      </div>
    </div>
  );
}
