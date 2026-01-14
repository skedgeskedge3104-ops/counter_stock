# Dockerfile
# Ubuntu 22.04 LTS (Jammy Jellyfish) をベースイメージとして使用
FROM ubuntu:22.04


# 環境変数の設定 (Pythonのバッファリングを無効化し、コンテナログを即座に出力)
ENV PYTHONUNBUFFERED=1


# システムの更新と必要なパッケージ（PostgreSQLのクライアントライブラリ、Python、curl）のインストール
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libpq-dev \
        python3-pip \
        curl \
    && rm -rf /var/lib/apt/lists/*


# --- 💡 最終修正箇所: uvのインストールとPATH設定 ---
# uvをインストールし、インストール先 (/root/.local/bin) をPATHに追加
# StepごとにPATHを明示的に設定しないと、次のRUNコマンドに引き継がれないため、
# ENVコマンドでグローバルに設定します。
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
# uvのインストール先を環境変数PATHに追加
ENV PATH="/root/.local/bin:${PATH}"


# 作業ディレクトリの設定
WORKDIR /counter


# アプリケーションコードのコピー
COPY . /counter


# uvを使って依存関係をインストール
# ENVでPATHが設定されたため、ここでuvが実行可能です
COPY requirements.txt .
RUN uv pip install --system -r requirements.txt


# --- ここに2行追加 ---
# 1. ホストからwait-for-it.shをコンテナの/appにコピー
COPY wait-for-it.sh .


# 2. 実行権限を付与
RUN chmod +x wait-for-it.sh
# ----------------------


# ポートの公開 (Flask/Gunicornのデフォルトポート)
EXPOSE 8081