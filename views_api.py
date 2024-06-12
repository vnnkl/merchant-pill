from http import HTTPStatus
import json

import httpx
from fastapi import Depends, Query, Request
from lnurl import decode as decode_lnurl
from loguru import logger
from starlette.exceptions import HTTPException

from lnbits.core.crud import get_user
from lnbits.core.models import Payment
from lnbits.core.services import create_invoice
from lnbits.core.views.api import api_payment
from lnbits.decorators import (
    WalletTypeInfo,
    check_admin,
    get_key_type,
    require_admin_key,
    require_invoice_key,
)

from . import merchantpill_ext
from .crud import (
    create_merchantpill,
    update_merchantpill,
    delete_merchantpill,
    get_merchantpill,
    get_merchantpills,
)
from .models import CreateMerchantPillData


#######################################
##### ADD YOUR API ENDPOINTS HERE #####
#######################################

## Get all the records belonging to the user


@merchantpill_ext.get("/api/v1/myex", status_code=HTTPStatus.OK)
async def api_merchantpills(
    req: Request,
    all_wallets: bool = Query(False),
    wallet: WalletTypeInfo = Depends(get_key_type),
):
    wallet_ids = [wallet.wallet.id]
    if all_wallets:
        user = await get_user(wallet.wallet.user)
        wallet_ids = user.wallet_ids if user else []
    return [
        merchantpill.dict() for merchantpill in await get_merchantpills(wallet_ids, req)
    ]


## Get a single record


@merchantpill_ext.get("/api/v1/myex/{merchantpill_id}", status_code=HTTPStatus.OK)
async def api_merchantpill(
    req: Request, merchantpill_id: str, WalletTypeInfo=Depends(get_key_type)
):
    merchantpill = await get_merchantpill(merchantpill_id, req)
    if not merchantpill:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="MerchantPill does not exist."
        )
    return merchantpill.dict()


## update a record


@merchantpill_ext.put("/api/v1/myex/{merchantpill_id}")
async def api_merchantpill_update(
    req: Request,
    data: CreateMerchantPillData,
    merchantpill_id: str,
    wallet: WalletTypeInfo = Depends(get_key_type),
):
    if not merchantpill_id:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="MerchantPill does not exist."
        )
    merchantpill = await get_merchantpill(merchantpill_id, req)
    assert merchantpill, "MerchantPill couldn't be retrieved"

    if wallet.wallet.id != merchantpill.wallet:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail="Not your MerchantPill."
        )
    merchantpill = await update_merchantpill(
        merchantpill_id=merchantpill_id, **data.dict(), req=req
    )
    return merchantpill.dict()


## Create a new record


@merchantpill_ext.post("/api/v1/myex", status_code=HTTPStatus.CREATED)
async def api_merchantpill_create(
    req: Request,
    data: CreateMerchantPillData,
    wallet: WalletTypeInfo = Depends(require_admin_key),
):
    merchantpill = await create_merchantpill(
        wallet_id=wallet.wallet.id, data=data, req=req
    )
    return merchantpill.dict()


## Delete a record


@merchantpill_ext.delete("/api/v1/myex/{merchantpill_id}")
async def api_merchantpill_delete(
    merchantpill_id: str, wallet: WalletTypeInfo = Depends(require_admin_key)
):
    merchantpill = await get_merchantpill(merchantpill_id)

    if not merchantpill:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="MerchantPill does not exist."
        )

    if merchantpill.wallet != wallet.wallet.id:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail="Not your MerchantPill."
        )

    await delete_merchantpill(merchantpill_id)
    return "", HTTPStatus.NO_CONTENT


# ANY OTHER ENDPOINTS YOU NEED

## This endpoint creates a payment


@merchantpill_ext.post(
    "/api/v1/myex/payment/{merchantpill_id}", status_code=HTTPStatus.CREATED
)
async def api_tpos_create_invoice(
    merchantpill_id: str, amount: int = Query(..., ge=1), memo: str = ""
) -> dict:
    merchantpill = await get_merchantpill(merchantpill_id)

    if not merchantpill:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="MerchantPill does not exist."
        )

    # we create a payment and add some tags, so tasks.py can grab the payment once its paid

    try:
        payment_hash, payment_request = await create_invoice(
            wallet_id=merchantpill.wallet,
            amount=amount,
            memo=f"{memo} to {merchantpill.name}" if memo else f"{merchantpill.name}",
            extra={
                "tag": "merchantpill",
                "amount": amount,
            },
        )
    except Exception as e:
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(e))

    return {"payment_hash": payment_hash, "payment_request": payment_request}
