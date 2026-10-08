import Link from "next/link";
import { Button } from "@/components/ui/Button";

export function CTASection() {
  return (
    <section className="mx-auto max-w-desktop px-4 pb-16 md:px-8 md:pb-24">
      <div className="rounded-card bg-ku-green px-8 py-12 text-center md:py-16">
        <h2 className="text-h1 text-white">Ready to see your CEFR level?</h2>
        <p className="mx-auto mt-3 max-w-xl text-body text-white/85">
          The placement test takes a few minutes per skill. Start free, or try
          it as a guest first — no email required.
        </p>
        <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
          <Link href="/signup">
            <Button
              size="lg"
              className="w-full bg-white text-ku-dark-green hover:bg-ku-cream sm:w-auto"
            >
              Create free account
            </Button>
          </Link>
          <Link href="/login">
            <Button
              variant="secondary"
              size="lg"
              className="w-full border-white text-white hover:bg-white/10 sm:w-auto"
            >
              Log in
            </Button>
          </Link>
        </div>
      </div>
    </section>
  );
}
