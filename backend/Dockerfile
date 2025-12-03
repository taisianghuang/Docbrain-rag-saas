# 使用 uv 官方提供的 Python 3.11 映像檔 (基於 Debian Bookworm Slim)
# 這比自己安裝 python 再安裝 uv 更快且更穩定
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

WORKDIR /app

# 1. 設定環境變數
# UV_COMPILE_BYTECODE: 編譯 Python bytecode 加速啟動
# UV_LINK_MODE: 在 Docker 中使用 copy 模式 (避免 hardlink 問題)
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

# 2. 安裝系統依賴 (System Dependencies)
# 即使是 Slim 版，有些 Python 套件 (如 asyncpg, numpy 等) 可能仍需要編譯工具
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 3. 安裝 Python 依賴 (利用 uv.lock)
# --mount=type=cache: 快取 uv 的下載，加速重複構建
# --mount=type=bind: 直接讀取 host 的設定檔，不需要 COPY 進去再刪除
# --no-install-project: 先只安裝依賴，不安裝專案本身 (加速 caching)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# 4. 複製專案程式碼
COPY . /app

# 5. 將 .venv 加入 PATH
# uv 預設會在 /app/.venv 建立虛擬環境
ENV PATH="/app/.venv/bin:$PATH"

# 6. (可選) 安裝專案本身
# 如果您的專案是 package 形式才需要，普通 FastAPI app 這步通常只是檢查同步
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

EXPOSE 8000

# 啟動指令 (因為已經將 .venv 加入 PATH，可以直接呼叫 uvicorn)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]