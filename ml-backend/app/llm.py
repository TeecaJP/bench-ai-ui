import os
import google.generativeai as genai
from typing import List, Dict, Any

class GeminiClient:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-3-flash-preview')
        else:
            self.model = None

    def generate_feedback(self, reps: List[Dict[str, Any]]) -> str:
        """
        Generate coaching feedback based on rep metrics.
        """
        if not self.model:
            return "API Keyが設定されていないため、フィードバックを生成できません。"

        if not reps:
            return "レップが検出されなかったため、具体的なアドバイスが生成できませんでした。撮影角度や照明を確認してください。"

        # Summarize rep data for the prompt
        summary_lines = []
        for i, rep in enumerate(reps):
            summary_lines.append(
                f"Rep {i+1}: "
                f"尻上げ最大値 {rep.get('max_hip_deviation_ratio', 0):.2f}, "
                f"最大深さ {rep.get('max_elbow_depth_ratio', 0):.2f}, "
                f"最大上昇加速度 {rep.get('max_upward_acceleration_ratio', 0):.2f}"
            )
        
        reps_summary = "\n".join(summary_lines)

        prompt = f"""
あなたはパワーリフティングの審判員資格と、ボディビル・筋肥大トレーニングの高度な知識を併せ持つマスター・コーチです。
ユーザーの目的は「重量向上」または「筋肥大」です。解析データに基づき、プロの視点で分析してください。

### 解析データ（全{len(reps)}レップ）
{reps_summary}

### 解析データの解釈ガイドライン（コーチ用）
1. **お尻の浮き (max_hip_deviation_ratio)**:
   - 0.05以上はパワーリフティングでは「試技失敗（判定：不可）」、筋肥大目的でも「代償動作（大胸筋からの負荷の逃げ）」とみなします。足裏の踏ん張りをアドバイスしてください。

2. **ボトムの深さ (max_elbow_depth_ratio)**:
   - 筋肥大には「大胸筋の最大ストレッチ」が重要です。0.15以上を理想とし、0.05未満の場合は、可動域を広げ負荷を筋肉に乗せるよう促してください。

3. **バウンド/加速 (max_upward_acceleration_ratio)**:
   - ボトムでの急激な加速（跳ね返り）は、筋肥大においては「筋肉の緊張（Tension）が抜ける瞬間」としてネガティブに捉えます。コントロールされた動作を推奨してください。
   - 一方でパワー向上の場合は爆発力を称賛してください。

### 回答の構成ルール
以下の3段構成、合計200文字程度で回答してください：

1. **【総評】**: セット全体の質を簡潔に。
2. **【詳細分析】**: 数値が顕著だったレップ（例：3レップ目のお尻の浮き等）を具体的に指摘。
3. **【実践へのヒント】**: 肥大や重量向上のために、次のセットで意識すべき「感覚（キュー）」や「動作のコツ」を1つだけ提示。
"""

        try:
            # Use gemini-1.5-flash-latest for better compatibility
            # Logging prompt for debug
            print(f"Generating feedback for {len(reps)} reps...")
            response = self.model.generate_content(prompt)
            print("Feedback generated successfully.")
            return response.text.strip()
        except Exception as e:
            print(f"Error generating feedback: {str(e)}")
            import traceback
            traceback.print_exc()
            return "フィードバックの生成中にエラーが発生しました。"
