from fastapi import APIRouter
from app.api.v1.endpoints import admin_access, admin_collector, admin_log, admin_policy, collection_run_admin, health, policies, policy_search, recommendation

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health Check"])
api_router.include_router(admin_access.router, prefix="/admin", tags=["Admin Access"])
api_router.include_router(collection_run_admin.router, prefix="/admin/collection-runs", tags=["Admin Collection Runs"])
api_router.include_router(admin_collector.router, prefix="/admin/collectors", tags=["Admin Collectors"])
api_router.include_router(admin_policy.router, prefix="/admin/policies", tags=["Admin Policies"])
api_router.include_router(admin_log.router, prefix="/admin/logs", tags=["Admin Logs"])
api_router.include_router(recommendation.router, tags=["Recommendations"])
api_router.include_router(policy_search.router, prefix="/policies", tags=["Policies"])
api_router.include_router(policies.router, prefix="/policies", tags=["Policies"])
