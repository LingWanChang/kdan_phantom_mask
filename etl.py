import json
import os
from sqlalchemy import create_engine, Column, Integer, String, Float, JSON, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

# 定義模型（與上面 SQL 表格對應）
class Pharmacy(Base):
    __tablename__ = 'pharmacies'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    cash_balance = Column(Float)
    opening_hours = Column(JSON)

class Mask(Base):
    __tablename__ = 'masks'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    price = Column(Float)
    pharmacy_id = Column(Integer, ForeignKey('pharmacies.id'))

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    cash_balance = Column(Float)

class PurchaseHistory(Base):
    __tablename__ = 'purchase_history'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    mask_id = Column(Integer, ForeignKey('masks.id'))
    pharmacy_id = Column(Integer, ForeignKey('pharmacies.id'))
    transaction_amount = Column(Float)
    transaction_date = Column(DateTime)

# 連接到資料庫
#engine = create_engine('postgresql+psycopg2://postgres:Kris11063@localhost/pharmacy_db')
from sqlalchemy import create_engine
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql+psycopg2://postgres:Kris11063@localhost/pharmacy_db')
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# 讀取 JSON 檔案
def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# ETL 處理
def etl_pharmacies():
    pharmacies_data = load_json('data/pharmacies.json')
    for pharmacy in pharmacies_data:
        new_pharmacy = Pharmacy(
            name=pharmacy['name'],
            cash_balance=pharmacy['cashBalance'],
            opening_hours=pharmacy['openingHours']
        )
        session.add(new_pharmacy)
        session.flush()  # 獲取 pharmacy.id
        for mask in pharmacy.get('masks', []):
            new_mask = Mask(
                name=mask['name'],
                price=mask['price'],
                pharmacy_id=new_pharmacy.id
            )
            session.add(new_mask)

def etl_users():
    users_data = load_json('data/users.json')
    for user in users_data:
        new_user = User(
            name=user['name'],
            cash_balance=user['cashBalance']
        )
        session.add(new_user)
        session.flush()  # 獲取 user.id
        for purchase in user.get('purchaseHistories', []):
            mask = session.query(Mask).filter_by(name=purchase['maskName']).first()
            if mask:
                new_purchase = PurchaseHistory(
                    user_id=new_user.id,
                    mask_id=mask.id,
                    pharmacy_id=mask.pharmacy_id,
                    transaction_amount=purchase['transactionAmount'],
                    transaction_date=datetime.strptime(purchase['transactionDate'], '%Y-%m-%d %H:%M:%S')
                )
                session.add(new_purchase)

# 執行 ETL
if __name__ == '__main__':
    etl_pharmacies()
    etl_users()
    session.commit()
    print("ETL completed successfully!")