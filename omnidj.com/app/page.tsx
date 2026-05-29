// Home page — sections will be filled in Phase 2
import HomeHero from '@/components/hero/HomeHero';
import ArtistCarousel from '@/components/artists/ArtistCarousel';
import EnterpriseTabs from '@/components/enterprise/EnterpriseTabs';
import ToolOverview from '@/components/overview/ToolOverview';
import WorkflowGrid from '@/components/workflow/WorkflowGrid';
import AutoModeSection from '@/components/automode/AutoModeSection';
import FeaturesAccordion from '@/components/features/FeaturesAccordion';
import RoadmapCarousel from '@/components/roadmap/RoadmapCarousel';
import ClosingCta from '@/components/cta/ClosingCta';

/**
 * Hairline divider between two adjacent dark sections.
 * Dark<->creme borders carry their own contrast, so a hairline is only used
 * where two dark sections meet (hero/artist, tool-overview/workflow, features/roadmap).
 */
function DarkSeam() {
  return <div aria-hidden="true" className="divider-creme" style={{ opacity: 0.5 }} />;
}

export default function HomePage() {
  return (
    <>
      <HomeHero />
      <DarkSeam />
      <ArtistCarousel />
      <EnterpriseTabs />
      <ToolOverview />
      <DarkSeam />
      <WorkflowGrid />
      <AutoModeSection />
      <FeaturesAccordion />
      <DarkSeam />
      <RoadmapCarousel />
      <ClosingCta />
    </>
  );
}
