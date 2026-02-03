---
name: 商品コピーチェック
description: チェック対象物をルール違反しているか確認するツールです。
---

# 商品コピーチェック概要

商品やサービスの広告・販促用コピー（テキスト）について、
薬機法・景表法などの関連法令および社内ローカルルールに照らして、
NG/注意表現を検出し、修正方針をコメントするためのチェック専用エージェントです。

- 対象: Excelファイルの8項目があります。
- 目的：対象キーワードがあった場合、それらのキーワードの使い方OK/NGかチェックすること。
- 参考情報: masterのExcelをもとに生成した各種「チェック用キーワード」のリファレンスファイル
- 位置付け: 担当者の一次チェックを支援するツールであり、最終判断は人間が行う

## input/output
### input
Excelファイルからデータをinputされることです。
シート名：NGコピーリスト　要注意表現チェックリスト
①商品コピーをチェックするのに、最低限必要な商品情報は
　以下の項目になります。
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
- OK or NG or 対象キーワード存在しない
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
- 項目空になっている場合、（空文字で）何も返さないようにする。

上記の形式に統一してまとめてください。
それ以外の内容は回答しないでください。

## チェックルール
  以下の8項目それぞれ以下のようにチェックを行い。
   変更後_キャッチコピーBtoB
   変更後_商品の特徴BtoB
   変更後_短いキャッチコピーBtoB
   変更後_MDおすすめコメントBtoB
   変更後_キャッチコピーBtoC
   変更後_商品の特徴BtoC
   変更後_MDおすすめコメントBtoC
   変更後_短いキャッチコピーBtoC
チェック対象内容の中に「チェック用キーワード参照」に記載されたチェック用キーワードが含まれている場合は、該当する各referenceファイルを参照しながらチェックを行ってください。
キーワードが存在しない場合(チェック用キーワード参照に記載がない)、対象キーワード存在しないだけを返す。

## チェック用キーワード参照
- MRSA: backend/skills/商品コピーチェック/references/MRSA.md に参照
- おなか: backend/skills/商品コピーチェック/references/おなか.md に参照
- お腹: backend/skills/商品コピーチェック/references/お腹.md に参照
- お通じ: backend/skills/商品コピーチェック/references/お通じ.md に参照
- くびれ: backend/skills/商品コピーチェック/references/くびれ.md に参照
- そばかす: backend/skills/商品コピーチェック/references/そばかす.md に参照
- たるみ: backend/skills/商品コピーチェック/references/たるみ.md に参照
- だるさ: backend/skills/商品コピーチェック/references/だるさ.md に参照
- はきけ: backend/skills/商品コピーチェック/references/はきけ.md に参照
- むくみ: backend/skills/商品コピーチェック/references/むくみ.md に参照
- めまい: backend/skills/商品コピーチェック/references/めまい.md に参照
- もの忘れ: backend/skills/商品コピーチェック/references/もの忘れ.md に参照
- やせる: backend/skills/商品コピーチェック/references/やせる.md に参照
- よみがえ: backend/skills/商品コピーチェック/references/よみがえ.md に参照
- わかがえ: backend/skills/商品コピーチェック/references/わかがえ.md に参照
- アトピー: backend/skills/商品コピーチェック/references/アトピー.md に参照
- アルツハイマー: backend/skills/商品コピーチェック/references/アルツハイマー.md に参照
- アレルギー作用: backend/skills/商品コピーチェック/references/アレルギー作用.md に参照
- アレルギー対策: backend/skills/商品コピーチェック/references/アレルギー対策.md に参照
- アレルギー症状: backend/skills/商品コピーチェック/references/アレルギー症状.md に参照
- アレルゲン: backend/skills/商品コピーチェック/references/アレルゲン.md に参照
- アンチエイジング: backend/skills/商品コピーチェック/references/アンチエイジング.md に参照
- インフルエンザ: backend/skills/商品コピーチェック/references/インフルエンザ.md に参照
- ウィルス: backend/skills/商品コピーチェック/references/ウィルス.md に参照
- ウイルス: backend/skills/商品コピーチェック/references/ウイルス.md に参照
- ウエスト: backend/skills/商品コピーチェック/references/ウエスト.md に参照
- エイジングケア: backend/skills/商品コピーチェック/references/エイジングケア.md に参照
- カゼ: backend/skills/商品コピーチェック/references/カゼ.md に参照
- ガンが: backend/skills/商品コピーチェック/references/ガンが.md に参照
- ケミカルピーリング: backend/skills/商品コピーチェック/references/ケミカルピーリング.md に参照
- コレステロール: backend/skills/商品コピーチェック/references/コレステロール.md に参照
- コロナ: backend/skills/商品コピーチェック/references/コロナ.md に参照
- ゴキブリ: backend/skills/商品コピーチェック/references/ゴキブリ.md に参照
- シミ: backend/skills/商品コピーチェック/references/シミ.md に参照
- シワ: backend/skills/商品コピーチェック/references/シワ.md に参照
- ストレス: backend/skills/商品コピーチェック/references/ストレス.md に参照
- タルミ: backend/skills/商品コピーチェック/references/タルミ.md に参照
- ダイエット: backend/skills/商品コピーチェック/references/ダイエット.md に参照
- デトックス: backend/skills/商品コピーチェック/references/デトックス.md に参照
- ノロウィルス: backend/skills/商品コピーチェック/references/ノロウィルス.md に参照
- ノロウイルス: backend/skills/商品コピーチェック/references/ノロウイルス.md に参照
- ハエ: backend/skills/商品コピーチェック/references/ハエ.md に参照
- バストアップ: backend/skills/商品コピーチェック/references/バストアップ.md に参照
- バリア: backend/skills/商品コピーチェック/references/バリア.md に参照
- ピロリ菌: backend/skills/商品コピーチェック/references/ピロリ菌.md に参照
- フリーラジカル: backend/skills/商品コピーチェック/references/フリーラジカル.md に参照
- ブドウ球菌: backend/skills/商品コピーチェック/references/ブドウ球菌.md に参照
- ヘルニア: backend/skills/商品コピーチェック/references/ヘルニア.md に参照
- ベストプライス: backend/skills/商品コピーチェック/references/ベストプライス.md に参照
- ホルモン: backend/skills/商品コピーチェック/references/ホルモン.md に参照
- ホワイトニング: backend/skills/商品コピーチェック/references/ホワイトニング.md に参照
- ボトックス: backend/skills/商品コピーチェック/references/ボトックス.md に参照
- メタボ: backend/skills/商品コピーチェック/references/メタボ.md に参照
- リウマチ: backend/skills/商品コピーチェック/references/リウマチ.md に参照
- 下痢: backend/skills/商品コピーチェック/references/下痢.md に参照
- 不妊症: backend/skills/商品コピーチェック/references/不妊症.md に参照
- 不活化: backend/skills/商品コピーチェック/references/不活化.md に参照
- 不活性化: backend/skills/商品コピーチェック/references/不活性化.md に参照
- 不眠: backend/skills/商品コピーチェック/references/不眠.md に参照
- 乾燥肌: backend/skills/商品コピーチェック/references/乾燥肌.md に参照
- 予防: backend/skills/商品コピーチェック/references/予防.md に参照
- 二日酔い: backend/skills/商品コピーチェック/references/二日酔い.md に参照
- 代謝: backend/skills/商品コピーチェック/references/代謝.md に参照
- 体内浄化: backend/skills/商品コピーチェック/references/体内浄化.md に参照
- 体力: backend/skills/商品コピーチェック/references/体力.md に参照
- 体質改善: backend/skills/商品コピーチェック/references/体質改善.md に参照
- 体重: backend/skills/商品コピーチェック/references/体重.md に参照
- 体験: backend/skills/商品コピーチェック/references/体験.md に参照
- 作用: backend/skills/商品コピーチェック/references/作用.md に参照
- 便秘: backend/skills/商品コピーチェック/references/便秘.md に参照
- 便通: backend/skills/商品コピーチェック/references/便通.md に参照
- 促進: backend/skills/商品コピーチェック/references/促進.md に参照
- 信頼: backend/skills/商品コピーチェック/references/信頼.md に参照
- 免疫: backend/skills/商品コピーチェック/references/免疫.md に参照
- 冷え: backend/skills/商品コピーチェック/references/冷え.md に参照
- 分泌: backend/skills/商品コピーチェック/references/分泌.md に参照
- 判断力: backend/skills/商品コピーチェック/references/判断力.md に参照
- 動悸: backend/skills/商品コピーチェック/references/動悸.md に参照
- 動脈硬化: backend/skills/商品コピーチェック/references/動脈硬化.md に参照
- 医師: backend/skills/商品コピーチェック/references/医師.md に参照
- 医療: backend/skills/商品コピーチェック/references/医療.md に参照
- 医者: backend/skills/商品コピーチェック/references/医者.md に参照
- 口臭: backend/skills/商品コピーチェック/references/口臭.md に参照
- 吐き気: backend/skills/商品コピーチェック/references/吐き気.md に参照
- 吹き出もの: backend/skills/商品コピーチェック/references/吹き出もの.md に参照
- 吹き出物: backend/skills/商品コピーチェック/references/吹き出物.md に参照
- 喘息: backend/skills/商品コピーチェック/references/喘息.md に参照
- 回復: backend/skills/商品コピーチェック/references/回復.md に参照
- 増強: backend/skills/商品コピーチェック/references/増強.md に参照
- 増毛: backend/skills/商品コピーチェック/references/増毛.md に参照
- 夏ばて: backend/skills/商品コピーチェック/references/夏ばて.md に参照
- 夏バテ: backend/skills/商品コピーチェック/references/夏バテ.md に参照
- 大腸菌: backend/skills/商品コピーチェック/references/大腸菌.md に参照
- 学力: backend/skills/商品コピーチェック/references/学力.md に参照
- 安全: backend/skills/商品コピーチェック/references/安全.md に参照
- 安心: backend/skills/商品コピーチェック/references/安心.md に参照
- 宿便: backend/skills/商品コピーチェック/references/宿便.md に参照
- 対策: backend/skills/商品コピーチェック/references/対策.md に参照
- 底値: backend/skills/商品コピーチェック/references/底値.md に参照
- 強壮: backend/skills/商品コピーチェック/references/強壮.md に参照
- 心臓: backend/skills/商品コピーチェック/references/心臓.md に参照
- 快便: backend/skills/商品コピーチェック/references/快便.md に参照
- 患者: backend/skills/商品コピーチェック/references/患者.md に参照
- 悩み: backend/skills/商品コピーチェック/references/悩み.md に参照
- 感想: backend/skills/商品コピーチェック/references/感想.md に参照
- 感染: backend/skills/商品コピーチェック/references/感染.md に参照
- 成長促進: backend/skills/商品コピーチェック/references/成長促進.md に参照
- 手足: backend/skills/商品コピーチェック/references/手足.md に参照
- 抑制: backend/skills/商品コピーチェック/references/抑制.md に参照
- 抗がん: backend/skills/商品コピーチェック/references/抗がん.md に参照
- 抗アレルギー: backend/skills/商品コピーチェック/references/抗アレルギー.md に参照
- 抗ガン: backend/skills/商品コピーチェック/references/抗ガン.md に参照
- 抗体: backend/skills/商品コピーチェック/references/抗体.md に参照
- 抗糖化: backend/skills/商品コピーチェック/references/抗糖化.md に参照
- 抗老化: backend/skills/商品コピーチェック/references/抗老化.md に参照
- 抵抗力: backend/skills/商品コピーチェック/references/抵抗力.md に参照
- 捻挫: backend/skills/商品コピーチェック/references/捻挫.md に参照
- 排尿: backend/skills/商品コピーチェック/references/排尿.md に参照
- 推奨: backend/skills/商品コピーチェック/references/推奨.md に参照
- 推薦: backend/skills/商品コピーチェック/references/推薦.md に参照
- 早割: backend/skills/商品コピーチェック/references/早割.md に参照
- 更年期: backend/skills/商品コピーチェック/references/更年期.md に参照
- 最終価格: backend/skills/商品コピーチェック/references/最終価格.md に参照
- 有効成分: backend/skills/商品コピーチェック/references/有効成分.md に参照
- 服用: backend/skills/商品コピーチェック/references/服用.md に参照
- 機能が: backend/skills/商品コピーチェック/references/機能が.md に参照
- 機能の: backend/skills/商品コピーチェック/references/機能の.md に参照
- 機能を: backend/skills/商品コピーチェック/references/機能を.md に参照
- 機能性が: backend/skills/商品コピーチェック/references/機能性が.md に参照
- 機能性の: backend/skills/商品コピーチェック/references/機能性の.md に参照
- 機能性を: backend/skills/商品コピーチェック/references/機能性を.md に参照
- 歯周: backend/skills/商品コピーチェック/references/歯周.md に参照
- 歯槽膿漏: backend/skills/商品コピーチェック/references/歯槽膿漏.md に参照
- 殺菌: backend/skills/商品コピーチェック/references/殺菌.md に参照
- 毒素: backend/skills/商品コピーチェック/references/毒素.md に参照
- 治る: backend/skills/商品コピーチェック/references/治る.md に参照
- 治療: backend/skills/商品コピーチェック/references/治療.md に参照
- 治癒力: backend/skills/商品コピーチェック/references/治癒力.md に参照
- 活性化: backend/skills/商品コピーチェック/references/活性化.md に参照
- 活性酸素: backend/skills/商品コピーチェック/references/活性酸素.md に参照
- 消化不良: backend/skills/商品コピーチェック/references/消化不良.md に参照
- 消毒: backend/skills/商品コピーチェック/references/消毒.md に参照
- 漢方: backend/skills/商品コピーチェック/references/漢方.md に参照
- 熱中症: backend/skills/商品コピーチェック/references/熱中症.md に参照
- 燃焼: backend/skills/商品コピーチェック/references/燃焼.md に参照
- 物忘: backend/skills/商品コピーチェック/references/物忘.md に参照
- 生活習慣病: backend/skills/商品コピーチェック/references/生活習慣病.md に参照
- 甲状腺: backend/skills/商品コピーチェック/references/甲状腺.md に参照
- 疲労: backend/skills/商品コピーチェック/references/疲労.md に参照
- 疲労回復: backend/skills/商品コピーチェック/references/疲労回復.md に参照
- 病: backend/skills/商品コピーチェック/references/病.md に参照
- 症: backend/skills/商品コピーチェック/references/症.md に参照
- 痛: backend/skills/商品コピーチェック/references/痛.md に参照
- 痩: backend/skills/商品コピーチェック/references/痩.md に参照
- 癌: backend/skills/商品コピーチェック/references/癌.md に参照
- 発毛: backend/skills/商品コピーチェック/references/発毛.md に参照
- 発汗: backend/skills/商品コピーチェック/references/発汗.md に参照
- 白髪予防: backend/skills/商品コピーチェック/references/白髪予防.md に参照
- 皮膚: backend/skills/商品コピーチェック/references/皮膚.md に参照
- 眼: backend/skills/商品コピーチェック/references/眼.md に参照
- 神経: backend/skills/商品コピーチェック/references/神経.md に参照
- 科医: backend/skills/商品コピーチェック/references/科医.md に参照
- 立ちくらみ: backend/skills/商品コピーチェック/references/立ちくらみ.md に参照
- 筋肉: backend/skills/商品コピーチェック/references/筋肉.md に参照
- 精力: backend/skills/商品コピーチェック/references/精力.md に参照
- 糖尿: backend/skills/商品コピーチェック/references/糖尿.md に参照
- 細胞: backend/skills/商品コピーチェック/references/細胞.md に参照
- 美容師: backend/skills/商品コピーチェック/references/美容師.md に参照
- 美白: backend/skills/商品コピーチェック/references/美白.md に参照
- 美肌: backend/skills/商品コピーチェック/references/美肌.md に参照
- 老化: backend/skills/商品コピーチェック/references/老化.md に参照
- 老廃物: backend/skills/商品コピーチェック/references/老廃物.md に参照
- 肉体改造: backend/skills/商品コピーチェック/references/肉体改造.md に参照
- 肝斑: backend/skills/商品コピーチェック/references/肝斑.md に参照
- 肝機能: backend/skills/商品コピーチェック/references/肝機能.md に参照
- 肝炎: backend/skills/商品コピーチェック/references/肝炎.md に参照
- 肝細胞: backend/skills/商品コピーチェック/references/肝細胞.md に参照
- 肝臓: backend/skills/商品コピーチェック/references/肝臓.md に参照
- 肝障害: backend/skills/商品コピーチェック/references/肝障害.md に参照
- 育毛: backend/skills/商品コピーチェック/references/育毛.md に参照
- 肺炎: backend/skills/商品コピーチェック/references/肺炎.md に参照
- 胃もたれ: backend/skills/商品コピーチェック/references/胃もたれ.md に参照
- 胃腸: backend/skills/商品コピーチェック/references/胃腸.md に参照
- 胸やけ: backend/skills/商品コピーチェック/references/胸やけ.md に参照
- 脂肪: backend/skills/商品コピーチェック/references/脂肪.md に参照
- 脂肪減少: backend/skills/商品コピーチェック/references/脂肪減少.md に参照
- 脂肪燃焼: backend/skills/商品コピーチェック/references/脂肪燃焼.md に参照
- 脳: backend/skills/商品コピーチェック/references/脳.md に参照
- 脳出血: backend/skills/商品コピーチェック/references/脳出血.md に参照
- 脳卒中: backend/skills/商品コピーチェック/references/脳卒中.md に参照
- 脳梗塞: backend/skills/商品コピーチェック/references/脳梗塞.md に参照
- 腎臓: backend/skills/商品コピーチェック/references/腎臓.md に参照
- 腎障害: backend/skills/商品コピーチェック/references/腎障害.md に参照
- 腫瘍: backend/skills/商品コピーチェック/references/腫瘍.md に参照
- 腱鞘炎: backend/skills/商品コピーチェック/references/腱鞘炎.md に参照
- 腸: backend/skills/商品コピーチェック/references/腸.md に参照
- 膿: backend/skills/商品コピーチェック/references/膿.md に参照
- 花粉: backend/skills/商品コピーチェック/references/花粉.md に参照
- 若返: backend/skills/商品コピーチェック/references/若返.md に参照
- 薬: backend/skills/商品コピーチェック/references/薬.md に参照
- 薬剤師: backend/skills/商品コピーチェック/references/薬剤師.md に参照
- 虫歯: backend/skills/商品コピーチェック/references/虫歯.md に参照
- 蚊: backend/skills/商品コピーチェック/references/蚊.md に参照
- 血圧: backend/skills/商品コピーチェック/references/血圧.md に参照
- 血液: backend/skills/商品コピーチェック/references/血液.md に参照
- 血糖値: backend/skills/商品コピーチェック/references/血糖値.md に参照
- 血行: backend/skills/商品コピーチェック/references/血行.md に参照
- 視力: backend/skills/商品コピーチェック/references/視力.md に参照
- 解毒: backend/skills/商品コピーチェック/references/解毒.md に参照
- 記憶力: backend/skills/商品コピーチェック/references/記憶力.md に参照
- 豊胸: backend/skills/商品コピーチェック/references/豊胸.md に参照
- 貧血: backend/skills/商品コピーチェック/references/貧血.md に参照
- 関節: backend/skills/商品コピーチェック/references/関節.md に参照
- 集中力: backend/skills/商品コピーチェック/references/集中力.md に参照
- 難聴: backend/skills/商品コピーチェック/references/難聴.md に参照
- 風邪: backend/skills/商品コピーチェック/references/風邪.md に参照
- 食べるだけ: backend/skills/商品コピーチェック/references/食べるだけ.md に参照
- 食中毒: backend/skills/商品コピーチェック/references/食中毒.md に参照
- 食事制限: backend/skills/商品コピーチェック/references/食事制限.md に参照
- 食欲不振: backend/skills/商品コピーチェック/references/食欲不振.md に参照
- 食欲増進: backend/skills/商品コピーチェック/references/食欲増進.md に参照
- 食欲減退: backend/skills/商品コピーチェック/references/食欲減退.md に参照
- 飲むだけ: backend/skills/商品コピーチェック/references/飲むだけ.md に参照
- 養毛: backend/skills/商品コピーチェック/references/養毛.md に参照
- 骨粗: backend/skills/商品コピーチェック/references/骨粗.md に参照
- 高血圧: backend/skills/商品コピーチェック/references/高血圧.md に参照
- Ｏ-157: backend/skills/商品コピーチェック/references/Ｏ-157.md に参照
- Ｏ157: backend/skills/商品コピーチェック/references/Ｏ157.md に参照

## 例
### キャッチコピーの例

