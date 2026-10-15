# アーキテクチャ

アプリを機能ごとのモジュールに分け、起動と画面遷移を `app.py` に集約しています。画面部品は保存処理やBMI計算の実装を直接持たず、必要な処理をアプリ制御層または `Storage` に依頼します。

## 起動と画面遷移

```text
BMI_cal.py → app.main() → App
                         ├─ AuthScreen → Storage
                         └─ BMI入力画面
                              ├─ DatePicker
                              ├─ HistoryGraphPanel
                              └─ HistoryEditor → Storage
```

`App` は認証画面と計算画面を切り替えます。ログイン成功時に `Storage` からユーザーの最新身長と履歴を読み込み、計算画面へ渡します。計算後は履歴を保存してグラフを更新します。

## モジュール

| ファイル | 役割 |
| --- | --- |
| `BMI_cal.py` | 起動用エントリーポイント |
| `app.py` | 画面遷移、計算、各画面部品の接続 |
| `auth_screen.py` | ログインとユーザー登録 |
| `storage.py` | SQLiteスキーマ、認証、設定、履歴の保存と読み込み |
| `bmi_logic.py` | BMI計算と区分判定。Tkinterに依存しない処理 |
| `date_picker.py` | 年・月・日の選択とカレンダーポップアップ |
| `history_graph.py` | BMI、身長、体重のグラフと凡例 |
| `history_editor.py` | 過去の測定履歴の一覧と編集 |
| `ui_style.py` | 共通配色、ボタン、入力欄 |

## SQLiteデータ

データベースはOSユーザーのアプリデータ領域に保存します。`users` はソルト付きパスワードハッシュ、`app_settings` は自動ログイン設定、`bmi_history` はユーザーID・測定日・身長・体重・BMIを保持します。履歴の読み書きは常にユーザーIDで絞り込みます。

過去のバージョンの履歴テーブルは起動時に必要な列を追加して移行します。アカウントがまだない状態で作られた履歴は、最初に登録したユーザーへ割り当てます。
