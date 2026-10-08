import { BookMarked, Headphones, Mic, PenLine, SpellCheck2, Text } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";

const SKILLS = [
  { icon: SpellCheck2, name: "Grammar", available: true },
  { icon: BookMarked, name: "Vocabulary", available: true },
  { icon: Text, name: "Reading", available: false },
  { icon: Headphones, name: "Listening", available: false },
  { icon: Mic, name: "Speaking", available: false },
  { icon: PenLine, name: "Writing", available: false },
];

export function SkillsSection() {
  return (
    <section id="modules" className="mx-auto max-w-desktop px-4 py-16 md:px-8 md:py-24">
      <p className="text-small font-medium uppercase tracking-wide text-ku-green">
        Skill-based assessment
      </p>
      <h2 className="mt-2 max-w-2xl text-h1 text-ku-dark-green">
        Six skills, tested and tracked separately.
      </h2>
      <p className="mt-4 max-w-2xl text-body text-text-secondary">
        Grammar and Vocabulary placement tests are live today, with 477
        CEFR-mapped questions across A1–C2. Reading, Listening, Speaking, and
        Writing are on the roadmap for upcoming sprints.
      </p>
      <div className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {SKILLS.map((skill) => (
          <Card key={skill.name} className="flex items-center gap-4">
            <div className="flex h-11 w-11 items-center justify-center rounded-input bg-ku-soft-green/50">
              <skill.icon className="h-5 w-5 text-ku-dark-green" aria-hidden="true" />
            </div>
            <div className="flex-1">
              <p className="text-h4 text-text-primary">{skill.name}</p>
            </div>
            <Badge tone={skill.available ? "success" : "neutral"}>
              {skill.available ? "Live" : "Coming soon"}
            </Badge>
          </Card>
        ))}
      </div>
    </section>
  );
}
