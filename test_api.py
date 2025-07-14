import pytest
import json
from app import app, expand_days, parse_opening_hours, is_open, is_pharmacy_open
from unittest.mock import patch
from datetime import datetime

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

# ---------- 原本既有 API 測試 ----------

def test_get_pharmacies_open(client):
    res = client.get("/pharmacies/open?time=14:30&day=monday")
    assert res.status_code == 200
    assert isinstance(res.get_json(), list)

def test_get_pharmacy_masks(client):
    res = client.get("/pharmacies/Carepoint/masks?sort_by=price&order=asc")
    assert res.status_code == 200
    assert isinstance(res.get_json(), list)

def test_get_pharmacies_mask_count(client):
    res = client.get("/pharmacies/mask_count?min_price=10&max_price=30&count=2&threshold=gt")
    assert res.status_code == 200
    assert isinstance(res.get_json(), list)

def test_get_top_users(client):
    res = client.get("/users/top_by_transaction_amount?start_date=2021-01-01&end_date=2021-12-31&x=5")
    assert res.status_code == 200
    assert isinstance(res.get_json(), list)

def test_get_mask_stats(client):
    res = client.get("/masks/stats?start_date=2021-01-01&end_date=2021-12-31")
    assert res.status_code == 200
    data = res.get_json()
    assert "total_mask_count" in data
    assert "total_transaction_amount" in data

def test_search(client):
    res = client.get("/search?query=Care")
    assert res.status_code == 200
    data = res.get_json()
    assert "pharmacies" in data
    assert "masks" in data

# 各類錯誤處理測試，包含缺參、格式錯誤等
def test_top_users_missing_params(client):
    res = client.get("/users/top_by_transaction_amount?start_date=2021-01-01")
    assert res.status_code == 400
    assert res.get_json().get("error") == "start_date and end_date are required"

def test_top_users_invalid_date_format(client):
    res = client.get("/users/top_by_transaction_amount?start_date=abc&end_date=2021-12-31")
    assert res.status_code == 400
    assert res.get_json().get("error") == "start_date and end_date must be in YYYY-MM-DD format"

def test_top_users_invalid_x(client):
    res = client.get("/users/top_by_transaction_amount?start_date=2021-01-01&end_date=2021-12-31&x=-1")
    assert res.status_code == 400
    assert res.get_json().get("error") == "x must be a positive integer"

def test_search_missing_query(client):
    res = client.get("/search")
    assert res.status_code == 400
    assert res.get_json().get("error") == "query parameter is required"

def test_pharmacies_open_missing_time(client):
    res = client.get("/pharmacies/open")
    assert res.status_code == 200
    data = res.get_json()
    assert isinstance(data, list)

def test_mask_count_missing_max_price(client):
    res = client.get("/pharmacies/mask_count")
    assert res.status_code == 400
    assert "max_price is required" == res.get_json().get("error")

def test_masks_stats_invalid_date_format(client):
    res = client.get("/masks/stats?start_date=invalid&end_date=2021-12-31")
    assert res.status_code == 400
    assert res.get_json().get("error") == "start_date and end_date must be in YYYY-MM-DD format"

def test_list_open_pharmacies_invalid_time(client):
    rv = client.get('/pharmacies/open?time=invalid')
    assert rv.status_code == 400
    assert b'Invalid time format' in rv.data

def test_list_open_pharmacies_with_day(client):
    rv = client.get('/pharmacies/open?time=10:00&day=Monday')
    assert rv.status_code == 200

def test_list_pharmacy_masks_not_found(client):
    rv = client.get('/pharmacies/masks/masks')
    assert rv.status_code == 404
    assert b'not found' in rv.data

def test_list_pharmacies_by_mask_count_missing_max_price(client):
    rv = client.get('/pharmacies/mask_count')
    assert rv.status_code == 400
    assert b'max_price is required' in rv.data

def test_list_top_users_missing_dates(client):
    rv = client.get('/users/top_by_transaction_amount')
    assert rv.status_code == 400
    assert b'start_date and end_date are required' in rv.data

def test_list_top_users_invalid_dates(client):
    rv = client.get('/users/top_by_transaction_amount?start_date=2025-01-01&end_date=2024-12-31')
    assert rv.status_code == 400
    assert b'end_date must be greater than or equal to start_date' in rv.data

def test_list_top_users_invalid_x(client):
    rv = client.get('/users/top_by_transaction_amount?start_date=2025-01-01&end_date=2025-01-31&x=0')
    assert rv.status_code == 400
    assert b'x must be a positive integer' in rv.data

def test_get_mask_stats_missing_dates(client):
    rv = client.get('/masks/stats')
    assert rv.status_code == 400
    assert b'start_date and end_date are required' in rv.data

def test_search_pharmacies_and_masks_missing_query(client):
    rv = client.get('/search')
    assert rv.status_code == 400
    assert b'query parameter is required' in rv.data

def test_list_pharmacy_masks_invalid_sort_by(client):
    rv = client.get('/pharmacies/Carepoint/masks?sort_by=invalid')
    data = rv.get_json()
    assert rv.status_code == 400
    assert data['error'] == 'sort_by must be "name" or "price"'

def test_list_pharmacy_masks_invalid_order(client):
    rv = client.get('/pharmacies/Carepoint/masks?order=invalid')
    data = rv.get_json()
    assert rv.status_code == 400
    assert data['error'] == 'order must be "asc" or "desc"'

def test_list_pharmacies_by_mask_count_invalid_threshold(client):
    rv = client.get('/pharmacies/mask_count?max_price=100&threshold=invalid')
    data = rv.get_json()
    assert rv.status_code == 400
    assert data['error'] == 'threshold must be "gt" or "lt"'

def test_expand_days_range_and_single_days(client):
    res = client.get("/pharmacies/open?time=09:00&day=Mon")
    assert res.status_code == 200

import logging

def test_expand_days_invalid_format(caplog):
    with caplog.at_level('WARNING'):
        result = expand_days("Mon, InvalidDay-")
    assert isinstance(result, list)
    assert any("expand_days parsing error" in rec.message for rec in caplog.records)

def test_parse_opening_hours_invalid_format(caplog):
    with caplog.at_level('WARNING'):
        result = parse_opening_hours("InvalidFormatWithoutTimes")
    assert isinstance(result, dict)
    assert any("Opening hours block format not matched" in rec.message for rec in caplog.records)

def test_is_open_cross_midnight():
    schedule = {
        "Mon": [{"start": "22:00", "end": "02:00"}]
    }
    assert is_open(schedule, "Mon", "23:00") is True
    assert is_open(schedule, "Mon", "01:00") is True
    assert is_open(schedule, "Mon", "03:00") is False

def test_is_pharmacy_open_error_handling():
    class DummyPharmacy:
        opening_hours = "Invalid/Format"
    result = is_pharmacy_open(DummyPharmacy(), datetime.now().time(), "Mon")
    assert result is False

def test_list_open_pharmacies_invalid_time_format(client):
    rv = client.get('/pharmacies/open?time=25:00')
    assert rv.status_code == 400
    assert b'Invalid time format' in rv.data

def test_search_internal_error(client):
    with patch('app.Session') as mock_session:
        mock_session.side_effect = Exception("DB error")
        rv = client.get('/search?query=test')
        assert rv.status_code == 500
        assert 'error' in rv.get_json()

def test_expand_days_with_empty_and_invalid():
    assert expand_days("") == []
    assert expand_days("XYZ") == ["XYZ"]

def test_parse_opening_hours_with_weird_formats(caplog):
    with caplog.at_level('WARNING'):
        res = parse_opening_hours("Mon-Fri 09:00-18:00 / invalid block")
    assert "Opening hours block format not matched" in caplog.text

def test_is_open_midnight_cross():
    schedule = {"Fri": [{"start": "22:00", "end": "02:00"}]}
    assert is_open(schedule, "Fri", "23:00")
    assert is_open(schedule, "Fri", "01:00")
    assert not is_open(schedule, "Fri", "03:00")

def test_is_pharmacy_open_with_bad_data():
    class BadPharmacy:
        opening_hours = None
    assert not is_pharmacy_open(BadPharmacy(), datetime.now().time(), "Mon")

from unittest.mock import MagicMock
def test_db_query_exception_handling(client):
    with patch('app.Session') as mock_session:
        mock_session.side_effect = Exception("DB error")
        rv = client.get('/pharmacies/open?time=10:00')
        assert rv.status_code == 500
        assert "error" in rv.get_json()
        
def test_expand_days_exception_handling():
    # 傳入格式錯誤字串會觸發except，回傳空陣列
    result = expand_days("invalid-day-string-that-will-cause-error")
    assert result == []

def test_parse_opening_hours_with_invalid_format():
    bad_time_string = "Mon 09:00 to 18:00 / Fri 10:00 18:00"  # 格式不正確
    schedule = parse_opening_hours(bad_time_string)
    assert isinstance(schedule, dict)
    assert all(isinstance(v, list) for v in schedule.values())

def test_is_open_cross_midnight():
    schedule = {
        'Mon': [{'start': '22:00', 'end': '02:00'}]
    }
    assert is_open(schedule, 'Mon', '23:00') is True
    assert is_open(schedule, 'Mon', '01:00') is True
    assert is_open(schedule, 'Mon', '03:00') is False

def test_pharmacies_mask_count_threshold_variants(client):
    res = client.get("/pharmacies/mask_count?min_price=0&max_price=100&count=0&threshold=gt")
    assert res.status_code == 200
    res = client.get("/pharmacies/mask_count?min_price=0&max_price=100&count=100&threshold=lt")
    assert res.status_code == 200

def test_users_top_transaction_errors(client):
    res = client.get("/users/top_by_transaction_amount?start_date=2025-01-01&end_date=2024-12-31")
    assert res.status_code == 400
    res = client.get("/users/top_by_transaction_amount?start_date=2025-01-01&end_date=2025-01-31&x=0")
    assert res.status_code == 400

def test_mask_stats_date_error(client):
    res = client.get("/masks/stats?start_date=bad&end_date=2025-01-01")
    assert res.status_code == 400

def test_expand_days_invalid_format():
    result = expand_days(None)
    assert result == []

def test_parse_opening_hours_invalid_format():
    result = parse_opening_hours("Fri 10-20")
    assert result == {}

def test_is_open_midnight_cross_range():
    schedule = {'Mon': [{'start': '22:00', 'end': '02:00'}]}
    assert is_open(schedule, 'Mon', '23:00') is True
    assert is_open(schedule, 'Mon', '01:00') is True
    assert is_open(schedule, 'Mon', '03:00') is False

def test_pharmacies_mask_count_max_price_missing(client):
    res = client.get("/pharmacies/mask_count?min_price=10")
    assert res.status_code == 400
    assert res.get_json().get("error") == "max_price is required"

def test_pharmacies_mask_count_invalid_range(client):
    res = client.get("/pharmacies/mask_count?min_price=100&max_price=10&count=1&threshold=gt")
    assert res.status_code == 400
    assert res.get_json().get("error") == "max_price must be greater than or equal to min_price"

def test_top_users_invalid_date_format(client):
    res = client.get("/users/top_by_transaction_amount?start_date=abc&end_date=xyz")
    assert res.status_code == 400
    assert res.get_json().get("error") == "start_date and end_date must be in YYYY-MM-DD format"

def test_mask_stats_missing_dates(client):
    res = client.get("/masks/stats")
    assert res.status_code == 400
    assert b"start_date and end_date are required" in res.data

# ---------- 新增 /purchase API 測試 ----------

def test_purchase_success(client):
    payload = {
        "user_id": 1,
        "items": [
            {"pharmacy_id": 1, "mask_id": 1, "quantity": 2}
        ]
    }
    res = client.post("/purchase", data=json.dumps(payload), content_type="application/json")
    assert res.status_code == 200
    data = res.get_json()
    assert "user_id" in data
    assert "total_amount" in data
    assert "remaining_balance" in data
    assert data["user_id"] == 1
    assert data["total_amount"] > 0
    assert data["remaining_balance"] >= 0

def test_purchase_missing_payload(client):
    res = client.post("/purchase", data="", content_type="application/json")
    assert res.status_code == 400
    data = res.get_json()
    assert "error" in data
    assert data["error"] == "Invalid JSON data"

def test_purchase_missing_user_id(client):
    payload = {
        "items": [
            {"pharmacy_id": 1, "mask_id": 1, "quantity": 1}
        ]
    }
    res = client.post("/purchase", data=json.dumps(payload), content_type="application/json")
    assert res.status_code == 400
    data = res.get_json()
    assert "user_id and items are required" in data["error"]

def test_purchase_missing_items(client):
    payload = {
        "user_id": 1
    }
    res = client.post("/purchase", data=json.dumps(payload), content_type="application/json")
    assert res.status_code == 400
    data = res.get_json()
    assert "user_id and items are required" in data["error"]

def test_purchase_invalid_quantity(client):
    payload = {
        "user_id": 1,
        "items": [
            {"pharmacy_id": 1, "mask_id": 1, "quantity": 0}
        ]
    }
    res = client.post("/purchase", data=json.dumps(payload), content_type="application/json")
    assert res.status_code == 400
    data = res.get_json()
    assert "Each item must include pharmacy_id, mask_id, and positive quantity" in data["error"]

def test_purchase_mask_pharmacy_mismatch(client):
    payload = {
        "user_id": 1,
        "items": [
            {"pharmacy_id": 2, "mask_id": 1, "quantity": 1}  # 假設 mask_id=1不屬於 pharmacy_id=2
        ]
    }
    res = client.post("/purchase", data=json.dumps(payload), content_type="application/json")
    assert res.status_code == 400
    data = res.get_json()
    assert "Mask does not belong to the given pharmacy" in data["error"]

def test_purchase_insufficient_balance(client):
    payload = {
        "user_id": 1,
        "items": [
            {"pharmacy_id": 1, "mask_id": 1, "quantity": 1000000}
        ]
    }
    res = client.post("/purchase", data=json.dumps(payload), content_type="application/json")
    assert res.status_code == 400
    data = res.get_json()
    assert "Insufficient balance" in data["error"]

def test_purchase_user_not_found(client):
    payload = {
        "user_id": 999999,
        "items": [
            {"pharmacy_id": 1, "mask_id": 1, "quantity": 1}
        ]
    }
    res = client.post("/purchase", data=json.dumps(payload), content_type="application/json")
    assert res.status_code == 404
    data = res.get_json()
    assert "User with id 999999 not found" in data["error"]

def test_purchase_pharmacy_or_mask_not_found(client):
    payload = {
        "user_id": 1,
        "items": [
            {"pharmacy_id": 999, "mask_id": 999, "quantity": 1}
        ]
    }
    res = client.post("/purchase", data=json.dumps(payload), content_type="application/json")
    assert res.status_code == 404
    data = res.get_json()
    assert "Pharmacy or mask not found" in data["error"]
