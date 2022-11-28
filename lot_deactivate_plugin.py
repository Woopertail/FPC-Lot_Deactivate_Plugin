"""
Данный плагин деактивирует лоты, если товары для данного лота закончилось.
"""


from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from cardinal import Cardinal
    from FunPayAPI.orders import Order

from threading import Thread
import traceback
import logging
import json
import time


logger = logging.getLogger(f"Cardinal.{__name__}")


def get_products_count(path: str):
    with open(path, "r", encoding="utf-8") as f:
        products = f.read()

    products = json.loads(products)
    return len(products)


def deactivate_lot(order: Order, text: str, cardinal: Cardinal, errored: bool, *args):
    """
    Деактивирует лот, если закончились товары.
    """
    if errored:
        return

    for cfg_lot_name in cardinal.auto_delivery_config.sections():
        if cfg_lot_name not in order.title:
            continue

        if cardinal.auto_delivery_config[cfg_lot_name].get("productsFilePath") is None:
            continue

        if get_products_count(cardinal.auto_delivery_config[cfg_lot_name]["productsFilePath"]):
            continue

        cardinal_lots = [clot for clot in cardinal.lots if cfg_lot_name in clot.title]
        if not cardinal_lots:
            return

        clot = cardinal_lots[0]

        attempts = 3
        while attempts:
            try:
                result = cardinal.account.change_lot_state(clot.id, clot.game_id, state=False)
                if result.get("error"):
                    logger.warning(f"Не удалось деактивировать лот $YELLOW{clot.id}.")
                    logger.debug(result)
                    attempts -= 1
                    time.sleep(1)
                else:
                    logger.info(f"Деактивировал лот $YELLOW{clot.id}.")
                    break
            except:
                logger.error(f"Произошла пошибка при деактивации лота $YELLOW{clot.id}.")
                logger.debug(traceback.format_exc())
                attempts -= 1
                time.sleep(1)
        if not attempts:
            logger.error("Не удалось деактивировать лот $YELLOW{clot.id}$color: превышено кол-во попыток.")
            return


def deactivate_lot_handler(order: Order, text: str, cardinal: Cardinal, errored: bool, *args):
    Thread(target=deactivate_lot, args=(order, text, cardinal, errored, *args, )).start()


REGISTER_TO_DELIVERY_EVENT = [
    deactivate_lot_handler
]
