# tax-accounting

税務・会計業務（帳簿レビュー、決算チェック、申告書レビュー、消費税・償却資産の書類作成）で再利用する手順・チェックリスト・教訓を置く場所。
会社が変わっても使える一般則だけを書く。顧問先固有の事実は書かない（それはメモリ `~/.claude/projects/C--claude/memory/` に置く）。

## どれを使うか

作業の順番は、帳簿レビュー → 申告書レビュー。

| 場面 | 読むファイル |
|---|---|
| 決算前の帳簿チェック（残高・タグ・重複・税区分・証憑突合） | [freee-closing-check-rules.md](freee-closing-check-rules.md)、論点別の観点は [bookkeeping-review-checklist.md](bookkeeping-review-checklist.md) |
| 月次チェック（13観点） | [freee-monthly-check-rules.md](freee-monthly-check-rules.md)（手順は skill `freee-monthly-check`） |
| 申告書レビュー（法人税・消費税・地方税） | [corporate-tax-return-review-checklist.md](corporate-tax-return-review-checklist.md) |
| 消費税計算書類（区分別表）の作成 | [consumption-tax-calc-sheet.md](consumption-tax-calc-sheet.md) |
| 固定資産台帳・償却資産申告（freee） | [freee-fixed-asset-depreciable-tax.md](freee-fixed-asset-depreciable-tax.md) |

## ファイル一覧

| ファイル | 中身 | 初版 |
|---|---|---|
| [bookkeeping-review-checklist.md](bookkeeping-review-checklist.md) | 帳簿（freee）レビューの論点別チェックリスト（前期決算整理仕訳の二重計上、桁違い、給与・源泉、消費税の納税義務、関係会社、債務超過） | 2026-10-18 |
| [corporate-tax-return-review-checklist.md](corporate-tax-return-review-checklist.md) | 法人税・消費税・地方税の申告書レビュー（登記簿突合、別表、地方税、概況書、内訳書、検算式） | 2026-09-23 |
| [freee-closing-check-rules.md](freee-closing-check-rules.md) | freee決算前チェック（機械チェックA〜H、誤検知の除外、証憑突合、HTML成果物の型） | 2026-10-14 |
| [freee-monthly-check-rules.md](freee-monthly-check-rules.md) | freee月次チェック13観点の定義（判定5区分、基準、対応文） | 2026-11-10 |
| [freee-fixed-asset-depreciable-tax.md](freee-fixed-asset-depreciable-tax.md) | freee固定資産台帳と償却資産申告（過年度少額資産のAPI登録、償却方法コード、提出先、前回申告書との突合） | 2026-11-13 |
| [consumption-tax-calc-sheet.md](consumption-tax-calc-sheet.md) | 消費税計算書類（区分別表）の作り方と使い方（シート構成、検算、更新手順） | 2026-11-13 |

## 更新ルール

- チェック・レビューのたびに、新しく見つけた一般則を該当ファイルに追記する。ユーザー指示がなくても自動で行う。
- 顧問先名・個人名・取引先名・固有金額は書かない。事例は付録に匿名で1行だけ。
- 条文・項番号は一次情報（e-Gov・国税庁）で確認してから書く。記憶では書かない。
- 追記したら別エージェントで根拠を照合してからコミットする。
- 大きなテーマ（相続・組織再編・国際税務など）が増えたら別ファイルに分け、上の表に追加する。
