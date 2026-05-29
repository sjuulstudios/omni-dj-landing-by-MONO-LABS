import React from 'react';
import { Composition } from 'remotion';
import { LogoReveal } from './compositions/LogoReveal';
import { AutoModePipeline } from './compositions/AutoModePipeline';
import { ToolOverviewFlow } from './compositions/ToolOverviewFlow';

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="LogoReveal"
        component={LogoReveal}
        durationInFrames={360}        // 12s at 30fps — entry then one full slow rotation, loops cleanly
        fps={30}
        width={800}
        height={800}
      />
      <Composition
        id="AutoModePipeline"
        component={AutoModePipeline}
        durationInFrames={240}        // 8s loop
        fps={30}
        width={1600}
        height={600}
      />
      <Composition
        id="ToolOverviewFlow"
        component={ToolOverviewFlow}
        durationInFrames={300}        // 10s loop
        fps={30}
        width={1600}
        height={600}
      />
    </>
  );
};
