-- ===============================================
-- Add Paystack Payment Option to Database
-- ===============================================
-- Run this SQL in your PostgreSQL database
-- You can use pgAdmin, psql, or any database client

INSERT INTO payment_options (name, provider, account_name, account_number, is_active)
VALUES ('Paystack', 'paystack', NULL, NULL, true)
ON CONFLICT DO NOTHING;

-- Verify the insertion
SELECT * FROM payment_options WHERE provider = 'paystack';
