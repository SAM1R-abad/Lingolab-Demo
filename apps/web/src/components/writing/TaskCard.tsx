"use client";

import Link from "next/link";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import type { WritingTask } from "@/services/types";

export function TaskCard({ task }: { task: WritingTask }) {
  return (
    <Link href={`/dashboard/writing/${task.id}`}>
      <Card className="flex h-full flex-col gap-3 transition-shadow hover:shadow-md">
        <div className="flex aspect-[4/3] items-center justify-center overflow-hidden rounded-input bg-background">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={task.svg_url}
            alt={`Illustration for the "${task.title}" writing task`}
            className="h-full w-full object-contain p-2"
          />
        </div>
        <div className="flex items-center justify-between gap-2">
          <h3 className="text-h4 text-text-primary">{task.title}</h3>
          {task.target_level && <Badge tone="green">{task.target_level}</Badge>}
        </div>
        <p className="line-clamp-2 text-small text-text-secondary">{task.prompt}</p>
        <p className="mt-auto text-caption text-text-secondary">At least {task.min_word_count} words</p>
      </Card>
    </Link>
  );
}
