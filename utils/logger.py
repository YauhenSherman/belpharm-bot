import logging


def setup_logger() -> logging.Logger:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    # Делаем шумные библиотеки тише
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("telegram.ext.ExtBot").setLevel(logging.WARNING)

    logger = logging.getLogger("belpharm_bot")
    logger.setLevel(logging.INFO)

    return logger


logger = setup_logger()