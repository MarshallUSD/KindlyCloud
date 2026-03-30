"""Main FastAPI application."""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from app.api.routes import admin_routes, attendance, auth, children, groups, kindergarten_routes, parent_routes, staff, teachers
from app.core.exceptions import ApplicationException

# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.VERSION,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)


# Exception handlers
@app.exception_handler(ApplicationException)
async def application_exception_handler(request: Request, exc: ApplicationException):
    """Handle custom application exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.message,
            "error_code": exc.error_code,
            "details": exc.details
        },
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Include routers
app.include_router(auth.router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["auth"])
app.include_router(admin_routes.router, prefix=f"{settings.API_V1_PREFIX}/admin", tags=["admin"])
app.include_router(groups.router, prefix=f"{settings.API_V1_PREFIX}/groups", tags=["groups"])
app.include_router(children.router, prefix=f"{settings.API_V1_PREFIX}/children", tags=["children"])
app.include_router(attendance.router, prefix=f"{settings.API_V1_PREFIX}/attendance", tags=["attendance"])
app.include_router(staff.router, prefix=f"{settings.API_V1_PREFIX}/staff", tags=["staff"])
app.include_router(teachers.router, prefix=f"{settings.API_V1_PREFIX}/teachers", tags=["teachers"])
app.include_router(kindergarten_routes.router, prefix=f"{settings.API_V1_PREFIX}/kindergartens", tags=["kindergarten"])
app.include_router(parent_routes.router, prefix=f"{settings.API_V1_PREFIX}/parent", tags=["parent"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to KindlyCloud API",
        "version": settings.VERSION,
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
