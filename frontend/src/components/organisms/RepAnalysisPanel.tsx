import React, { useState } from 'react';
import { AnalyzeResponse } from '@/lib/api';
import { useRepEvaluation } from '@/hooks/useRepEvaluation';
import { useTranslation } from '@/hooks/useTranslation';
import { Slider } from '@/components/atoms/Slider';
import { Card } from '@/components/atoms/Card';
import { Badge } from '@/components/atoms/Badge';
import { CheckCircle2, XCircle, AlertCircle } from 'lucide-react';

interface RepAnalysisPanelProps {
  analysis: AnalyzeResponse;
  settings: {
    hipLiftTolerance: number;
    depthTolerance: number;
    bounceTolerance: number;
  };
  onSettingsChange: (settings: any) => void;
}

/**
 * Combined panel (legacy or simple use)
 */
export const RepAnalysisPanel: React.FC<RepAnalysisPanelProps> = ({ analysis, settings, onSettingsChange }) => {
  const evaluations = useRepEvaluation(analysis.reps, settings);

  return (
    <div className="space-y-6">
      <EvaluationSettings settings={settings} onSettingsChange={onSettingsChange} />
      <RepEvaluationList evaluations={evaluations} />
    </div>
  );
};

export const EvaluationSettings: React.FC<{
  settings: any;
  onSettingsChange: (settings: any) => void;
}> = ({ settings, onSettingsChange }) => {
  const { t } = useTranslation();

  return (
    <Card className="p-6 space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-1">{t.repPanel.criteriaTitle}</h3>
        <p className="text-sm text-muted-foreground">{t.repPanel.criteriaDesc}</p>
      </div>

      <div className="space-y-6">
        <Slider
          label={t.repPanel.hipTolerance}
          valueLabel={`${(settings.hipLiftTolerance * 100).toFixed(0)}%`}
          min={0.01}
          max={0.30}
          step={0.01}
          value={settings.hipLiftTolerance}
          onChange={(e) => onSettingsChange({ ...settings, hipLiftTolerance: parseFloat(e.target.value) })}
        />
        <p className="text-xs text-muted-foreground">
          {t.repPanel.hipToleranceDesc}
        </p>

        <Slider
          label={t.repPanel.depthTolerance}
          valueLabel={`${(settings.depthTolerance * 100).toFixed(0)}%`}
          min={-0.20}
          max={0.10}
          step={0.01}
          value={settings.depthTolerance}
          onChange={(e) => onSettingsChange({ ...settings, depthTolerance: parseFloat(e.target.value) })}
        />
        <p className="text-xs text-muted-foreground">
          {t.repPanel.depthToleranceDesc}
        </p>

        <Slider
          label={t.repPanel.bounceTolerance}
          valueLabel={`${(settings.bounceTolerance * 100).toFixed(0)}%`}
          min={0.01}
          max={0.50}
          step={0.01}
          value={settings.bounceTolerance}
          onChange={(e) => onSettingsChange({ ...settings, bounceTolerance: parseFloat(e.target.value) })}
        />
        <p className="text-xs text-muted-foreground">
          {t.repPanel.bounceToleranceDesc}
        </p>
      </div>
    </Card>
  );
};

export const RepEvaluationList: React.FC<{ evaluations: any[] }> = ({ evaluations }) => {
  const { t } = useTranslation();
  const passedReps = evaluations.filter(e => e.isPass).length;
  const totalReps = evaluations.length;

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-end">
        <h3 className="text-lg font-semibold">{t.repPanel.repDetails}</h3>
        <div className="text-sm font-medium">
          {passedReps} <span className="text-muted-foreground font-normal">/ {totalReps} {t.repPanel.repsOk}</span>
        </div>
      </div>

      {evaluations.length === 0 ? (
        <div className="text-muted-foreground p-4 border border-dashed rounded-lg text-center">
          {t.repPanel.noReps}
        </div>
      ) : (
        <div className="space-y-3 pr-2">
          {evaluations.map((rep) => (
            <Card
              key={rep.repIndex}
              className={`p-4 border-l-4 ${rep.isPass ? 'border-l-green-500' : 'border-l-destructive'}`}
            >
              <div className="flex justify-between items-start mb-2">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-lg">{t.repPanel.rep} {rep.repIndex}</span>
                  {rep.isPass ? (
                    <Badge variant="default" className="bg-green-600 hover:bg-green-700">{t.status.goodLift}</Badge>
                  ) : (
                    <Badge variant="destructive">{t.status.noLift}</Badge>
                  )}
                </div>
                <div className="text-xs text-muted-foreground">
                  {rep.data.rep_duration.toFixed(1)}s
                </div>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm mt-3">
                {/* Hip Lift Metric */}
                <div className="space-y-1">
                  <div className="flex items-center gap-1 text-muted-foreground">
                    <span>{t.repPanel.hipStability}</span>
                    {rep.isHipLiftFail ? <XCircle className="w-4 h-4 text-destructive" /> : <CheckCircle2 className="w-4 h-4 text-green-500" />}
                  </div>
                  <div className="font-medium">
                    {t.repPanel.maxDeviation}: <span className={rep.isHipLiftFail ? "text-destructive" : ""}>{(rep.data.max_hip_deviation_ratio * 100).toFixed(1)}%</span>
                  </div>
                </div>

                {/* Depth Metric */}
                <div className="space-y-1">
                  <div className="flex items-center gap-1 text-muted-foreground">
                    <span>{t.repPanel.depth}</span>
                    {rep.isShallowFail ? <AlertCircle className="w-4 h-4 text-destructive" /> : <CheckCircle2 className="w-4 h-4 text-green-500" />}
                  </div>
                  <div className="font-medium">
                    {t.repPanel.margin}: <span className={rep.isShallowFail ? "text-destructive" : ""}>{(rep.data.max_elbow_depth_ratio * 100).toFixed(1)}%</span>
                  </div>
                </div>

                {/* Bounce Metric */}
                <div className="space-y-1">
                  <div className="flex items-center gap-1 text-muted-foreground">
                    <span>{t.repPanel.bounce}</span>
                    {rep.isBounceFail ? <XCircle className="w-4 h-4 text-destructive" /> : <CheckCircle2 className="w-4 h-4 text-green-500" />}
                  </div>
                  <div className="font-medium">
                    {t.repPanel.maxAcceleration}: <span className={rep.isBounceFail ? "text-destructive" : ""}>{(rep.data.max_upward_acceleration_ratio * 100).toFixed(1)}%</span>
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};
