import { useMemo } from 'react';
import { RepData } from '@/lib/api';

export interface EvaluationSettings {
  hipLiftTolerance: number; // e.g. 0.15 (15% deviation allowed)
  depthTolerance: number;   // e.g. -0.05 (allow elbow to be 5% above shoulder)
}

export interface RepEvaluation {
  repIndex: number;
  isHipLiftFail: boolean;
  isShallowFail: boolean;
  isPass: boolean;
  data: RepData;
}

export const useRepEvaluation = (reps: RepData[] = [], settings: EvaluationSettings): RepEvaluation[] => {
  return useMemo(() => {
    if (!reps || reps.length === 0) return [];

    return reps.map((rep, index) => {
      // Hip Lift Check: Fail if deviation > tolerance
      const isHipLiftFail = rep.max_hip_deviation_ratio > settings.hipLiftTolerance;

      // Depth Check: Fail if max depth < tolerance
      // max_elbow_depth_ratio is: (ElbowY - ShoulderY) / Torso
      // Positive val = Deep/Below shoulder. Negative val = Shallow/Above shoulder.
      // e.g. If setting is -0.05 (allow slightly above), and user hits -0.02 (ok), it passes.
      // If user hits -0.10 (too shallow), it fails (-0.10 < -0.05).
      const isShallowFail = rep.max_elbow_depth_ratio < settings.depthTolerance;

      return {
        repIndex: index + 1,
        isHipLiftFail,
        isShallowFail,
        isPass: !isHipLiftFail && !isShallowFail,
        data: rep
      };
    });
  }, [reps, settings]);
};
