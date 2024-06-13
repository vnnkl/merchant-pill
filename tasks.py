import asyncio

from loguru import logger

from lnbits.core.models import Payment
from lnbits.core.services import create_invoice, websocket_updater
from lnbits.helpers import get_current_extension_name
from lnbits.tasks import register_invoice_listener

from .crud import get_user, update_user, get_debt, update_debt, create_transaction


#######################################
########## RUN YOUR TASKS HERE ########
#######################################

# The usual task is to listen to invoices related to this extension


async def wait_for_paid_invoices():
    invoice_queue = asyncio.Queue()
    register_invoice_listener(invoice_queue, get_current_extension_name())
    while True:
        payment = await invoice_queue.get()
        await on_invoice_paid(payment)


# Do something when an invoice related to this extension is paid


async def on_invoice_paid(payment: Payment) -> None:
    if payment.extra.get("tag") != "MerchantPill":
        return

    user_id = payment.extra.get("userId")
    user = await get_user(user_id)

    # update something in the db
    if payment.extra.get("lnurlwithdraw"):
        total = user.total - payment.amount
    else:
        total = user.total + payment.amount
    data_to_update = {"total": total, "satoshipaid": payment.amount}

    await update_user(user_id=user_id, **data_to_update)

    # update debt if exists
    if user.debt_id:
        debt = await get_debt(user.debt_id)
        debt_data_to_update = {"debtPaid": debt.debtPaid + payment.amount}
        await update_debt(debt_id=user.debt_id, **debt_data_to_update)

    # create a transaction
    transaction_data = {
        "from_user_id": user_id,
        "to_user_id": user.invited_by,
        "amount": payment.amount,
        "currency": "euro",  # assuming euro as currency
    }
    await create_transaction(**transaction_data)

    # here we could send some data to a websocket on wss://<your-lnbits>/api/v1/ws/<user_id>
    # and then listen to it on the frontend, which we do with index.html connectWebocket()

    some_payment_data = {
        "name": user.name,
        "amount": payment.amount,
        "fee": payment.fee,
        "checking_id": payment.checking_id,
    }

    await websocket_updater(user_id, str(some_payment_data))
