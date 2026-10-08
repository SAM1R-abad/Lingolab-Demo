import {
  ClipboardCheck,
  Stethoscope,
  Route,
  BookOpen,
  Dumbbell,
  Award,
  TrendingUp,
} from "lucide-react";

const STAGES = [
  {
    step: "01",
    icon: ClipboardCheck,
    title: "Assess",
    description: "An adaptive placement test detects your CEFR level per skill, not just overall.",
  },
  {
    step: "02",
    icon: Stethoscope,
    title: "Diagnose",
    description: "A skill-by-skill report shows exactly where you're strong and where to improve.",
  },
  {
    step: "03",
    icon: Route,
    title: "Personalize",
    description: "Your results shape a learning route and weekly plan built around your gaps.",
  },
  {
    step: "04",
    icon: BookOpen,
    title: "Learn",
    description: "Reading, listening, grammar, and vocabulary material matched to your level.",
  },
  {
    step: "05",
    icon: Dumbbell,
    title: "Practice",
    description: "Exercises, flashcards, and quizzes turn material into working knowledge.",
  },
  {
    step: "06",
    icon: Award,
    title: "Certify",
    description: "Level exams and digital certificates recognize what you've achieved.",
  },
  {
    step: "07",
    icon: TrendingUp,
    title: "Progress",
    description: "A CEFR progress tracker follows your development over time.",
  },
];

export function PipelineSection() {
  return (
    <section id="pipeline" className="bg-ku-dark-green py-16 md:py-24">
      <div className="mx-auto max-w-desktop px-4 md:px-8">
        <p className="text-small font-medium uppercase tracking-wide text-ku-soft-green">
          The LingoLab model
        </p>
        <h2 className="mt-2 text-h1 text-white">
          One continuous cycle, not one static course.
        </h2>
        <div className="mt-12 grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          {STAGES.map((stage) => (
            <div
              key={stage.step}
              className="rounded-card border border-white/10 bg-white/5 p-6"
            >
              <div className="flex items-center gap-3">
                <span className="text-caption font-semibold text-ku-soft-green">
                  {stage.step}
                </span>
                <stage.icon className="h-5 w-5 text-ku-soft-green" aria-hidden="true" />
              </div>
              <h3 className="mt-3 text-h4 text-white">{stage.title}</h3>
              <p className="mt-2 text-small text-white/70">{stage.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
