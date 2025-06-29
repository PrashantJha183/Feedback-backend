from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.mongo import init_db
from app.routers import user, feedback, notification

app = FastAPI(title="Feedback Tool")

# Adding middleware for CORS policy 
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:5173",
        "https://localhost:5173",
        "http://127.0.0.1:5173",
        "https://127.0.0.1:5173",
        "http://localhost:3000",
        "https://127.0.0.1:3000",
        "https://feedback-2uwd.onrender.com",
        "http://feedback-2uwd.onrender.com",
        "https://feedback-frontend-git-main-prashantjha183s-projects.vercel.app",
        "https://feedback-frontend-three.vercel.app",
        "https://voxpop.netlify.app",
        "http://voxpop.netlify.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Root route
@app.get("/")
def root():
    return{"message":"Welcome to Feedback API"}

#Intialize MongoDB Atlas connection on startup
@app.on_event("startup")
async def startup_event():
    await init_db()
print ("Connected to MongoDB and intialized Beanie models.")
app.include_router(user.router, prefix="/users", tags=["Users"])
app.include_router(feedback.router, prefix="/feedback", tags=["Feedback"])
app.include_router(notification.router, prefix="/notifications", tags=["Notifications"])
