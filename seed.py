from database import SessionLocal
from models import PaymentOption

db = SessionLocal()

banks = [
    PaymentOption(
        name="Opay",
        provider="manual",
        account_name="okenrenkporooritsewinor",
        account_number="8112874709"
    ),
    PaymentOption(
        name="UBA Bank",
        provider="manual",
        account_name="Okenrenkporooritsewinor",
        account_number="2146421990"
    ),
    PaymentOption(
        name="GTBank",
        provider="manual",
        account_name="okenrenkporooritsewinor",
        account_number="0890493592"
    ),
]

db.add_all(banks)
db.commit()
db.close()  
print("payment seed")
