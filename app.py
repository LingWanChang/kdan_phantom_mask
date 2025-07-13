from flask import Flask, request, jsonify
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from datetime import datetime, time
from models import Pharmacy, Base, Mask, User, PurchaseHistory
import os
import re

app = Flask(__name__)
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql+psycopg2://postgres:Kris11063@localhost/pharmacy_db')
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

weekday_map = {
    "Mon": "Monday",
    "Tue": "Tuesday",
    "Wed": "Wednesday",
    "Thu": "Thursday",
    "Thur": "Thursday",
    "Fri": "Friday",
    "Sat": "Saturday",
    "Sun": "Sunday",
}
reverse_weekday_map = {v: k for k, v in weekday_map.items()}

def expand_days(day_str):
    parts = [s.strip() for s in day_str.split(",")]
    result = []
    keys = list(weekday_map.keys())
    for part in parts:
        if "-" in part:
            start, end = [d.strip() for d in part.split("-")]
            start_idx = keys.index(start)
            end_idx = keys.index(end) + 1
            result.extend(keys[start_idx:end_idx])
        else:
            result.append(part)
    return result

def parse_opening_hours(time_string):
    blocks = [b.strip() for b in time_string.split("/")]
    schedule = {}
    for block in blocks:
        match = re.match(r"(.+?)\s+(\d{2}:\d{2})\s*-\s*(\d{2}:\d{2})", block)
        if match:
            days_part, start_time, end_time = match.groups()
            days = expand_days(days_part)
            for day in days:
                schedule.setdefault(day, []).append({"start": start_time, "end": end_time})
    return schedule

def is_open(schedule, day_code, check_time_str):
    check_time = datetime.strptime(check_time_str, "%H:%M").time()
    periods = schedule.get(day_code, [])
    for period in periods:
        start = datetime.strptime(period["start"], "%H:%M").time()
        end = datetime.strptime(period["end"], "%H:%M").time()
        if start <= end:
            if start <= check_time <= end:
                return True
        else:
            if check_time >= start or check_time <= end:
                return True
    return False

def is_pharmacy_open(pharmacy, check_time, day):
    try:
        if not day:
            return True
        day_code = day.lower()[:3].capitalize()
        schedule = parse_opening_hours(pharmacy.opening_hours)
        return is_open(schedule, day_code, check_time.strftime("%H:%M"))
    except Exception as e:
        print(f"Error in is_pharmacy_open: {e}")
        return False

@app.route('/pharmacies/open', methods=['GET'])
def list_open_pharmacies():
    try:
        session = Session()
        time_str = request.args.get('time', '00:00')
        day = request.args.get('day', None)
        check_time = datetime.strptime(time_str, '%H:%M').time()
        pharmacies = session.query(Pharmacy).all()
        open_pharmacies = [p for p in pharmacies if is_pharmacy_open(p, check_time, day)]
        result = [{'id': p.id, 'name': p.name, 'cash_balance': float(p.cash_balance), 'opening_hours': p.opening_hours} for p in open_pharmacies]
        session.close()
        return jsonify(result)
    except Exception as e:
        session.close()
        print(f"Error in list_open_pharmacies: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/pharmacies/<pharmacy_name>/masks', methods=['GET'])
def list_pharmacy_masks(pharmacy_name):
    try:
        session = Session()
        # 查詢藥局
        pharmacy = session.query(Pharmacy).filter(Pharmacy.name == pharmacy_name).first()
        if not pharmacy:
            session.close()
            return jsonify({'error': f'Pharmacy with name {pharmacy_name} not found'}), 404

        # 獲取查詢參數
        sort_by = request.args.get('sort_by', 'name')  # 預設按名稱排序
        order = request.args.get('order', 'asc')

        # 驗證參數
        if sort_by not in ['name', 'price']:
            session.close()
            return jsonify({'error': 'sort_by must be "name" or "price"'}), 400
        if order not in ['asc', 'desc']:
            session.close()
            return jsonify({'error': 'order must be "asc" or "desc"'}), 400

        # 查詢口罩
        query = session.query(Mask).filter(Mask.pharmacy_id == pharmacy.id)
        
        # 排序
        if sort_by == 'name':
            query = query.order_by(Mask.name.asc() if order == 'asc' else Mask.name.desc())
        else:  # sort_by == 'price'
            query = query.order_by(Mask.price.asc() if order == 'asc' else Mask.price.desc())

        masks = query.all()
        result = [{'id': m.id, 'name': m.name, 'price': float(m.price)} for m in masks]
        session.close()
        return jsonify(result)
    except Exception as e:
        session.close()
        print(f"Error in list_pharmacy_masks: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/pharmacies/mask_count', methods=['GET'])
def list_pharmacies_by_mask_count():
    try:
        session = Session()
        # 獲取查詢參數
        min_price = float(request.args.get('min_price', 0.0))
        max_price = request.args.get('max_price')
        count = int(request.args.get('count', 0))
        threshold = request.args.get('threshold', 'gt')

        # 驗證參數
        if max_price is None:
            session.close()
            return jsonify({'error': 'max_price is required'}), 400
        try:
            max_price = float(max_price)
            if max_price < min_price:
                session.close()
                return jsonify({'error': 'max_price must be greater than or equal to min_price'}), 400
        except (ValueError, TypeError):
            session.close()
            return jsonify({'error': 'min_price and max_price must be valid numbers'}), 400
        if count < 0:
            session.close()
            return jsonify({'error': 'count must be non-negative'}), 400
        if threshold not in ['gt', 'lt']:
            session.close()
            return jsonify({'error': 'threshold must be "gt" or "lt"'}), 400

        # 查詢每個藥局在價格範圍內的口罩數量
        mask_counts = (
            session.query(
                Pharmacy.id,
                Pharmacy.name,
                Pharmacy.cash_balance,
                func.count(Mask.id).label('mask_count')
            )
            .outerjoin(Mask, Pharmacy.id == Mask.pharmacy_id)
            .filter(Mask.price.between(min_price, max_price))
            .group_by(Pharmacy.id, Pharmacy.name, Pharmacy.cash_balance)
            .having(
                func.count(Mask.id) > count if threshold == 'gt' else func.count(Mask.id) < count
            )
            .all()
        )
        
        # 格式化結果
        result = [
            {
                'id': row[0],
                'name': row[1],
                'cash_balance': float(row[2]),
                'mask_count': row[3]
            }
            for row in mask_counts
        ]

        session.close()
        return jsonify(result)
    except Exception as e:
        session.close()
        print(f"Error in list_pharmacies_by_mask_count: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/users/top_by_transaction_amount', methods=['GET'])
def list_top_users_by_transaction():
    try:
        session = Session()
        # 獲取查詢參數
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        x = int(request.args.get('x', 10))

        # 驗證參數
        if not start_date or not end_date:
            session.close()
            return jsonify({'error': 'start_date and end_date are required'}), 400
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S').date()
            if end_date < start_date:
                session.close()
                return jsonify({'error': 'end_date must be greater than or equal to start_date'}), 400
        except ValueError:
            session.close()
            return jsonify({'error': 'start_date and end_date must be in YYYY-MM-DD format'}), 400
        if x <= 0:
            session.close()
            return jsonify({'error': 'x must be a positive integer'}), 400

        # 查詢每個使用者的總交易金額
        top_users = (
            session.query(
                User.id,
                User.name,
                func.sum(PurchaseHistory.transaction_amount).label('total_transaction_amount')
            )
            .join(PurchaseHistory, User.id == PurchaseHistory.user_id)
            .filter(PurchaseHistory.transaction_date.between(start_date, end_date))
            .group_by(User.id, User.name)
            .order_by(func.sum(PurchaseHistory.transaction_amount).desc())
            .limit(x)
            .all()
        )

        # 格式化結果
        result = [
            {
                'id': user.id,
                'name': user.name,
                'total_transaction_amount': float(user.total_transaction_amount or 0)
            }
            for user in top_users
        ]

        session.close()
        return jsonify(result)
    except Exception as e:
        session.close()
        print(f"Error in list_top_users_by_transaction: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/masks/stats', methods=['GET'])
def get_mask_stats():
    try:
        session = Session()
        # 獲取查詢參數
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # 驗證參數
        if not start_date or not end_date:
            session.close()
            return jsonify({'error': 'start_date and end_date are required'}), 400
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            if end_date < start_date:
                session.close()
                return jsonify({'error': 'end_date must be greater than or equal to start_date'}), 400
        except ValueError:
            session.close()
            return jsonify({'error': 'start_date and end_date must be in YYYY-MM-DD format'}), 400

        # 查詢口罩總數和交易總金額
        stats = (
            session.query(
                func.count(PurchaseHistory.id).label('total_mask_count'),
                func.sum(PurchaseHistory.transaction_amount).label('total_transaction_amount')
            )
            .filter(PurchaseHistory.transaction_date.between(start_date, end_date))
            .first()
        )

        # 格式化結果
        result = {
            'total_mask_count': int(stats.total_mask_count or 0),
            'total_transaction_amount': float(stats.total_transaction_amount or 0)
        }

        session.close()
        return jsonify(result)
    except Exception as e:
        session.close()
        print(f"Error in get_mask_stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/search', methods=['GET'])
def search_pharmacies_and_masks():
    try:
        session = Session()
        # 獲取查詢參數並清理
        query = request.args.get('query', '').strip()
        
        # 驗證參數
        if not query:
            session.close()
            return jsonify({'error': 'query parameter is required'}), 400
        
        # 模糊搜尋藥局
        search_pattern = f'%{query}%'
        pharmacies = (
            session.query(Pharmacy)
            .filter(Pharmacy.name.ilike(search_pattern))
            .order_by(Pharmacy.name.asc())
            .all()
        )
        
        # 模糊搜尋口罩，並關聯藥局名稱
        masks = (
            session.query(Mask, Pharmacy.name.label('pharmacy_name'))
            .join(Pharmacy, Mask.pharmacy_id == Pharmacy.id)
            .filter(Mask.name.ilike(search_pattern))
            .order_by(Mask.name.asc())
            .all()
        )
        
        # 格式化結果
        result = {
            'pharmacies': [
                {
                    'id': p.id,
                    'name': p.name,
                    'cash_balance': float(p.cash_balance),
                    'opening_hours': p.opening_hours
                }
                for p in pharmacies
            ],
            'masks': [
                {
                    'id': m.id,
                    'name': m.name,
                    'price': float(m.price),
                    'pharmacy_name': pharmacy_name
                }
                for m, pharmacy_name in masks
            ]
        }
        
        session.close()
        return jsonify(result)
    except Exception as e:
        session.close()
        print(f"Error in search_pharmacies_and_masks: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
