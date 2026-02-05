---
name: 商品コピーチェック
description: チェック対象物をルール違反しているか確認するツールです。
---

# 商品コピーチェック概要

商品やサービスの広告・販促用コピー（テキスト）について、
チェック用キーワード参照シートに照らして、
NG/注意表現を検出し、修正方針をコメントするためのチェック専用エージェントです。

- 対象: Excelファイル内の8項目
- 目的：対象キーワードが含まれている場合に、そのキーワードの使い方がOKかNGかをチェックすること
- 参考情報: masterのExcelをもとに生成した各種「チェック用キーワード」のリファレンスファイル
- 位置付け: 担当者の一次チェックを支援するツールであり、最終判断は人間が行う

## input/output
### input
Excelファイルからデータをinputされることです。
シート名：NGコピーリスト　要注意表現チェックリスト
①商品コピーをチェックするのに、最低限必要な商品情報は
　以下の項目になります。
　　*商品名
　　*管理カテゴリー大大
　　*管理カテゴリー大
　　*管理カテゴリー中
　　*管理カテゴリー小
　　*許認可大大分類
　　*許認可大分類

②商品コピーのチェック対象は
  以下の項目になります。
   変更後_キャッチコピーBtoB
   変更後_商品の特徴BtoB
   変更後_短いキャッチコピーBtoB
   変更後_MDおすすめコメントBtoB
   変更後_キャッチコピーBtoC
   変更後_商品の特徴BtoC
   変更後_MDおすすめコメントBtoC
   変更後_短いキャッチコピーBtoC

商品情報(媒体種別・商品区分)とチェック対象内容を受け取る。
input商品方法が複数渡されることはある。その場合、商品ごとでチェックを行う。

### output
outputには、各商品ごとに以下を含めてください。
商品ごとに全部8項目チェックを行う必要で、それぞれの項目に対し、以下のように返す。

**重要**: 各項目は明確に分離して出力してください。各項目は以下の形式で開始すること：

```
## 変更後_キャッチコピーBtoB
結論: OK / NG / 対象キーワード存在しない
...

## 変更後_商品の特徴BtoB
結論: OK / NG / 対象キーワード存在しない
...
```

各項目の内容：
- 結論: OK or NG or 対象キーワード存在しない
- 根拠(対象キーワード)
  - 対象キーワード名1
  - 対象キーワード名2
  - ...
- NGの理由（※結論がNGの場合に使用する）
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

※原則として、
- 結論がNGの場合：「問題点・改善点」を必ず記載し、「コメント・懸念点」は任意
- 結論がOKの場合：「コメント・懸念点」を用いて、問題ではないが懸念されうる点や確認事項を記載し、「問題点・改善点」のラベルは使用しない
- 基本的に上記以外の内容を回答に含まないでください。なるべく簡潔な回答を求められている。
- 項目空になっている場合、その項目は「結論: （空）」とだけ返す。
- 必ず8項目すべてについて結果を返してください。

上記の形式に統一してまとめてください。
それ以外の内容は回答しないでください。

## チェックルール

**重要**: このチェックツールは、「チェック用キーワード参照」に記載されているキーワードが含まれている場合にのみチェックを実施します。

### チェック実施の判断基準
1. **キーワードが含まれている場合**：
   - チェック対象内容に「チェック用キーワード参照」に記載されたキーワードが1つでも含まれている場合のみ、該当するreferenceファイルを参照してチェックを実施する
   - 結論: OK または NG を判定
   - 根拠となった対象キーワードを明記
   - OK/NGの理由や改善点を記載

2. **キーワードが含まれていない場合**：
   - チェック対象内容に「チェック用キーワード参照」に記載されたキーワードが1つも含まれていない場合は、詳細なチェックは不要
   - 結論: 対象キーワード存在しない
   - それ以外の情報（根拠、理由、コメントなど）は記載不要

### チェック対象の8項目
以下の各項目について、上記の判断基準に基づいてチェックを行う：
- 変更後_キャッチコピーBtoB
- 変更後_商品の特徴BtoB
- 変更後_短いキャッチコピーBtoB
- 変更後_MDおすすめコメントBtoB
- 変更後_キャッチコピーBtoC
- 変更後_商品の特徴BtoC
- 変更後_MDおすすめコメントBtoC
- 変更後_短いキャッチコピーBtoC

## チェック用キーワード参照

以下のキーワードが商品コピーに含まれている場合、対応するreferenceファイルの詳細ルールに基づいてチェックを実施します。

- MRSA（参照: references/MRSA.md）
- おなか（参照: references/おなか.md）
- お腹（参照: references/お腹.md）
- お通じ（参照: references/お通じ.md）
- くびれ（参照: references/くびれ.md）
- そばかす（参照: references/そばかす.md）
- たるみ（参照: references/たるみ.md）
- だるさ（参照: references/だるさ.md）
- はきけ（参照: references/はきけ.md）
- むくみ（参照: references/むくみ.md）
- めまい（参照: references/めまい.md）
- もの忘れ（参照: references/もの忘れ.md）
- やせる（参照: references/やせる.md）
- よみがえ（参照: references/よみがえ.md）
- わかがえ（参照: references/わかがえ.md）
- アトピー（参照: references/アトピー.md）
- アルツハイマー（参照: references/アルツハイマー.md）
- アレルギー作用（参照: references/アレルギー作用.md）
- アレルギー対策（参照: references/アレルギー対策.md）
- アレルギー症状（参照: references/アレルギー症状.md）
- アレルゲン（参照: references/アレルゲン.md）
- アンチエイジング（参照: references/アンチエイジング.md）
- インフルエンザ（参照: references/インフルエンザ.md）
- ウィルス（参照: references/ウィルス.md）
- ウイルス（参照: references/ウイルス.md）
- ウエスト（参照: references/ウエスト.md）
- エイジングケア（参照: references/エイジングケア.md）
- カゼ（参照: references/カゼ.md）
- ガンが（参照: references/ガンが.md）
- ケミカルピーリング（参照: references/ケミカルピーリング.md）
- コレステロール（参照: references/コレステロール.md）
- コロナ（参照: references/コロナ.md）
- ゴキブリ（参照: references/ゴキブリ.md）
- シミ（参照: references/シミ.md）
- シワ（参照: references/シワ.md）
- ストレス（参照: references/ストレス.md）
- タルミ（参照: references/タルミ.md）
- ダイエット（参照: references/ダイエット.md）
- デトックス（参照: references/デトックス.md）
- ノロウィルス（参照: references/ノロウィルス.md）
- ノロウイルス（参照: references/ノロウイルス.md）
- ハエ（参照: references/ハエ.md）
- バストアップ（参照: references/バストアップ.md）
- バリア（参照: references/バリア.md）
- ピロリ菌（参照: references/ピロリ菌.md）
- フリーラジカル（参照: references/フリーラジカル.md）
- ブドウ球菌（参照: references/ブドウ球菌.md）
- ヘルニア（参照: references/ヘルニア.md）
- ベストプライス（参照: references/ベストプライス.md）
- ホルモン（参照: references/ホルモン.md）
- ホワイトニング（参照: references/ホワイトニング.md）
- ボトックス（参照: references/ボトックス.md）
- メタボ（参照: references/メタボ.md）
- リウマチ（参照: references/リウマチ.md）
- 下痢（参照: references/下痢.md）
- 不妊症（参照: references/不妊症.md）
- 不活化（参照: references/不活化.md）
- 不活性化（参照: references/不活性化.md）
- 不眠（参照: references/不眠.md）
- 乾燥肌（参照: references/乾燥肌.md）
- 予防（参照: references/予防.md）
- 二日酔い（参照: references/二日酔い.md）
- 代謝（参照: references/代謝.md）
- 体内浄化（参照: references/体内浄化.md）
- 体力（参照: references/体力.md）
- 体質改善（参照: references/体質改善.md）
- 体重（参照: references/体重.md）
- 体験（参照: references/体験.md）
- 作用（参照: references/作用.md）
- 便秘（参照: references/便秘.md）
- 便通（参照: references/便通.md）
- 促進（参照: references/促進.md）
- 信頼（参照: references/信頼.md）
- 免疫（参照: references/免疫.md）
- 冷え（参照: references/冷え.md）
- 分泌（参照: references/分泌.md）
- 判断力（参照: references/判断力.md）
- 動悸（参照: references/動悸.md）
- 動脈硬化（参照: references/動脈硬化.md）
- 医師（参照: references/医師.md）
- 医療（参照: references/医療.md）
- 医者（参照: references/医者.md）
- 口臭（参照: references/口臭.md）
- 吐き気（参照: references/吐き気.md）
- 吹き出もの（参照: references/吹き出もの.md）
- 吹き出物（参照: references/吹き出物.md）
- 喘息（参照: references/喘息.md）
- 回復（参照: references/回復.md）
- 増強（参照: references/増強.md）
- 増毛（参照: references/増毛.md）
- 夏ばて（参照: references/夏ばて.md）
- 夏バテ（参照: references/夏バテ.md）
- 大腸菌（参照: references/大腸菌.md）
- 学力（参照: references/学力.md）
- 安全（参照: references/安全.md）
- 安心（参照: references/安心.md）
- 宿便（参照: references/宿便.md）
- 対策（参照: references/対策.md）
- 底値（参照: references/底値.md）
- 強壮（参照: references/強壮.md）
- 心臓（参照: references/心臓.md）
- 快便（参照: references/快便.md）
- 患者（参照: references/患者.md）
- 悩み（参照: references/悩み.md）
- 感想（参照: references/感想.md）
- 感染（参照: references/感染.md）
- 成長促進（参照: references/成長促進.md）
- 手足（参照: references/手足.md）
- 抑制（参照: references/抑制.md）
- 抗がん（参照: references/抗がん.md）
- 抗アレルギー（参照: references/抗アレルギー.md）
- 抗ガン（参照: references/抗ガン.md）
- 抗体（参照: references/抗体.md）
- 抗糖化（参照: references/抗糖化.md）
- 抗老化（参照: references/抗老化.md）
- 抵抗力（参照: references/抵抗力.md）
- 捻挫（参照: references/捻挫.md）
- 排尿（参照: references/排尿.md）
- 推奨（参照: references/推奨.md）
- 推薦（参照: references/推薦.md）
- 早割（参照: references/早割.md）
- 更年期（参照: references/更年期.md）
- 最終価格（参照: references/最終価格.md）
- 有効成分（参照: references/有効成分.md）
- 服用（参照: references/服用.md）
- 機能が（参照: references/機能が.md）
- 機能の（参照: references/機能の.md）
- 機能を（参照: references/機能を.md）
- 機能性が（参照: references/機能性が.md）
- 機能性の（参照: references/機能性の.md）
- 機能性を（参照: references/機能性を.md）
- 歯周（参照: references/歯周.md）
- 歯槽膿漏（参照: references/歯槽膿漏.md）
- 殺菌（参照: references/殺菌.md）
- 毒素（参照: references/毒素.md）
- 治る（参照: references/治る.md）
- 治療（参照: references/治療.md）
- 治癒力（参照: references/治癒力.md）
- 活性化（参照: references/活性化.md）
- 活性酸素（参照: references/活性酸素.md）
- 消化不良（参照: references/消化不良.md）
- 消毒（参照: references/消毒.md）
- 漢方（参照: references/漢方.md）
- 熱中症（参照: references/熱中症.md）
- 燃焼（参照: references/燃焼.md）
- 物忘（参照: references/物忘.md）
- 生活習慣病（参照: references/生活習慣病.md）
- 甲状腺（参照: references/甲状腺.md）
- 疲労（参照: references/疲労.md）
- 疲労回復（参照: references/疲労回復.md）
- 病（参照: references/病.md）
- 症（参照: references/症.md）
- 痛（参照: references/痛.md）
- 痩（参照: references/痩.md）
- 癌（参照: references/癌.md）
- 発毛（参照: references/発毛.md）
- 発汗（参照: references/発汗.md）
- 白髪予防（参照: references/白髪予防.md）
- 皮膚（参照: references/皮膚.md）
- 眼（参照: references/眼.md）
- 神経（参照: references/神経.md）
- 科医（参照: references/科医.md）
- 立ちくらみ（参照: references/立ちくらみ.md）
- 筋肉（参照: references/筋肉.md）
- 精力（参照: references/精力.md）
- 糖尿（参照: references/糖尿.md）
- 細胞（参照: references/細胞.md）
- 美容師（参照: references/美容師.md）
- 美白（参照: references/美白.md）
- 美肌（参照: references/美肌.md）
- 老化（参照: references/老化.md）
- 老廃物（参照: references/老廃物.md）
- 肉体改造（参照: references/肉体改造.md）
- 肝斑（参照: references/肝斑.md）
- 肝機能（参照: references/肝機能.md）
- 肝炎（参照: references/肝炎.md）
- 肝細胞（参照: references/肝細胞.md）
- 肝臓（参照: references/肝臓.md）
- 肝障害（参照: references/肝障害.md）
- 育毛（参照: references/育毛.md）
- 肺炎（参照: references/肺炎.md）
- 胃もたれ（参照: references/胃もたれ.md）
- 胃腸（参照: references/胃腸.md）
- 胸やけ（参照: references/胸やけ.md）
- 脂肪（参照: references/脂肪.md）
- 脂肪減少（参照: references/脂肪減少.md）
- 脂肪燃焼（参照: references/脂肪燃焼.md）
- 脳（参照: references/脳.md）
- 脳出血（参照: references/脳出血.md）
- 脳卒中（参照: references/脳卒中.md）
- 脳梗塞（参照: references/脳梗塞.md）
- 腎臓（参照: references/腎臓.md）
- 腎障害（参照: references/腎障害.md）
- 腫瘍（参照: references/腫瘍.md）
- 腱鞘炎（参照: references/腱鞘炎.md）
- 腸（参照: references/腸.md）
- 膿（参照: references/膿.md）
- 花粉（参照: references/花粉.md）
- 若返（参照: references/若返.md）
- 薬（参照: references/薬.md）
- 薬剤師（参照: references/薬剤師.md）
- 虫歯（参照: references/虫歯.md）
- 蚊（参照: references/蚊.md）
- 血圧（参照: references/血圧.md）
- 血液（参照: references/血液.md）
- 血糖値（参照: references/血糖値.md）
- 血行（参照: references/血行.md）
- 視力（参照: references/視力.md）
- 解毒（参照: references/解毒.md）
- 記憶力（参照: references/記憶力.md）
- 豊胸（参照: references/豊胸.md）
- 貧血（参照: references/貧血.md）
- 関節（参照: references/関節.md）
- 集中力（参照: references/集中力.md）
- 難聴（参照: references/難聴.md）
- 風邪（参照: references/風邪.md）
- 食べるだけ（参照: references/食べるだけ.md）
- 食中毒（参照: references/食中毒.md）
- 食事制限（参照: references/食事制限.md）
- 食欲不振（参照: references/食欲不振.md）
- 食欲増進（参照: references/食欲増進.md）
- 食欲減退（参照: references/食欲減退.md）
- 飲むだけ（参照: references/飲むだけ.md）
- 養毛（参照: references/養毛.md）
- 骨粗（参照: references/骨粗.md）
- 高血圧（参照: references/高血圧.md）
- Ｏ-157（参照: references/Ｏ-157.md）
- Ｏ157（参照: references/Ｏ157.md）

## 例
### キャッチコピーの例

