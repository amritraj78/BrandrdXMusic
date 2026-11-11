from motor.motor_asyncio import AsyncIOMotorClient as _mongo_client_
from pymongo import MongoClient

import config
from ..logging import LOGGER

if not config.MONGO_DB_URI:
    LOGGER(__name__).critical("MONGO_DB_URI is missing! Please configure MONGO_DB_URI in environment variables.")
    raise SystemExit("[ERROR] - MONGO_DB_URI is required to run the bot.")

_mongo_async_ = _mongo_client_(config.MONGO_DB_URI)
_mongo_sync_ = MongoClient(config.MONGO_DB_URI)
mongodb = _mongo_async_.BrandrdXMusic
pymongodb = _mongo_sync_.BrandrdXMusic
