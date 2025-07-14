# 藥局平台 API 文件

本文件描述藥局平台的 API 端點，使用 Flask 和 SQLAlchemy 構建，搭配 PostgreSQL 資料庫。所有端點回傳 JSON 格式，伺服器地址為 `http://127.0.0.1:5000`。

## 目錄
1. [GET /pharmacies/open](#get-pharmaciesopen)
2. [GET /pharmacies/<pharmacy_name>/masks](#get-pharmaciespharmacy_namemasks)
3. [GET /pharmacies/mask_count](#get-pharmaciesmask_count)
4. [GET /users/top_by_transaction_amount](#get-userstop_by_transaction_amount)
5. [GET /masks/stats](#get-masksstats)
6. [GET /search](#get-search)

---

### GET /pharmacies/open
列出在指定時間和（可選）星期開放的藥局。

#### 查詢參數
time（必填，字串）：格式為 HH:MM（例如 14:30）。
day（選填，字串）：星期（例如 monday、tue），不區分大小寫。

#### 回應
- **內容**：藥局物件陣列，包含 `id`、 `name`、 `cash_balance` 和 `opening_hours`。

#### 範例
http://127.0.0.1:5000/pharmacies/open?time=14:30&day=monday

---

### GET /pharmacies/<pharmacy_name>/masks</id>
列出指定藥局的口罩清單，可按價格或名稱排序。

#### 查詢參數
pharmacy_name（必填）：藥局名稱or口罩名稱。
sort_by（選填，字串）：排序欄位（price 或 name）。
order（選填，字串）：排序方式（asc 或 desc）。

#### 回應
- **內容**：藥局物件陣列，包含 `id`、 `name`、 `cash_balance` 和 `opening_hours`。

#### 範例
http://127.0.0.1:5000/pharmacies/Carepoint/masks?sort_by=price&order=asc

---

### GET /pharmacies/mask_count
列出在指定價格範圍內，口罩數量大於或小於某數量的藥局。

#### 查詢參數
- `min_price`（浮點數，選填）：最低價格。
- `max_price`（浮點數，必填）：最高價格。
- `count`（整數，選填，預設：0）：口罩數量門檻。
- `threshold`（字串，選填，預設：`gt`）：比較類型（`gt` 表示大於，`lt` 表示小於）。

#### 回應
- **內容**：藥局物件陣列，包含 `id`、 `name`、 `cash_balance`、 `opening_hours` 和 `mask_count`。

#### 範例
http://127.0.0.1:5000/pharmacies/mask_count?min_price=10.0&max_price=30.0&count=2&threshold=gt

---

### GET /users/top_by_transaction_amount
列出指定日期範圍內交易總金額前 X 名的使用者。

#### 查詢參數
- `start_date`（字串，必填，格式：`YYYY-MM-DD`）：日期範圍起始。
- `end_date`（字串，必填，格式：`YYYY-MM-DD`）：日期範圍結束。
- `x`（整數，選填，預設：10）：返回的使用者數量。

#### 回應
- **內容**：使用者物件陣列，包含 `id`、 `name` 和 `total_transaction_amount`，按金額降序排列。

#### 範例
http://127.0.0.1:5000/users/top_by_transaction_amount?start_date=2021-01-01&end_date=2021-12-31&x=5

---

### GET /masks/stats
計算指定日期範圍內的口罩總數和交易總金額。

#### 查詢參數
- `start_date`（字串，必填，格式：`YYYY-MM-DD`）：日期範圍起始。
- `end_date`（字串，必填，格式：`YYYY-MM-DD`）：日期範圍結束。

#### 回應
- **內容**：物件，包含 `total_mask_count`（整數）和 `total_transaction_amount`（浮點數）。

#### 範例
http://127.0.0.1:5000/masks/stats?start_date=2021-01-01&end_date=2021-12-31

---

### GET /search
按名稱搜尋藥局或口罩，按相關性（字母順序）排序。

#### 查詢參數
- `query`（字串，必填）：藥局或口罩名稱的搜尋詞（不區分大小寫）。

#### 回應
- **內容**：物件，包含兩個陣列：
  - `pharmacies`：藥局物件陣列，包含 `id`、 `name`、 `cash_balance` 和 `opening_hours`。
  - `masks`：口罩物件陣列，包含 `id`、 `name`、 `price` 和 `pharmacy_name`。

#### 範例
**請求**：
http://127.0.0.1:5000/search?query=Care

- 搜尋不區分大小寫，使用模糊匹配（PostgreSQL 的 `ILIKE`）。


### POST /purchase
使用者購買口罩，可一次購買多項，且可來自不同藥局。

#### 參數
{
  "user_id": 整數，表示使用者的ID，
  "items": [
    {
      "pharmacy_id": 整數，表示藥局ID，
      "mask_id": 整數，表示口罩ID，
      "quantity": 正整數，表示購買數量（必須大於0）
    },
    ...
  ]
}

#### 範例
curl -X POST "http://127.0.0.1:5000/purchase" ^
-H "Content-Type: application/json" ^
-d "{\"user_id\": 1, \"items\": [{\"pharmacy_id\": 1, \"mask_id\": 1, \"quantity\": 2}]}"
