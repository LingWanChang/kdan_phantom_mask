# 使用 Python 3.8 基礎映像
FROM python:3.8-slim

# 設置工作目錄
WORKDIR /app

# 複製 requirements.txt 並安裝依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式程式碼
COPY . .

# 暴露 Flask 預設端口
EXPOSE 5000

# 啟動應用程式
CMD ["python", "app.py"]