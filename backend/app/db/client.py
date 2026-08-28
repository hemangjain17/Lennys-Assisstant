from supabase import create_client, Client
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

def get_supabase_client() -> Client:
    if not settings.supabase_url or not settings.supabase_service_role_key:
        logger.warning("Supabase URL or Key is missing. Database operations will fail.")
        # We allow it to return None or raise an exception later if it is actually invoked without credentials
    return create_client(settings.supabase_url, settings.supabase_service_role_key)
