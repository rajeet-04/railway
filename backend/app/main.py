from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, seat_holds, bookings, admin, stations, trains, train_runs

app = FastAPI(title="Railway Booking Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(stations.router, prefix="/api/stations", tags=["stations"])
app.include_router(trains.router, prefix="/api/trains", tags=["trains"])
app.include_router(train_runs.router, prefix="/api/train_runs", tags=["train_runs"])
app.include_router(seat_holds.router, prefix="/api/seat_holds", tags=["seat_holds"])
app.include_router(bookings.router, prefix="/api/bookings", tags=["bookings"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])

@app.get("/")
def read_root():
    return {"status": "ok", "service": "railway-backend"}
