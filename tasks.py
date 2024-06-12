import asyncio

from loguru import logger

from lnbits.core.models import Payment
from lnbits.core.services import create_invoice, websocket_updater
from lnbits.helpers import get_current_extension_name
from lnbits.tasks import register_invoice_listener

from .crud import get_merchantpill, update_merchantpill


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


# Do somethhing when an invoice related top this extension is paid


async def on_invoice_paid(payment: Payment) -> None:
    if payment.extra.get("tag") != "MyExtension":
        return

    merchantpill_id = payment.extra.get("merchantpillId")
    merchantpill = await get_merchantpill(merchantpill_id)

    # update something in the db
    if payment.extra.get("lnurlwithdraw"):
        total = merchantpill.total - payment.amount
    else:
        total = merchantpill.total + payment.amount
    data_to_update = {"total": total}

    await update_merchantpill(merchantpill_id=merchantpill_id, **data_to_update)

    # here we could send some data to a websocket on wss://<your-lnbits>/api/v1/ws/<merchantpill_id>
    # and then listen to it on the frontend, which we do with index.html connectWebocket()

    some_payment_data = {
        "name": merchantpill.name,
        "amount": payment.amount,
        "fee": payment.fee,
        "checking_id": payment.checking_id,
    }

    await websocket_updater(merchantpill_id, str(some_payment_data))
