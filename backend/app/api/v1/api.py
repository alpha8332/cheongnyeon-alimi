from fastapi import APIRouter
from app.api.v1.endpoints import admin_access, collection_run_admin, health, policies, policy_search, recommendation

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health Check"])
api_router.include_router(admin_access.router, prefix="/admin", tags=["Admin Access"])
api_router.include_router(collection_run_admin.router, prefix="/admin/collection-runs", tags=["Admin Collection Runs"])
api_router.include_router(recommendation.router, tags=["Recommendations"])
api_router.include_router(policy_search.router, prefix="/policies", tags=["Policies"])
api_router.include_router(policies.router, prefix="/policies", tags=["Policies"])
