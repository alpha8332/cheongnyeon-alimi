from fastapi import APIRouter
from app.api.v1.endpoints import admin_access, health, policies, policy_search

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health Check"])
api_router.include_router(admin_access.router, prefix="/admin", tags=["Admin Access"])
api_router.include_router(policy_search.router, prefix="/policies", tags=["Policies"])
api_router.include_router(policies.router, prefix="/policies", tags=["Policies"])
