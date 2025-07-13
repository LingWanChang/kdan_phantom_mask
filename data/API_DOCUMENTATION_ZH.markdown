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
列出目前或指定時間開放的藥局。

#### 查詢參數
- `datetime`（選填，字串，格式：`YYYY-MM-DD HH:MM`）：指定檢查時間，預設為現在時間。

#### 回應
- **狀態碼**：200 OK
- **內容**：藥局物件陣列，包含 `id`、 `name`、 `cash_balance` 和 `opening_hours`。
- **錯誤**：400（日期格式錯誤）、500（伺服器錯誤）。

#### 範例
**請求**：
```bash
curl "http://127.0.0.1:5000/pharmacies/open?datetime=2023-01-01%2010:00"
```

**回應**：
```json
[
    {
        "id": 2,
        "name": "Carepoint",
        "cash_balance": 593.35,
        "opening_hours": "Mon - Fri 08:00 - 17:00"
    }
]
```

---

### GET /pharmacies/<pharmacy_name>/masks
列出指定藥局的所有口罩。

#### 路徑參數
- `pharmacy_name`（字串，必填）：藥局名稱（區分大小寫）。

#### 回應
- **狀態碼**：200 OK
- **內容**：口罩物件陣列，包含 `id`、 `name` 和 `price`。
- **錯誤**：404（藥局不存在）、500（伺服器錯誤）。

#### 範例
**請求**：
```bash
curl "http://127.0.0.1:5000/pharmacies/Carepoint/masks"
```

**回應**：
```json
[
    {
        "id": 3,
        "name": "CareMask Pro",
        "price": 2.00
    }
]
```

---

### GET /pharmacies/mask_count
列出在指定價格範圍內，口罩數量大於或小於某數量的藥局。

#### 查詢參數
- `min_price`（浮點數，選填，預設：0.0）：最低價格。
- `max_price`（浮點數，必填）：最高價格。
- `count`（整數，選填，預設：0）：口罩數量門檻。
- `threshold`（字串，選填，預設：`gt`）：比較類型（`gt` 表示大於，`lt` 表示小於）。

#### 回應
- **狀態碼**：200 OK
- **內容**：藥局物件陣列，包含 `id`、 `name`、 `cash_balance`、 `opening_hours` 和 `mask_count`。
- **錯誤**：400（參數無效）、500（伺服器錯誤）。

#### 範例
**請求**：
```bash
curl "http://127.0.0.1:5000/pharmacies/mask_count?min_price=1.0&max_price=5.0&count=2&threshold=gt"
```

**回應**：
```json
[
    {
        "id": 2,
        "name": "Carepoint",
        "cash_balance": 593.35,
        "opening_hours": "Mon - Fri 08:00 - 17:00",
        "mask_count": 3
    }
]
```

---

### GET /users/top_by_transaction_amount
列出指定日期範圍內交易總金額前 X 名的使用者。

#### 查詢參數
- `start_date`（字串，必填，格式：`YYYY-MM-DD`）：日期範圍起始。
- `end_date`（字串，必填，格式：`YYYY-MM-DD`）：日期範圍結束。
- `x`（整數，選填，預設：10）：返回的使用者數量。

#### 回應
- **狀態碼**：200 OK
- **內容**：使用者物件陣列，包含 `id`、 `name` 和 `total_transaction_amount`，按金額降序排列。
- **錯誤**：400（日期格式或範圍錯誤）、500（伺服器錯誤）。

#### 範例
**請求**：
```bash
curl "http://127.0.0.1:5000/users/top_by_transaction_amount?start_date=2023-01-01&end_date=2023-12-31&x=5"
```

**回應**：
```json
[
    {
        "id": 1,
        "name": "John Doe",
        "total_transaction_amount": 150.50
    }
]
```

---

### GET /masks/stats
計算指定日期範圍內的口罩總數和交易總金額。

#### 查詢參數
- `start_date`（字串，必填，格式：`YYYY-MM-DD`）：日期範圍起始。
- `end_date`（字串，必填，格式：`YYYY-MM-DD`）：日期範圍結束。

#### 回應
- **狀態碼**：200 OK
- **內容**：物件，包含 `total_mask_count`（整數）和 `total_transaction_amount`（浮點數）。
- **錯誤**：400（日期格式或範圍錯誤）、500（伺服器錯誤）。

#### 範例
**請求**：
```bash
curl "http://127.0.0.1:5000/masks/stats?start_date=2023-01-01&end_date=2023-12-31"
```

**回應**：
```json
{
    "total_mask_count": 150,
    "total_transaction_amount": 450.75
}
```

---

### GET /search
按名稱搜尋藥局或口罩，按相關性（字母順序）排序。

#### 查詢參數
- `query`（字串，必填）：藥局或口罩名稱的搜尋詞（不區分大小寫）。

#### 回應
- **狀態碼**：200 OK
- **內容**：物件，包含兩個陣列：
  - `pharmacies`：藥局物件陣列，包含 `id`、 `name`、 `cash_balance` 和 `opening_hours`。
  - `masks`：口罩物件陣列，包含 `id`、 `name`、 `price` 和 `pharmacy_name`。
- **錯誤**：400（缺少搜尋詞）、500（伺服器錯誤）。

#### 範例
**請求**：
```bash
curl "http://127.0.0.1:5000/search?query=Care"
```

**回應**：
```json
{
    "pharmacies": [
        {
            "id": 2,
            "name": "Carepoint",
            "cash_balance": 593.35,
            "opening_hours": "Mon - Fri 08:00 - 17:00"
        }
    ],
    "masks": [
        {
            "id": 3,
            "name": "CareMask Pro",
            "pharmacy_name": "Carepoint",
            "price": 2.00
        }
    ]
}
```

---

## 錯誤處理
- **400 錯誤請求**：參數無效或缺少（例如日期格式錯誤、缺少必要參數）。
- **404 未找到**：資源不存在（例如 `/pharmacies/<pharmacy_name>/masks` 中的藥局名稱）。
- **500 伺服器錯誤**：意外問題（例如資料庫連接失敗）。

## 注意事項
- 所有金額欄位（`cash_balance`、 `price`、 `total_transaction_amount`）回傳為浮點數。
- 日期參數需為 `YYYY-MM-DD` 格式。
- 時間參數（`/pharmacies/open`）需為 `YYYY-MM-DD HH:MM` 格式。
- 搜尋不區分大小寫，使用模糊匹配（PostgreSQL 的 `ILIKE`）。