import { useMemo } from 'react';
import { RepData } from '@/lib/api';

export interface EvaluationSettings {
  hipLiftTolerance: number; // e.g. 0.15 (15% deviation allowed)
  depthTolerance: number;   // e.g. -0.05 (allow elbow to be 5% above shoulder)
  bounceTolerance: number;  // e.g. 0.10 (normalized acceleration threshold)
}

export interface RepEvaluation {
  repIndex: number;
  isHipLiftFail: boolean;
  isShallowFail: boolean;
  isBounceFail: boolean;
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
      const isShallowFail = rep.max_elbow_depth_ratio < settings.depthTolerance;

      // Bounce Check: Fail if acceleration > tolerance
      const isBounceFail = rep.max_upward_acceleration_ratio > settings.bounceTolerance;

      return {
        repIndex: index + 1,
        isHipLiftFail,
        isShallowFail,
        isBounceFail,
        isPass: !isHipLiftFail && !isShallowFail && !isBounceFail,
        data: rep
      };
    });
  }, [reps, settings]);
};
