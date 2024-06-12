# Maybe your extension needs some LNURL stuff.
# Here is a very simple example of how to do it.
# Feel free to delete this file if you don't need it.

from http import HTTPStatus
from fastapi import Depends, Query, Request
from . import merchantpill_ext
from .crud import get_merchantpill
from lnbits.core.services import create_invoice, pay_invoice
from loguru import logger
from typing import Optional
from .crud import update_merchantpill
from .models import MerchantPill
import shortuuid

#################################################
########### A very simple LNURLpay ##############
# https://github.com/lnurl/luds/blob/luds/06.md #
#################################################
#################################################


@merchantpill_ext.get(
    "/api/v1/lnurl/pay/{merchantpill_id}",
    status_code=HTTPStatus.OK,
    name="merchantpill.api_lnurl_pay",
)
async def api_lnurl_pay(
    request: Request,
    merchantpill_id: str,
):
    merchantpill = await get_merchantpill(merchantpill_id)
    if not merchantpill:
        return {"status": "ERROR", "reason": "No merchantpill found"}
    return {
        "callback": str(
            request.url_for(
                "merchantpill.api_lnurl_pay_callback", merchantpill_id=merchantpill_id
            )
        ),
        "maxSendable": merchantpill.lnurlpayamount * 1000,
        "minSendable": merchantpill.lnurlpayamount * 1000,
        "metadata": '[["text/plain", "' + merchantpill.name + '"]]',
        "tag": "payRequest",
    }


@merchantpill_ext.get(
    "/api/v1/lnurl/paycb/{merchantpill_id}",
    status_code=HTTPStatus.OK,
    name="merchantpill.api_lnurl_pay_callback",
)
async def api_lnurl_pay_cb(
    request: Request,
    merchantpill_id: str,
    amount: int = Query(...),
):
    merchantpill = await get_merchantpill(merchantpill_id)
    logger.debug(merchantpill)
    if not merchantpill:
        return {"status": "ERROR", "reason": "No merchantpill found"}

    payment_hash, payment_request = await create_invoice(
        wallet_id=merchantpill.wallet,
        amount=int(amount / 1000),
        memo=merchantpill.name,
        unhashed_description=f'[["text/plain", "{merchantpill.name}"]]'.encode(),
        extra={
            "tag": "MerchantPill",
            "merchantpillId": merchantpill_id,
            "extra": request.query_params.get("amount"),
        },
    )
    return {
        "pr": payment_request,
        "routes": [],
        "successAction": {"tag": "message", "message": f"Paid {merchantpill.name}"},
    }


#################################################
######## A very simple LNURLwithdraw ############
# https://github.com/lnurl/luds/blob/luds/03.md #
#################################################
## withdraws are unique, removing 'tickerhash' ##
## here and crud.py will allow muliple pulls ####
#################################################


@merchantpill_ext.get(
    "/api/v1/lnurl/withdraw/{merchantpill_id}/{tickerhash}",
    status_code=HTTPStatus.OK,
    name="merchantpill.api_lnurl_withdraw",
)
async def api_lnurl_withdraw(
    request: Request,
    merchantpill_id: str,
    tickerhash: str,
):
    merchantpill = await get_merchantpill(merchantpill_id)
    if not merchantpill:
        return {"status": "ERROR", "reason": "No merchantpill found"}
    k1 = shortuuid.uuid(name=merchantpill.id + str(merchantpill.ticker))
    if k1 != tickerhash:
        return {"status": "ERROR", "reason": "LNURLw already used"}

    return {
        "tag": "withdrawRequest",
        "callback": str(
            request.url_for(
                "merchantpill.api_lnurl_withdraw_callback", merchantpill_id=merchantpill_id
            )
        ),
        "k1": k1,
        "defaultDescription": merchantpill.name,
        "maxWithdrawable": merchantpill.lnurlwithdrawamount * 1000,
        "minWithdrawable": merchantpill.lnurlwithdrawamount * 1000,
    }


@merchantpill_ext.get(
    "/api/v1/lnurl/withdrawcb/{merchantpill_id}",
    status_code=HTTPStatus.OK,
    name="merchantpill.api_lnurl_withdraw_callback",
)
async def api_lnurl_withdraw_cb(
    request: Request,
    merchantpill_id: str,
    pr: Optional[str] = None,
    k1: Optional[str] = None,
):
    assert k1, "k1 is required"
    assert pr, "pr is required"
    merchantpill = await get_merchantpill(merchantpill_id)
    if not merchantpill:
        return {"status": "ERROR", "reason": "No merchantpill found"}

    k1Check = shortuuid.uuid(name=merchantpill.id + str(merchantpill.ticker))
    if k1Check != k1:
        return {"status": "ERROR", "reason": "Wrong k1 check provided"}

    await update_merchantpill(
        merchantpill_id=merchantpill_id, ticker=merchantpill.ticker + 1
    )
    await pay_invoice(
        wallet_id=merchantpill.wallet,
        payment_request=pr,
        max_sat=int(merchantpill.lnurlwithdrawamount * 1000),
        extra={
            "tag": "MerchantPill",
            "merchantpillId": merchantpill_id,
            "lnurlwithdraw": True,
        },
    )
    return {"status": "OK"}
