# Data models for your extension

from sqlite3 import Row
from typing import Optional, List
from pydantic import BaseModel
from fastapi import Request

from lnbits.lnurl import encode as lnurl_encode
from urllib.parse import urlparse


class CreateUser(BaseModel):
    wallet: Optional[str]
    name: Optional[str]
    total: Optional[int]
    lnurlpayamount: Optional[int]
    lnurlwithdrawamount: Optional[int]
    lnurlwithdraw: Optional[str]
    lnurlpay: Optional[str]
    invited_by: Optional[str]
    debt_id: Optional[str]


class User(BaseModel):
    id: str
    wallet: Optional[str]
    name: Optional[str]
    total: Optional[int]
    lnurlpayamount: Optional[int]
    lnurlwithdrawamount: Optional[int]
    lnurlwithdraw: Optional[str]
    lnurlpay: Optional[str]
    invited_by: Optional[str]
    debt_id: Optional[str]

    @classmethod
    def from_row(cls, row: Row) -> "User":
        return cls(**dict(row))


class Debt(BaseModel):
    id: str
    inviter_id: str
    inviterWallet: Optional[str]
    debtPaid: Optional[int]
    debtOutstanding: Optional[int]
    debtCurrency: Optional[str]

    @classmethod
    def from_row(cls, row: Row) -> "Debt":
        return cls(**dict(row))


class Transaction(BaseModel):
    id: str
    from_user_id: str
    to_user_id: str
    amount: Optional[int]
    currency: Optional[str]
    timestamp: Optional[str]

    @classmethod
    def from_row(cls, row: Row) -> "Transaction":
        return cls(**dict(row))