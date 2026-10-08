"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";

const SAMPLE_LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"] as const;

export function Hero() {
  return (
    <section className="mx-auto max-w-desktop px-4 pb-16 pt-12 md:px-8 md:pb-24 md:pt-16">
      <div className="grid items-center gap-12 lg:grid-cols-2">
        <div>
          <Badge tone="green" className="mb-4">
            <Sparkles className="h-3 w-3" aria-hidden="true" />
            Karabakh University Excellence Center
          </Badge>
          <h1 className="text-h1 md:text-display text-ku-dark-green">
            Find your real English level. Then get a plan built around it.
          </h1>
          <p className="mt-4 max-w-lg text-body text-text-secondary">
            LingoLab is an adaptive language-development platform. Instead of one
            generic course for everyone, it tests each skill separately, adjusts
            question difficulty as you answer, and reports your actual CEFR
            level — from Pre-A1 to C2.
          </p>
          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <Link href="/signup">
              <Button size="lg" className="w-full sm:w-auto">
                Start your placement test
                <ArrowRight className="h-4 w-4" aria-hidden="true" />
              </Button>
            </Link>
            <Link href="/login">
              <Button variant="secondary" size="lg" className="w-full sm:w-auto">
                I already have an account
              </Button>
            </Link>
          </div>
          <p className="mt-3 text-caption text-text-secondary">
            No account yet? You can also try it as a guest — no email required.
          </p>
        </div>

        {/* Signature element: the adaptive engine visualized as a live CEFR ladder */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: "easeOut" }}
          className="rounded-card border border-border bg-surface p-6 shadow-md"
        >
          <p className="text-small font-medium text-text-secondary">Vocabulary · Live session</p>
          <h3 className="mt-1 text-h4 text-text-primary">
            A &lsquo;meticulous&rsquo; worker pays...
          </h3>
          <div className="mt-4 flex flex-col gap-2">
            {[
              "no attention to detail",
              "very careful attention to detail",
              "attention only to money",
            ].map((option, i) => (
              <div
                key={option}
                className={
                  "rounded-input border px-3 py-2 text-small " +
                  (i === 1
                    ? "border-ku-green bg-ku-soft-green/40 text-ku-dark-green"
                    : "border-border text-text-secondary")
                }
              >
                {option}
              </div>
            ))}
          </div>

          <div className="mt-6 border-t border-border pt-4">
            <div className="mb-2 flex items-center justify-between text-caption text-text-secondary">
              <span>Adjusting difficulty</span>
              <span className="font-medium text-ku-green">Level up → B2</span>
            </div>
            <div className="flex gap-1">
              {SAMPLE_LEVELS.map((level, i) => (
                <div key={level} className="flex-1">
                  <div
                    className={
                      "h-2 rounded-badge " + (i <= 3 ? "bg-ku-green" : "bg-border")
                    }
                  />
                  <p
                    className={
                      "mt-1 text-center text-caption " +
                      (i === 3 ? "font-semibold text-ku-dark-green" : "text-text-secondary")
                    }
                  >
                    {level}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
