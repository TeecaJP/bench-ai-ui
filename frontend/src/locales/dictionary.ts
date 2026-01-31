export type Dictionary = {
  common: {
    backToLibrary: string;
    loading: string;
    processing: string;
    processingDesc: string;
    na: string;
  };
  status: {
    pending: string;
    processing: string;
    completed: string;
    failed: string;
    ok: string;
    goodLift: string;
    noLift: string;
  };
  analysis: {
    results: string;
    overallStatus: string;
    formAnalysis: string;
    videoInfo: string;
    hipLift: string;
    shallowRep: string;
    totalFrames: string;
    fps: string;
    duration: string;
    barHeightTitle: string;
    barHeightDesc: string;
  };
  repPanel: {
    title: string;
    criteriaTitle: string;
    criteriaDesc: string;
    hipTolerance: string;
    hipToleranceDesc: string;
    depthTolerance: string;
    depthToleranceDesc: string;
    result: string;
    repsOk: string;
    repDetails: string;
    noReps: string;
    rep: string;
    hipStability: string;
    depth: string;
    maxDeviation: string;
    margin: string;
  };
};
