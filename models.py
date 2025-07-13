from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class Pharmacy(Base):
    __tablename__ = 'pharmacies'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    cash_balance = Column(Float)
    opening_hours = Column(String)
    masks = relationship("Mask", back_populates="pharmacy")

class Mask(Base):
    __tablename__ = 'masks'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    price = Column(Float)
    pharmacy_id = Column(Integer, ForeignKey('pharmacies.id'))
    pharmacy = relationship("Pharmacy", back_populates="masks")
    
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
    transaction_date = Column(String)