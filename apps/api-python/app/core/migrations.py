"""
Database indexes for performance optimization.
Add indexes to frequently queried fields.
"""
from sqlalchemy import text


async def add_indexes(engine):
    """Add performance indexes to database tables."""
    async with engine.begin() as conn:
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_leads_email       ON leads(email)",
            "CREATE INDEX IF NOT EXISTS idx_leads_workspace   ON leads(workspace_id)",
            "CREATE INDEX IF NOT EXISTS idx_leads_created     ON leads(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_leads_status      ON leads(pipeline_stage)",
            "CREATE INDEX IF NOT EXISTS idx_leads_campaign    ON leads(campaign_id)",
            "CREATE INDEX IF NOT EXISTS idx_campaigns_ws      ON campaigns(workspace_id)",
            "CREATE INDEX IF NOT EXISTS idx_campaigns_status  ON campaigns(status)",
            "CREATE INDEX IF NOT EXISTS idx_users_email       ON users(email)",
        ]
        for sql in indexes:
            try:
                await conn.execute(text(sql))
            except Exception:
                pass   # index may already exist
