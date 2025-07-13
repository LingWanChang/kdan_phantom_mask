# Pharmacy Platform API Documentation

This document describes the API endpoints for the Pharmacy Platform, built with Flask and SQLAlchemy, using a PostgreSQL database. All endpoints return JSON responses and are hosted at `http://127.0.0.1:5000`.

## Table of Contents
1. [GET /pharmacies/open](#get-pharmaciesopen)
2. [GET /pharmacies/<pharmacy_name>/masks](#get-pharmaciespharmacy_namemasks)
3. [GET /pharmacies/mask_count](#get-pharmaciesmask_count)
4. [GET /users/top_by_transaction_amount](#get-userstop_by_transaction_amount)
5. [GET /masks/stats](#get-masksstats)
6. [GET /search](#get-search)

---

### GET /pharmacies/open
List all pharmacies that are open at the current time or a specified time.

#### Query Parameters
- `datetime` (optional, string, format: `YYYY-MM-DD HH:MM`): Check open pharmacies at a specific time. Defaults to current time.

#### Response
- **Status**: 200 OK
- **Body**: Array of pharmacy objects with `id`, `name`, `cash_balance`, and `opening_hours`.
- **Error**: 400 (invalid `datetime` format), 500 (server error).

#### Example
**Request**:
```bash
curl "http://127.0.0.1:5000/pharmacies/open?datetime=2023-01-01%2010:00"
```

**Response**:
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
List all masks available at a specific pharmacy.

#### Path Parameters
- `pharmacy_name` (string, required): Name of the pharmacy (case-sensitive).

#### Response
- **Status**: 200 OK
- **Body**: Array of mask objects with `id`, `name`, and `price`.
- **Error**: 404 (pharmacy not found), 500 (server error).

#### Example
**Request**:
```bash
curl "http://127.0.0.1:5000/pharmacies/Carepoint/masks"
```

**Response**:
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
List pharmacies with a number of mask products within a price range, either greater than or less than a specified count.

#### Query Parameters
- `min_price` (float, optional, default: 0.0): Minimum price of masks.
- `max_price` (float, required): Maximum price of masks.
- `count` (integer, optional, default: 0): Number of mask products threshold.
- `threshold` (string, optional, default: `gt`): Comparison type (`gt` for greater than, `lt` for less than).

#### Response
- **Status**: 200 OK
- **Body**: Array of pharmacy objects with `id`, `name`, `cash_balance`, `opening_hours`, and `mask_count`.
- **Error**: 400 (invalid parameters), 500 (server error).

#### Example
**Request**:
```bash
curl "http://127.0.0.1:5000/pharmacies/mask_count?min_price=1.0&max_price=5.0&count=2&threshold=gt"
```

**Response**:
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
List the top X users by total transaction amount within a date range.

#### Query Parameters
- `start_date` (string, required, format: `YYYY-MM-DD`): Start of date range.
- `end_date` (string, required, format: `YYYY-MM-DD`): End of date range.
- `x` (integer, optional, default: 10): Number of users to return.

#### Response
- **Status**: 200 OK
- **Body**: Array of user objects with `id`, `name`, and `total_transaction_amount`, sorted by `total_transaction_amount` in descending order.
- **Error**: 400 (invalid date format or range), 500 (server error).

#### Example
**Request**:
```bash
curl "http://127.0.0.1:5000/users/top_by_transaction_amount?start_date=2023-01-01&end_date=2023-12-31&x=5"
```

**Response**:
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
Calculate the total number of masks and total transaction amount within a date range.

#### Query Parameters
- `start_date` (string, required, format: `YYYY-MM-DD`): Start of date range.
- `end_date` (string, required, format: `YYYY-MM-DD`): End of date range.

#### Response
- **Status**: 200 OK
- **Body**: Object with `total_mask_count` (integer) and `total_transaction_amount` (float).
- **Error**: 400 (invalid date format or range), 500 (server error).

#### Example
**Request**:
```bash
curl "http://127.0.0.1:5000/masks/stats?start_date=2023-01-01&end_date=2023-12-31"
```

**Response**:
```json
{
    "total_mask_count": 150,
    "total_transaction_amount": 450.75
}
```

---

### GET /search
Search for pharmacies or masks by name, ranked by relevance (alphabetical order).

#### Query Parameters
- `query` (string, required): Search term for pharmacy or mask names (case-insensitive).

#### Response
- **Status**: 200 OK
- **Body**: Object with two arrays:
  - `pharmacies`: Array of pharmacy objects with `id`, `name`, `cash_balance`, and `opening_hours`.
  - `masks`: Array of mask objects with `id`, `name`, `price`, and `pharmacy_name`.
- **Error**: 400 (missing query), 500 (server error).

#### Example
**Request**:
```bash
curl "http://127.0.0.1:5000/search?query=Care"
```

**Response**:
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

## Error Handling
- **400 Bad Request**: Invalid or missing parameters (e.g., invalid date format, missing required parameters).
- **404 Not Found**: Resource not found (e.g., pharmacy name in `/pharmacies/<pharmacy_name>/masks`).
- **500 Internal Server Error**: Unexpected server issues (e.g., database connection failure).

## Notes
- All monetary values (`cash_balance`, `price`, `total_transaction_amount`) are returned as floats.
- Date parameters must follow the `YYYY-MM-DD` format.
- Time parameters (for `/pharmacies/open`) must follow the `YYYY-MM-DD HH:MM` format.
- Search is case-insensitive and uses fuzzy matching (`ILIKE` in PostgreSQL).