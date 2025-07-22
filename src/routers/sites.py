import uuid

from src.db.database import RepositoryContainer, get_db
from src.dependencies import UserClaims, decode_jwt_token
from src.routers.router_model import SiteResponse

from fastapi import status, HTTPException, Depends, Query, APIRouter


sites_router = APIRouter()


@sites_router.get("/sites/{site_id}",
                  response_model=SiteResponse)
async def get_site(
    site_id: uuid.UUID,
    user: UserClaims = Depends(decode_jwt_token),
    db: RepositoryContainer = Depends(get_db)
):
    # return { "id" :uuid.uuid4(), "name" :"ddd"}
    # more detailed data about requested site
    site = await db.sites.get_user_site(site_id=site_id)
    if not site:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"site with id: {site_id} was not found")
    return site


@sites_router.get(
    "/sites",
    response_model=list[SiteResponse],
    description="Return list of all site for given user",
    responses={
           "200": {"description":"List of all sites", "model": list[SiteResponse] },
           "401": {"description": "Invalid of missing JSON" },
        }
    )
async def get_sites(
    user: UserClaims = Depends(decode_jwt_token),
    db: RepositoryContainer = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of sites to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of sites to return")
):
    # get all sites attached to user
    sites = await db.sites.get_all_user_sites(user_id=uuid.UUID(user.id), offset=skip, limit=limit)
    if not sites:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No sites was found")

    return sites

