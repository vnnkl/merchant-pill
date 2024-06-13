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
    create_user,
    update_user,
    delete_user,
    get_user,
    get_users,
    create_debt,
    update_debt,
    delete_debt,
    get_debt,
    get_debts,
    create_transaction,
    update_transaction,
    delete_transaction,
    get_transaction,
    get_transactions,
)
from .models import CreateUser, CreateDebt, CreateTransaction


#######################################
##### ADD YOUR API ENDPOINTS HERE #####
#######################################

## Get all the records belonging to the user


@merchantpill_ext.get("/api/v1/user", status_code=HTTPStatus.OK)
async def api_users(
    req: Request,
    all_wallets: bool = Query(False),
    wallet: WalletTypeInfo = Depends(get_key_type),
):
    wallet_ids = [wallet.wallet.id]
    if all_wallets:
        user = await get_user(wallet.wallet.user)
        wallet_ids = user.wallet_ids if user else []
    return [
        user.dict() for user in await get_users(wallet_ids, req)
    ]


## Get a single record


@merchantpill_ext.get("/api/v1/user/{user_id}", status_code=HTTPStatus.OK)
async def api_user(
    req: Request, user_id: str, WalletTypeInfo=Depends(get_key_type)
):
    user = await get_user(user_id, req)
    if not user:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="User does not exist."
        )
    return user.dict()


## update a record


@merchantpill_ext.put("/api/v1/user/{user_id}")
async def api_user_update(
    req: Request,
    data: CreateUser,
    user_id: str,
    wallet: WalletTypeInfo = Depends(get_key_type),
):
    if not user_id:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="User does not exist."
        )
    user = await get_user(user_id, req)
    assert user, "User couldn't be retrieved"

    if wallet.wallet.id != user.wallet:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail="Not your User."
        )
    user = await update_user(
        user_id=user_id, **data.dict(), req=req
    )
    return user.dict()


## Create a new record


@merchantpill_ext.post("/api/v1/user", status_code=HTTPStatus.CREATED)
async def api_user_create(
    req: Request,
    data: CreateUser,
    wallet: WalletTypeInfo = Depends(require_admin_key),
):
    user = await create_user(
        wallet_id=wallet.wallet.id, data=data, req=req
    )
    return user.dict()


## Delete a record


@merchantpill_ext.delete("/api/v1/user/{user_id}")
async def api_user_delete(
    user_id: str, wallet: WalletTypeInfo = Depends(require_admin_key)
):
    user = await get_user(user_id)

    if not user:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="User does not exist."
        )

    if user.wallet != wallet.wallet.id:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail="Not your User."
        )

    await delete_user(user_id)
    return "", HTTPStatus.NO_CONTENT


# ANY OTHER ENDPOINTS YOU NEED

## This endpoint creates a payment


@merchantpill_ext.post(
    "/api/v1/user/payment/{user_id}", status_code=HTTPStatus.CREATED
)
async def api_tpos_create_invoice(
    user_id: str, amount: int = Query(..., ge=1), memo: str = ""
) -> dict:
    user = await get_user(user_id)

    if not user:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="User does not exist."
        )

    # we create a payment and add some tags, so tasks.py can grab the payment once its paid

    try:
        payment_hash, payment_request = await create_invoice(
            wallet_id=user.wallet,
            amount=amount,
            memo=f"{memo} to {user.name}" if memo else f"{user.name}",
            extra={
                "tag": "user",
                "amount": amount,
            },
        )
    except Exception as e:
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(e))

    return {"payment_hash": payment_hash, "payment_request": payment_request}
