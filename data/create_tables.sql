\connect pharmacy_db

CREATE TABLE pharmacies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    opening_hours JSONB NOT NULL,
    cash_balance DECIMAL(10,2) NOT NULL
);

CREATE TABLE masks (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    pharmacy_id INTEGER REFERENCES pharmacies(id)
);

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    cash_balance DECIMAL(10,2) NOT NULL
);

CREATE TABLE purchase_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    mask_id INTEGER REFERENCES masks(id),
    pharmacy_id INTEGER REFERENCES pharmacies(id),
    transaction_amount DECIMAL(10,2) NOT NULL,
    purchase_date TIMESTAMP NOT NULL
);


