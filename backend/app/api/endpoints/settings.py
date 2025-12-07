import logging
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api import deps
from app.services.tenant import TenantService

router = APIRouter()
logger = logging.getLogger(__name__)


class TenantSettingsUpdate(BaseModel):
    openai_key: str | None = None
    llama_cloud_key: str | None = None


class TenantSettingsResponse(BaseModel):
    tenant_id: str
    openai_key_configured: bool
    llama_cloud_key_configured: bool


@router.get("/tenant/settings", response_model=TenantSettingsResponse)
async def get_tenant_settings(
    current_user=Depends(deps.get_current_user),
    tenant_service: TenantService = Depends(deps.get_tenant_service),
):
    """Retrieve tenant API key configuration status (not the actual keys)."""
    logger.debug(
        f"Fetching tenant settings for tenant_id: {current_user.tenant_id}")
    tenant = await tenant_service.get_tenant(current_user.tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

    return {
        "tenant_id": str(tenant.id),
        "openai_key_configured": bool(tenant.encrypted_openai_key),
        "llama_cloud_key_configured": bool(tenant.encrypted_llama_cloud_key),
    }


@router.patch("/tenant/settings", response_model=TenantSettingsResponse)
async def update_tenant_settings(
    data: TenantSettingsUpdate,
    current_user=Depends(deps.get_current_user),
    tenant_service: TenantService = Depends(deps.get_tenant_service),
):
    """Update tenant API keys (encrypted on store)."""
    logger.info(
        f"Updating tenant settings for tenant_id: {current_user.tenant_id}")
    try:
        updated = await tenant_service.update_tenant_settings(
            current_user.tenant_id,
            openai_key=data.openai_key,
            llama_cloud_key=data.llama_cloud_key,
        )
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

        return {
            "tenant_id": str(updated.id),
            "openai_key_configured": bool(updated.encrypted_openai_key),
            "llama_cloud_key_configured": bool(updated.encrypted_llama_cloud_key),
        }
    except Exception as e:
        logger.error(
            f"Error updating tenant settings: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update settings")
