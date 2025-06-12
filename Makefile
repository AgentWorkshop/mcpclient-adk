.PHONY: init install run-local check-env test

# 默認目標
all: init install run-local

# 初始化：檢查 .env 文件
init: check-env
	@echo "✅ 初始化完成"

# 檢查 .env 文件是否存在且不包含默認值
check-env:
	@if [ ! -f .env ]; then \
		echo "❌ .env 文件不存在！"; \
		echo "請根據 .env.sample 創建 .env 文件"; \
		exit 1; \
	fi
	@if grep -q "YOUR_VALUE_HERE" .env; then \
		echo "❌ .env 文件中包含默認值 'YOUR_VALUE_HERE'"; \
		echo "請更新您的 API 密鑰"; \
		exit 1; \
	fi
	@if grep -q "YOUR_PROJECT_ID" .env; then \
		echo "❌ .env 文件中包含默認值 'YOUR_PROJECT_ID'"; \
		echo "請更新您的 Google Cloud 項目 ID"; \
		exit 1; \
	fi
	@echo "✅ .env 文件檢查通過"

# 安裝依賴
install:
	@echo "📦 安裝依賴..."
	pip install -r requirements.txt
	@echo "✅ 依賴安裝完成"

# 運行本地服務器並打開瀏覽器
run-local:
	@echo "🚀 啟動本地服務器..."
	@(sleep 2 && open http://localhost:8000) & uvicorn main:app --reload

# 運行測試
test:
	@echo "🧪 運行測試..."
	python -m pytest
	@echo "✅ 測試完成"

# 幫助信息
help:
	@echo "可用命令："
	@echo "  make init       - 檢查 .env 文件是否存在且不包含默認值"
	@echo "  make install    - 安裝 requirements.txt 中的依賴"
	@echo "  make run-local  - 啟動本地服務器並自動打開瀏覽器"
	@echo "  make test       - 運行單元測試"
	@echo "  make all        - 執行以上所有命令"
	@echo "  make help       - 顯示此幫助信息"
