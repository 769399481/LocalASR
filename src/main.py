import logging
from logging.handlers import RotatingFileHandler

from batch import BatchProcessor
from config import LOG_DIR


def main():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[logging.StreamHandler(), RotatingFileHandler(
            LOG_DIR / "asr.log", maxBytes=2_000_000, backupCount=3, encoding="utf-8")],
        force=True,
    )
    logging.info("Application started")
    try:
        summary = BatchProcessor().run()
        return 1 if summary.failed else 0
    except Exception:
        logging.exception("Application failed")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
