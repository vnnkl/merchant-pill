from typing import List, Optional, Union

from lnbits.helpers import urlsafe_short_hash
from lnbits.lnurl import encode as lnurl_encode
from . import db
from .models import CreateMerchantPillData, MerchantPill
from loguru import logger
from fastapi import Request
from lnurl import encode as lnurl_encode
import shortuuid


async def create_merchantpill(
    wallet_id: str, data: CreateMerchantPillData, req: Request
) -> MerchantPill:
    merchantpill_id = urlsafe_short_hash()
    await db.execute(
        """
        INSERT INTO merchantpill.maintable (id, wallet, name, lnurlpayamount, lnurlwithdrawamount)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            merchantpill_id,
            wallet_id,
            data.name,
            data.lnurlpayamount,
            data.lnurlwithdrawamount,
        ),
    )
    merchantpill = await get_merchantpill(merchantpill_id, req)
    assert merchantpill, "Newly created table couldn't be retrieved"
    return merchantpill


async def get_merchantpill(
    merchantpill_id: str, req: Optional[Request] = None
) -> Optional[MerchantPill]:
    row = await db.fetchone(
        "SELECT * FROM merchantpill.maintable WHERE id = ?", (merchantpill_id,)
    )
    if not row:
        return None
    rowAmended = MerchantPill(**row)
    if req:
        rowAmended.lnurlpay = lnurl_encode(
            req.url_for("merchantpill.api_lnurl_pay", merchantpill_id=row.id)._url
        )
        rowAmended.lnurlwithdraw = lnurl_encode(
            req.url_for(
                "merchantpill.api_lnurl_withdraw",
                merchantpill_id=row.id,
                tickerhash=shortuuid.uuid(name=rowAmended.id + str(rowAmended.ticker)),
            )._url
        )
    return rowAmended


async def get_merchantpills(
    wallet_ids: Union[str, List[str]], req: Optional[Request] = None
) -> List[MerchantPill]:
    if isinstance(wallet_ids, str):
        wallet_ids = [wallet_ids]

    q = ",".join(["?"] * len(wallet_ids))
    rows = await db.fetchall(
        f"SELECT * FROM merchantpill.maintable WHERE wallet IN ({q})", (*wallet_ids,)
    )
    tempRows = [MerchantPill(**row) for row in rows]
    if req:
        for row in tempRows:
            row.lnurlpay = lnurl_encode(
                req.url_for("merchantpill.api_lnurl_pay", merchantpill_id=row.id)._url
            )
            row.lnurlwithdraw = lnurl_encode(
                req.url_for(
                    "merchantpill.api_lnurl_withdraw",
                    merchantpill_id=row.id,
                    tickerhash=shortuuid.uuid(name=row.id + str(row.ticker)),
                )._url
            )
    return tempRows


async def update_merchantpill(
    merchantpill_id: str, req: Optional[Request] = None, **kwargs
) -> MerchantPill:
    q = ", ".join([f"{field[0]} = ?" for field in kwargs.items()])
    await db.execute(
        f"UPDATE merchantpill.maintable SET {q} WHERE id = ?",
        (*kwargs.values(), merchantpill_id),
    )
    merchantpill = await get_merchantpill(merchantpill_id, req)
    assert merchantpill, "Newly updated merchantpill couldn't be retrieved"
    return merchantpill


async def delete_merchantpill(merchantpill_id: str) -> None:
    await db.execute(
        "DELETE FROM merchantpill.maintable WHERE id = ?", (merchantpill_id,)
    )
