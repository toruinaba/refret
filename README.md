# Guitar Lesson Review App (RefRet)

ギターレッスンの音源をアップロードし、ボーカル（会話）と楽器（ギター演奏）を分離、会話内容を文字起こし・要約するStreamlitアプリケーションです。

## 機能概要

1.  **音源分離 (Audio Separation)**
    *   **Demucs** (Hybrid Transformer Demucs) モデルを使用。
    *   アップロードされた音源から「ボーカル（会話）」と「ギター/バッキングトラック」を分離します。
    *   **特徴**: ギターのみのトラックを作成する際、単純な引き算ではなく、ドラム・ベース・その他のステムを合成することで、会話の音声をきれいに除去しています。

2.  **文字起こし (Transcription)**
    *   **Faster-Whisper** を使用。
    *   分離されたボーカルトラックから会話内容をテキスト化します。
    *   日本語（`language="ja"`）に最適化された `small` モデルを使用し、高速かつ高精度な認識を実現しています。

3.  **要約 (Summarization)**
    *   **LLM (Large Language Model)** を統合。
    *   文字起こしテキストから、レッスンの要点、登場したコード、練習フレーズなどを抽出・要約します。
    *   **OpenAI API** (GPT-3.5/4/4o-mini等) および **Ollama** (ローカルLLM) の両方に対応。

4.  **ライブラリ管理**
    *   過去に解析したレッスンデータをローカル (`data/`) に保存し、いつでも再確認可能です。

## インストールとセットアップ

### 必要条件
*   Python 3.13 以上
*   [FFmpeg](https://ffmpeg.org/) (システムパスに通っていること)

### インストール手順

1.  リポジトリをクローンまたはダウンロードします。

2.  依存ライブラリをインストールします。
    ```bash
    pip install -r requirements.txt
    ```

3.  環境変数ファイル `.env` を作成し、LLMの設定を行います。
    ```bash
    # .env ファイルの例

    # OpenAIを使用する場合
    LLM_PROVIDER=openai
    OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxx
    LLM_MODEL=gpt-4o-mini

    # Ollama (ローカル) を使用する場合
    # LLM_PROVIDER=ollama
    # LLM_MODEL=llama3
    ```

### 実行方法

以下のコマンドでアプリケーションを起動します。

```bash
streamlit run app.py
```

ブラウザが立ち上がり、アプリが表示されます。「New Lesson」サイドバーから音声ファイルをアップロードして解析を開始してください。

## トラブルシューティング

*   **依存関係エラー**: `soundfile` や `av` 関連のエラーが出る場合は、OSのライブラリ不足の可能性があります（Macの場合は `brew install ffmpeg` 等を確認）。
*   **分離に時間がかかる**: Demucsの処理はCPU負荷が高いです。初回実行時はモデルのダウンロードも行われます。
