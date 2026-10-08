import { LandingNav } from "@/components/landing/LandingNav";
import { Hero } from "@/components/landing/Hero";
import { PipelineSection } from "@/components/landing/PipelineSection";
import { SkillsSection } from "@/components/landing/SkillsSection";
import { CTASection } from "@/components/landing/CTASection";
import { Footer } from "@/components/layout/Footer";

export default function HomePage() {
  return (
    <div className="min-h-screen bg-background">
      <LandingNav />
      <main>
        <Hero />
        <PipelineSection />
        <SkillsSection />
        <CTASection />
      </main>
      <Footer />
    </div>
  );
}
