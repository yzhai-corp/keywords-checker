---
name: 商品コピーチェック
description: チェック対象物をルール違反しているか確認するツールです。
---

# 商品コピーチェック概要

商品やサービスの広告・販促用コピー（テキスト）について、
薬機法・景表法などの関連法令および社内ローカルルールに照らして、
NG/注意表現を検出し、修正方針をコメントするためのチェック専用エージェントです。

- 対象: Webページ、バナー、LP、紙媒体、商品説明文、レビュー誘導文などの日本語テキスト
- 観点: 疾病・身体機能への効能効果、予防・治療の断定表現、誇大表示、根拠が不明確な表現 等
- 参考情報: masterのExcelをもとに生成した各種「チェック用キーワード」のリファレンスファイル
- 位置付け: 法務・薬事担当者の一次チェックを支援するツールであり、最終判断は人間が行う

## input/output
### input
チェック対象内容と、必要に応じて媒体種別・商品区分などの指示を受け取る。
input商品方法が複数渡されることはある。その場合、商品ごとでチェックを行う。

### output
チェック対象に対するチェック結果（問題箇所の指摘・理由・改善例など）を返す。
複数商品渡された場合、それぞれの回答をしてください。

outputには、各商品ごとに以下を含めてください。

- 商品名
  - 結論
    - OK or NG
  - 根拠(対象キーワード)
    - 対象キーワード名1
    - 対象キーワード名2
    - ...
  - 問題点・改善点（※結論がNGの場合に使用する）
    - 問題１
      - 問題となる原文
      - 理由
      - 修正案
    - 問題２
      - 問題となる原文
      - 理由
      - 修正案
    - 問題n
      - 問題となる原文
      - 理由
      - 修正案
  - コメント・懸念点（※結論がOKの場合に使用する）
    - 項目１
      - 内容（どの表現についてのコメントか）
      - 理由（OKと判断した根拠、または軽微な懸念）
      - 必要に応じた軽微な修正案（なければ「なし」で可）
    - 項目n
      - 内容
      - 理由
      - 修正案
- 商品名
  - 結論
    - OK or NG
  - 根拠(対象キーワード)
    - 対象キーワード名1
    - 対象キーワード名2
    - ...
  - 問題点・改善点（※結論がNGの場合に使用する）
    - 問題１
      - 問題となる原文
      - 理由
      - 修正案
    - 問題２
      - 問題となる原文
      - 理由
      - 修正案
    - 問題n
      - 問題となる原文
      - 理由
      - 修正案
  - コメント・懸念点（※結論がOKの場合に使用する）
    - 項目１
      - 内容
      - 理由
      - 修正案
    - 項目n
      - 内容
      - 理由
      - 修正案
- 商品名
  - 上記と同様の形式

※原則として、
- 結論がNGの場合：「問題点・改善点」を必ず記載し、「コメント・懸念点」は任意
- 結論がOKの場合：「コメント・懸念点」を用いて、問題ではないが懸念されうる点や確認事項を記載し、「問題点・改善点」のラベルは使用しない
- 基本的に上記以外の内容を回答に含まないでください。なるべく簡潔な回答を求められている。

上記の形式に統一してまとめてください。
それ以外の内容は回答しないでください。

## チェックルール
チェック対象内容の中に「チェック用キーワード参照」に記載されたチェック用キーワードが含まれている場合は、該当する各referenceファイルを参照しながらチェックを行ってください。
チェック用キーワード参照に記載がなくても、不自然なところがあれば指摘してください。

## チェック用キーワード参照
- MRSA: .github/skills/商品コピーチェック/references/MRSA.md に参照
- おなか: .github/skills/商品コピーチェック/references/おなか.md に参照
- お腹: .github/skills/商品コピーチェック/references/お腹.md に参照
- お通じ: .github/skills/商品コピーチェック/references/お通じ.md に参照
- くびれ: .github/skills/商品コピーチェック/references/くびれ.md に参照
- そばかす: .github/skills/商品コピーチェック/references/そばかす.md に参照
- たるみ: .github/skills/商品コピーチェック/references/たるみ.md に参照
- だるさ: .github/skills/商品コピーチェック/references/だるさ.md に参照
- はきけ: .github/skills/商品コピーチェック/references/はきけ.md に参照
- むくみ: .github/skills/商品コピーチェック/references/むくみ.md に参照
- めまい: .github/skills/商品コピーチェック/references/めまい.md に参照
- もの忘れ: .github/skills/商品コピーチェック/references/もの忘れ.md に参照
- やせる: .github/skills/商品コピーチェック/references/やせる.md に参照
- よみがえ: .github/skills/商品コピーチェック/references/よみがえ.md に参照
- わかがえ: .github/skills/商品コピーチェック/references/わかがえ.md に参照
- アトピー: .github/skills/商品コピーチェック/references/アトピー.md に参照
- アルツハイマー: .github/skills/商品コピーチェック/references/アルツハイマー.md に参照
- アレルギー作用: .github/skills/商品コピーチェック/references/アレルギー作用.md に参照
- アレルギー対策: .github/skills/商品コピーチェック/references/アレルギー対策.md に参照
- アレルギー症状: .github/skills/商品コピーチェック/references/アレルギー症状.md に参照
- アレルゲン: .github/skills/商品コピーチェック/references/アレルゲン.md に参照
- アンチエイジング: .github/skills/商品コピーチェック/references/アンチエイジング.md に参照
- インフルエンザ: .github/skills/商品コピーチェック/references/インフルエンザ.md に参照
- ウィルス: .github/skills/商品コピーチェック/references/ウィルス.md に参照
- ウイルス: .github/skills/商品コピーチェック/references/ウイルス.md に参照
- ウエスト: .github/skills/商品コピーチェック/references/ウエスト.md に参照
- エイジングケア: .github/skills/商品コピーチェック/references/エイジングケア.md に参照
- カゼ: .github/skills/商品コピーチェック/references/カゼ.md に参照
- ガンが: .github/skills/商品コピーチェック/references/ガンが.md に参照
- ケミカルピーリング: .github/skills/商品コピーチェック/references/ケミカルピーリング.md に参照
- コレステロール: .github/skills/商品コピーチェック/references/コレステロール.md に参照
- コロナ: .github/skills/商品コピーチェック/references/コロナ.md に参照
- ゴキブリ: .github/skills/商品コピーチェック/references/ゴキブリ.md に参照
- シミ: .github/skills/商品コピーチェック/references/シミ.md に参照
- シワ: .github/skills/商品コピーチェック/references/シワ.md に参照
- ストレス: .github/skills/商品コピーチェック/references/ストレス.md に参照
- タルミ: .github/skills/商品コピーチェック/references/タルミ.md に参照
- ダイエット: .github/skills/商品コピーチェック/references/ダイエット.md に参照
- デトックス: .github/skills/商品コピーチェック/references/デトックス.md に参照
- ノロウィルス: .github/skills/商品コピーチェック/references/ノロウィルス.md に参照
- ノロウイルス: .github/skills/商品コピーチェック/references/ノロウイルス.md に参照
- ハエ: .github/skills/商品コピーチェック/references/ハエ.md に参照
- バストアップ: .github/skills/商品コピーチェック/references/バストアップ.md に参照
- バリア: .github/skills/商品コピーチェック/references/バリア.md に参照
- ピロリ菌: .github/skills/商品コピーチェック/references/ピロリ菌.md に参照
- フリーラジカル: .github/skills/商品コピーチェック/references/フリーラジカル.md に参照
- ブドウ球菌: .github/skills/商品コピーチェック/references/ブドウ球菌.md に参照
- ヘルニア: .github/skills/商品コピーチェック/references/ヘルニア.md に参照
- ベストプライス: .github/skills/商品コピーチェック/references/ベストプライス.md に参照
- ホルモン: .github/skills/商品コピーチェック/references/ホルモン.md に参照
- ホワイトニング: .github/skills/商品コピーチェック/references/ホワイトニング.md に参照
- ボトックス: .github/skills/商品コピーチェック/references/ボトックス.md に参照
- メタボ: .github/skills/商品コピーチェック/references/メタボ.md に参照
- リウマチ: .github/skills/商品コピーチェック/references/リウマチ.md に参照
- 下痢: .github/skills/商品コピーチェック/references/下痢.md に参照
- 不妊症: .github/skills/商品コピーチェック/references/不妊症.md に参照
- 不活化: .github/skills/商品コピーチェック/references/不活化.md に参照
- 不活性化: .github/skills/商品コピーチェック/references/不活性化.md に参照
- 不眠: .github/skills/商品コピーチェック/references/不眠.md に参照
- 乾燥肌: .github/skills/商品コピーチェック/references/乾燥肌.md に参照
- 予防: .github/skills/商品コピーチェック/references/予防.md に参照
- 二日酔い: .github/skills/商品コピーチェック/references/二日酔い.md に参照
- 代謝: .github/skills/商品コピーチェック/references/代謝.md に参照
- 体内浄化: .github/skills/商品コピーチェック/references/体内浄化.md に参照
- 体力: .github/skills/商品コピーチェック/references/体力.md に参照
- 体質改善: .github/skills/商品コピーチェック/references/体質改善.md に参照
- 体重: .github/skills/商品コピーチェック/references/体重.md に参照
- 体験: .github/skills/商品コピーチェック/references/体験.md に参照
- 作用: .github/skills/商品コピーチェック/references/作用.md に参照
- 便秘: .github/skills/商品コピーチェック/references/便秘.md に参照
- 便通: .github/skills/商品コピーチェック/references/便通.md に参照
- 促進: .github/skills/商品コピーチェック/references/促進.md に参照
- 信頼: .github/skills/商品コピーチェック/references/信頼.md に参照
- 免疫: .github/skills/商品コピーチェック/references/免疫.md に参照
- 冷え: .github/skills/商品コピーチェック/references/冷え.md に参照
- 分泌: .github/skills/商品コピーチェック/references/分泌.md に参照
- 判断力: .github/skills/商品コピーチェック/references/判断力.md に参照
- 動悸: .github/skills/商品コピーチェック/references/動悸.md に参照
- 動脈硬化: .github/skills/商品コピーチェック/references/動脈硬化.md に参照
- 医師: .github/skills/商品コピーチェック/references/医師.md に参照
- 医療: .github/skills/商品コピーチェック/references/医療.md に参照
- 医者: .github/skills/商品コピーチェック/references/医者.md に参照
- 口臭: .github/skills/商品コピーチェック/references/口臭.md に参照
- 吐き気: .github/skills/商品コピーチェック/references/吐き気.md に参照
- 吹き出もの: .github/skills/商品コピーチェック/references/吹き出もの.md に参照
- 吹き出物: .github/skills/商品コピーチェック/references/吹き出物.md に参照
- 喘息: .github/skills/商品コピーチェック/references/喘息.md に参照
- 回復: .github/skills/商品コピーチェック/references/回復.md に参照
- 増強: .github/skills/商品コピーチェック/references/増強.md に参照
- 増毛: .github/skills/商品コピーチェック/references/増毛.md に参照
- 夏ばて: .github/skills/商品コピーチェック/references/夏ばて.md に参照
- 夏バテ: .github/skills/商品コピーチェック/references/夏バテ.md に参照
- 大腸菌: .github/skills/商品コピーチェック/references/大腸菌.md に参照
- 学力: .github/skills/商品コピーチェック/references/学力.md に参照
- 安全: .github/skills/商品コピーチェック/references/安全.md に参照
- 安心: .github/skills/商品コピーチェック/references/安心.md に参照
- 宿便: .github/skills/商品コピーチェック/references/宿便.md に参照
- 対策: .github/skills/商品コピーチェック/references/対策.md に参照
- 底値: .github/skills/商品コピーチェック/references/底値.md に参照
- 強壮: .github/skills/商品コピーチェック/references/強壮.md に参照
- 心臓: .github/skills/商品コピーチェック/references/心臓.md に参照
- 快便: .github/skills/商品コピーチェック/references/快便.md に参照
- 患者: .github/skills/商品コピーチェック/references/患者.md に参照
- 悩み: .github/skills/商品コピーチェック/references/悩み.md に参照
- 感想: .github/skills/商品コピーチェック/references/感想.md に参照
- 感染: .github/skills/商品コピーチェック/references/感染.md に参照
- 成長促進: .github/skills/商品コピーチェック/references/成長促進.md に参照
- 手足: .github/skills/商品コピーチェック/references/手足.md に参照
- 抑制: .github/skills/商品コピーチェック/references/抑制.md に参照
- 抗がん: .github/skills/商品コピーチェック/references/抗がん.md に参照
- 抗アレルギー: .github/skills/商品コピーチェック/references/抗アレルギー.md に参照
- 抗ガン: .github/skills/商品コピーチェック/references/抗ガン.md に参照
- 抗体: .github/skills/商品コピーチェック/references/抗体.md に参照
- 抗糖化: .github/skills/商品コピーチェック/references/抗糖化.md に参照
- 抗老化: .github/skills/商品コピーチェック/references/抗老化.md に参照
- 抵抗力: .github/skills/商品コピーチェック/references/抵抗力.md に参照
- 捻挫: .github/skills/商品コピーチェック/references/捻挫.md に参照
- 排尿: .github/skills/商品コピーチェック/references/排尿.md に参照
- 推奨: .github/skills/商品コピーチェック/references/推奨.md に参照
- 推薦: .github/skills/商品コピーチェック/references/推薦.md に参照
- 早割: .github/skills/商品コピーチェック/references/早割.md に参照
- 更年期: .github/skills/商品コピーチェック/references/更年期.md に参照
- 最終価格: .github/skills/商品コピーチェック/references/最終価格.md に参照
- 有効成分: .github/skills/商品コピーチェック/references/有効成分.md に参照
- 服用: .github/skills/商品コピーチェック/references/服用.md に参照
- 機能が: .github/skills/商品コピーチェック/references/機能が.md に参照
- 機能の: .github/skills/商品コピーチェック/references/機能の.md に参照
- 機能を: .github/skills/商品コピーチェック/references/機能を.md に参照
- 機能性が: .github/skills/商品コピーチェック/references/機能性が.md に参照
- 機能性の: .github/skills/商品コピーチェック/references/機能性の.md に参照
- 機能性を: .github/skills/商品コピーチェック/references/機能性を.md に参照
- 歯周: .github/skills/商品コピーチェック/references/歯周.md に参照
- 歯槽膿漏: .github/skills/商品コピーチェック/references/歯槽膿漏.md に参照
- 殺菌: .github/skills/商品コピーチェック/references/殺菌.md に参照
- 毒素: .github/skills/商品コピーチェック/references/毒素.md に参照
- 治る: .github/skills/商品コピーチェック/references/治る.md に参照
- 治療: .github/skills/商品コピーチェック/references/治療.md に参照
- 治癒力: .github/skills/商品コピーチェック/references/治癒力.md に参照
- 活性化: .github/skills/商品コピーチェック/references/活性化.md に参照
- 活性酸素: .github/skills/商品コピーチェック/references/活性酸素.md に参照
- 消化不良: .github/skills/商品コピーチェック/references/消化不良.md に参照
- 消毒: .github/skills/商品コピーチェック/references/消毒.md に参照
- 漢方: .github/skills/商品コピーチェック/references/漢方.md に参照
- 熱中症: .github/skills/商品コピーチェック/references/熱中症.md に参照
- 燃焼: .github/skills/商品コピーチェック/references/燃焼.md に参照
- 物忘: .github/skills/商品コピーチェック/references/物忘.md に参照
- 生活習慣病: .github/skills/商品コピーチェック/references/生活習慣病.md に参照
- 甲状腺: .github/skills/商品コピーチェック/references/甲状腺.md に参照
- 疲労: .github/skills/商品コピーチェック/references/疲労.md に参照
- 疲労回復: .github/skills/商品コピーチェック/references/疲労回復.md に参照
- 病: .github/skills/商品コピーチェック/references/病.md に参照
- 症: .github/skills/商品コピーチェック/references/症.md に参照
- 痛: .github/skills/商品コピーチェック/references/痛.md に参照
- 痩: .github/skills/商品コピーチェック/references/痩.md に参照
- 癌: .github/skills/商品コピーチェック/references/癌.md に参照
- 発毛: .github/skills/商品コピーチェック/references/発毛.md に参照
- 発汗: .github/skills/商品コピーチェック/references/発汗.md に参照
- 白髪予防: .github/skills/商品コピーチェック/references/白髪予防.md に参照
- 皮膚: .github/skills/商品コピーチェック/references/皮膚.md に参照
- 眼: .github/skills/商品コピーチェック/references/眼.md に参照
- 神経: .github/skills/商品コピーチェック/references/神経.md に参照
- 科医: .github/skills/商品コピーチェック/references/科医.md に参照
- 立ちくらみ: .github/skills/商品コピーチェック/references/立ちくらみ.md に参照
- 筋肉: .github/skills/商品コピーチェック/references/筋肉.md に参照
- 精力: .github/skills/商品コピーチェック/references/精力.md に参照
- 糖尿: .github/skills/商品コピーチェック/references/糖尿.md に参照
- 細胞: .github/skills/商品コピーチェック/references/細胞.md に参照
- 美容師: .github/skills/商品コピーチェック/references/美容師.md に参照
- 美白: .github/skills/商品コピーチェック/references/美白.md に参照
- 美肌: .github/skills/商品コピーチェック/references/美肌.md に参照
- 老化: .github/skills/商品コピーチェック/references/老化.md に参照
- 老廃物: .github/skills/商品コピーチェック/references/老廃物.md に参照
- 肉体改造: .github/skills/商品コピーチェック/references/肉体改造.md に参照
- 肝斑: .github/skills/商品コピーチェック/references/肝斑.md に参照
- 肝機能: .github/skills/商品コピーチェック/references/肝機能.md に参照
- 肝炎: .github/skills/商品コピーチェック/references/肝炎.md に参照
- 肝細胞: .github/skills/商品コピーチェック/references/肝細胞.md に参照
- 肝臓: .github/skills/商品コピーチェック/references/肝臓.md に参照
- 肝障害: .github/skills/商品コピーチェック/references/肝障害.md に参照
- 育毛: .github/skills/商品コピーチェック/references/育毛.md に参照
- 肺炎: .github/skills/商品コピーチェック/references/肺炎.md に参照
- 胃もたれ: .github/skills/商品コピーチェック/references/胃もたれ.md に参照
- 胃腸: .github/skills/商品コピーチェック/references/胃腸.md に参照
- 胸やけ: .github/skills/商品コピーチェック/references/胸やけ.md に参照
- 脂肪: .github/skills/商品コピーチェック/references/脂肪.md に参照
- 脂肪減少: .github/skills/商品コピーチェック/references/脂肪減少.md に参照
- 脂肪燃焼: .github/skills/商品コピーチェック/references/脂肪燃焼.md に参照
- 脳: .github/skills/商品コピーチェック/references/脳.md に参照
- 脳出血: .github/skills/商品コピーチェック/references/脳出血.md に参照
- 脳卒中: .github/skills/商品コピーチェック/references/脳卒中.md に参照
- 脳梗塞: .github/skills/商品コピーチェック/references/脳梗塞.md に参照
- 腎臓: .github/skills/商品コピーチェック/references/腎臓.md に参照
- 腎障害: .github/skills/商品コピーチェック/references/腎障害.md に参照
- 腫瘍: .github/skills/商品コピーチェック/references/腫瘍.md に参照
- 腱鞘炎: .github/skills/商品コピーチェック/references/腱鞘炎.md に参照
- 腸: .github/skills/商品コピーチェック/references/腸.md に参照
- 膿: .github/skills/商品コピーチェック/references/膿.md に参照
- 花粉: .github/skills/商品コピーチェック/references/花粉.md に参照
- 若返: .github/skills/商品コピーチェック/references/若返.md に参照
- 薬: .github/skills/商品コピーチェック/references/薬.md に参照
- 薬剤師: .github/skills/商品コピーチェック/references/薬剤師.md に参照
- 虫歯: .github/skills/商品コピーチェック/references/虫歯.md に参照
- 蚊: .github/skills/商品コピーチェック/references/蚊.md に参照
- 血圧: .github/skills/商品コピーチェック/references/血圧.md に参照
- 血液: .github/skills/商品コピーチェック/references/血液.md に参照
- 血糖値: .github/skills/商品コピーチェック/references/血糖値.md に参照
- 血行: .github/skills/商品コピーチェック/references/血行.md に参照
- 視力: .github/skills/商品コピーチェック/references/視力.md に参照
- 解毒: .github/skills/商品コピーチェック/references/解毒.md に参照
- 記憶力: .github/skills/商品コピーチェック/references/記憶力.md に参照
- 豊胸: .github/skills/商品コピーチェック/references/豊胸.md に参照
- 貧血: .github/skills/商品コピーチェック/references/貧血.md に参照
- 関節: .github/skills/商品コピーチェック/references/関節.md に参照
- 集中力: .github/skills/商品コピーチェック/references/集中力.md に参照
- 難聴: .github/skills/商品コピーチェック/references/難聴.md に参照
- 風邪: .github/skills/商品コピーチェック/references/風邪.md に参照
- 食べるだけ: .github/skills/商品コピーチェック/references/食べるだけ.md に参照
- 食中毒: .github/skills/商品コピーチェック/references/食中毒.md に参照
- 食事制限: .github/skills/商品コピーチェック/references/食事制限.md に参照
- 食欲不振: .github/skills/商品コピーチェック/references/食欲不振.md に参照
- 食欲増進: .github/skills/商品コピーチェック/references/食欲増進.md に参照
- 食欲減退: .github/skills/商品コピーチェック/references/食欲減退.md に参照
- 飲むだけ: .github/skills/商品コピーチェック/references/飲むだけ.md に参照
- 養毛: .github/skills/商品コピーチェック/references/養毛.md に参照
- 骨粗: .github/skills/商品コピーチェック/references/骨粗.md に参照
- 高血圧: .github/skills/商品コピーチェック/references/高血圧.md に参照
- Ｏ-157: .github/skills/商品コピーチェック/references/Ｏ-157.md に参照
- Ｏ157: .github/skills/商品コピーチェック/references/Ｏ157.md に参照

## 例
### キャッチコピーの例
- input
  - キャッチコピー:【泡タイプ・本体】薬用成分の泡ソープで洗浄・殺菌し手肌を清潔にします。 植物性油脂が主原料で手肌にやさしくたっぷり使えるお得な800ｍL詰換用です。
- output
  - 結論：NG
  - 修正後キャッチコピー:【泡タイプ・本体】薬用成分の泡ソープで洗浄・殺菌し手肌を清潔にします。 植物性油脂が主原料で手肌にやさしく使える200ｍL本体ボトルです。

- input
  - キャッチコピー:「減塩」に取り組む大田記念病品の管理栄養士によって監修。塩分や普段の食生活に気を遣われている方におすすめです。 レビューFD
- output
  - 結論：NG
  - 修正後キャッチコピー: 「減塩」に取り組む大田記念病品の管理栄養士によって監修。塩分や普段の食生活に気を遣われている方におすすめです。

### 商品特徴の例
- input
  - 商品特徴：「せき」と「たん」に特化。たんをともなうせきにも効くように設計された処方。非麻薬性鎮咳剤のデキストロメトルファン臭化水素酸塩水和物がせきをしずめ、ジプロフィリンが収縮した気管支を広げて気道を確保することで、せきをしずめるとともに、たんを出しやすくします。早く溶けて、長く効くダブルレイヤーアクション。徐放性顆粒の外側を速放性の層でおおった多重顆粒「早く溶けて、長く効く」を充填したカプセル剤で、1回1カプセルの服用で約12時間効果が持続します。
- output
  - 結論：NG
  - 修正後商品特徴：【セルフメディケーション税制対象商品】「せき」と「たん」に特化。たんをともなうせきにも効くように設計された処方。非麻薬性鎮咳剤のデキストロメトルファン臭化水素酸塩水和物がせきをしずめ、ジプロフィリンが収縮した気管支を広げて気道を確保することで、せきをしずめるとともに、たんを出しやすくします。早く溶けて、長く効くダブルレイヤーアクション。徐放性顆粒の外側を速放性の層でおおった多重顆粒「早く溶けて、長く効く」を充填したカプセル剤で、1回1カプセルの服用で約12時間効果が持続します。
