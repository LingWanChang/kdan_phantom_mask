import pytest
from app import app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Pharmacy, Mask, User, PurchaseHistory
from datetime import datetime, date
import os

# 設置測試資料庫
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql+psycopg2://postgres:Kris11063@db/pharmacy_db')
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture(scope="module")
def setup_database():
    Base.metadata.create_all(engine)
    session = Session()
    try:
        # 插入測試數據
        pharmacy = Pharmacy(name="Carepoint", cash_balance=593.35, opening_hours="Mon - Fri 08:00 - 17:00")
        session.add(pharmacy)
        session.flush()
        mask = Mask(name="CareMask Pro", price=2.00, pharmacy_id=pharmacy.id)
        session.add(mask)
        user = User(name="John Doe", cash_balance=100.00)
        session.add(user)
        session.flush()
        purchase = PurchaseHistory(
            user_id=user.id,
            mask_id=mask.id,
            pharmacy_id=pharmacy.id,
            transaction_amount=2.00,
            transaction_date=date(2023, 1, 1)
        )
        session.add(purchase)
        session.commit()
    finally:
        session.close()
    yield
    # 清理測試數據
    session = Session()
    session.query(PurchaseHistory).delete()
    session.query(Mask).delete()
    session.query(Pharmacy).delete()
    session.query(User).delete()
    session.commit()
    session.close()

def test_pharmacies_open(client, setup_database):
    # 測試當前時間（假設 2025-07-13 21:27 為週日，Carepoint 關閉）
    response = client.get('/pharmacies/open')
    assert response.status_code == 200
    assert isinstance(response.json, list)
    
    # 測試指定時間（週一 10:00，Carepoint 應開放）
    response = client.get('/pharmacies/open?datetime=2023-01-02 10:00')
    assert response.status_code == 200
    assert any(p['name'] == 'Carepoint' for p in response.json)
    
    # 測試無效 datetime
    response = client.get('/pharmacies/open?datetime=invalid')
    assert response.status_code == 400
    assert 'error' in response.json

def test_pharmacy_masks(client, setup_database):
    # 測試現有藥局
    response = client.get('/pharmacies/Carepoint/masks')
    assert response.status_code == 200
    assert any(m['name'] == 'CareMask Pro' for m in response.json)
    
    # 測試不存在的藥局
    response = client.get('/pharmacies/NonExistent/masks')
    assert response.status_code == 404
    assert 'error' in response.json

def test_pharmacies_mask_count(client, setup_database):
    # 測試正常情況
    response = client.get('/pharmacies/mask_count?min_price=1.0&max_price=5.0&count=0&threshold=gt')
    assert response.status_code == 200
    assert any(p['name'] == 'Carepoint' for p in response.json)
    
    # 測試無效 max_price
    response = client.get('/pharmacies/mask_count?min_price=5.0')
    assert response.status_code == 400
    assert 'error' in response.json
    
    # 測試無匹配結果
    response = client.get('/pharmacies/mask_count?min_price=10.0&max_price=20.0&count=5&threshold=gt')
    assert response.status_code == 200
    assert len(response.json) == 0

def test_top_users_by_transaction_amount(client, setup_database):
    # 測試正常情況
    response = client.get('/users/top_by_transaction_amount?start_date=2023-01-01&end_date=2023-12-31&x=5')
    assert response.status_code == 200
    assert any(u['name'] == 'John Doe' for u in response.json)
    
    # 測試無效日期
    response = client.get('/users/top_by_transaction_amount?start_date=invalid&end_date=2023-12-31')
    assert response.status_code == 400
    assert 'error' in response.json
    
    # 測試無交易記錄
    response = client.get('/users/top_by_transaction_amount?start_date=2024-01-01&end_date=2024-12-31')
    assert response.status_code == 200
    assert len(response.json) == 0

def test_mask_stats(client, setup_database):
    # 測試正常情況
    response = client.get('/masks/stats?start_date=2023-01-01&end_date=2023-12-31')
    assert response.status_code == 200
    assert response.json['total_mask_count'] == 1
    assert response.json['total_transaction_amount'] == 2.00
    
    # 測試無效日期
    response = client.get('/masks/stats?start_date=invalid&end_date=2023-12-31')
    assert response.status_code == 400
    assert 'error' in response.json
    
    # 測試無交易記錄
    response = client.get('/masks/stats?start_date=2024-01-01&end_date=2024-12-31')
    assert response.status_code == 200
    assert response.json['total_mask_count'] == 0

def test_search(client, setup_database):
    # 測試正常搜尋
    response = client.get('/search?query=Care')
    assert response.status_code == 200
    assert any(p['name'] == 'Carepoint' for p in response.json['pharmacies'])
    assert any(m['name'] == 'CareMask Pro' for m in response.json['masks'])
    
    # 測試無 query
    response = client.get('/search')
    assert response.status_code == 400
    assert 'error' in response.json
    
    # 測試無匹配結果
    response = client.get('/search?query=NonExistent')
    assert response.status_code == 200
    assert len(response.json['pharmacies']) == 0
    assert len(response.json['masks']) == 0

if __name__ == '__main__':
    pytest.main(['-v', '--cov=app', '--cov-report=html'])