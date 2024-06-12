from http import HTTPStatus

from fastapi import Depends, Request
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException
from starlette.responses import HTMLResponse

from lnbits.core.models import User
from lnbits.decorators import check_user_exists
from lnbits.settings import settings

from . import merchantpill_ext, merchantpill_renderer
from .crud import get_merchantpill

myex = Jinja2Templates(directory="myex")


#######################################
##### ADD YOUR PAGE ENDPOINTS HERE ####
#######################################


# Backend admin page


@merchantpill_ext.get("/", response_class=HTMLResponse)
async def index(request: Request, user: User = Depends(check_user_exists)):
    return merchantpill_renderer().TemplateResponse(
        "merchantpill/index.html", {"request": request, "user": user.dict()}
    )


# Frontend shareable page


@merchantpill_ext.get("/{merchantpill_id}")
async def merchantpill(request: Request, merchantpill_id):
    merchantpill = await get_merchantpill(merchantpill_id, request)
    if not merchantpill:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="MyExtension does not exist."
        )
    return merchantpill_renderer().TemplateResponse(
        "merchantpill/merchantpill.html",
        {
            "request": request,
            "merchantpill_id": merchantpill_id,
            "lnurlpay": merchantpill.lnurlpay,
            "web_manifest": f"/merchantpill/manifest/{merchantpill_id}.webmanifest",
        },
    )


# Manifest for public page, customise or remove manifest completely


@merchantpill_ext.get("/manifest/{merchantpill_id}.webmanifest")
async def manifest(merchantpill_id: str):
    merchantpill = await get_merchantpill(merchantpill_id)
    if not merchantpill:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="MyExtension does not exist."
        )

    return {
        "short_name": settings.lnbits_site_title,
        "name": merchantpill.name + " - " + settings.lnbits_site_title,
        "icons": [
            {
                "src": settings.lnbits_custom_logo
                if settings.lnbits_custom_logo
                else "https://cdn.jsdelivr.net/gh/lnbits/lnbits@0.3.0/docs/logos/lnbits.png",
                "type": "image/png",
                "sizes": "900x900",
            }
        ],
        "start_url": "/merchantpill/" + merchantpill_id,
        "background_color": "#1F2234",
        "description": "Minimal extension to build on",
        "display": "standalone",
        "scope": "/merchantpill/" + merchantpill_id,
        "theme_color": "#1F2234",
        "shortcuts": [
            {
                "name": merchantpill.name + " - " + settings.lnbits_site_title,
                "short_name": merchantpill.name,
                "description": merchantpill.name + " - " + settings.lnbits_site_title,
                "url": "/merchantpill/" + merchantpill_id,
            }
        ],
    }
