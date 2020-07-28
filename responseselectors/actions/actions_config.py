"""Configuration for custom action of Response Selector"""
import logging
from pathlib import Path
import ruamel.yaml

logger = logging.getLogger(__name__)

botconfig = (
    ruamel.yaml.safe_load(open(f"{Path(__file__).parents[0]}/bot_config.yml", "r"))
    or {}
)


# Askextension data after ETL
askextension_parquet = botconfig.get("askextension-parquet", None)

# original osticket that was scraped
askextension_url = botconfig.get("askextension-url", None)

logger.info("----------------------------------------------")
logger.info("ResponseSelector configuration:")
logger.info("- askextension_parquet = %s", askextension_parquet)
logger.info("- askextension_url     = %s", askextension_url)
logger.info("----------------------------------------------")
