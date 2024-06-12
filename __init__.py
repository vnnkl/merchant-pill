import asyncio

from fastapi import APIRouter

from lnbits.db import Database
from lnbits.helpers import template_renderer
from lnbits.tasks import create_permanent_unique_task
from loguru import logger

logger.debug("This logged message is from merchantpill/__init__.py, you can debug in your extension using 'import logger from loguru' and 'logger.debug(<thing-to-log>)'.")

db = Database("ext_merchantpill")

merchantpill_ext: APIRouter = APIRouter(
    prefix="/merchantpill", tags=["MyExtension"]
)

merchantpill_static_files = [
    {
        "path": "/merchantpill/static",
        "name": "merchantpill_static",
    }
]


def merchantpill_renderer():
    return template_renderer(["merchantpill/templates"])


from .lnurl import *
from .tasks import wait_for_paid_invoices
from .views import *
from .views_api import *

scheduled_tasks: list[asyncio.Task] = []

def merchantpill_stop():
    for task in scheduled_tasks:
        try:
            task.cancel()
        except Exception as ex:
            logger.warning(ex)

def merchantpill_start():
    task = create_permanent_unique_task("ext_merchantpill", wait_for_paid_invoices)
    scheduled_tasks.append(task)