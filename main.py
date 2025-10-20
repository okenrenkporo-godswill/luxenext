from fastapi import FastAPI,APIRouter,Request, status,HTTPException
from router import ( router_coupon,router_wishlist,router_payment,router_adress,router_cart,
                    router_category,router_order,router_product,router_review,router_user,route__auth,router_password)
from database import engine, Base
from dotenv import load_dotenv

from fastapi.middleware.cors import CORSMiddleware





app = FastAPI()
# Load environment variables
load_dotenv()


Base.metadata.create_all(bind=engine)



# ✅ Correct way to include router
# 1️⃣ Authentication & Users (entry point)
app.include_router(route__auth.router)
app.include_router(router_user.router)

# 2️⃣ Catalog (what users can browse)
app.include_router(router_category.router)
app.include_router(router_product.router)

# 3️⃣ Shopping features
app.include_router(router_cart.router)
app.include_router(router_wishlist.router)
app.include_router(router_coupon.router)

# 4️⃣ Orders & Payments
app.include_router(router_order.router)
app.include_router(router_payment.router)

# 5️⃣ User extras
app.include_router(router_adress.router)   # Shipping addresses
app.include_router(router_review.router)   # Product reviews
app.include_router(router_password.router) # Payments

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",             # local frontend
        "https://luxenext-f.vercel.app",     # deployed frontend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)