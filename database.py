import sqlite3
import aiosqlite
from datetime import datetime
from typing import Optional, List, Dict

class Database:
    def __init__(self, db_path: str = "moderation.db"):
        self.db_path = db_path
    
    async def init_db(self):
        async with aiosqlite.connect(self.db_path) as db:
            # Warnings table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS warnings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    moderator_id INTEGER NOT NULL,
                    reason TEXT,
                    timestamp TEXT NOT NULL
                )
            """)
            
            # Mod actions log table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS mod_actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    action_type TEXT NOT NULL,
                    user_id INTEGER NOT NULL,
                    moderator_id INTEGER NOT NULL,
                    reason TEXT,
                    duration INTEGER,
                    timestamp TEXT NOT NULL
                )
            """)
            
            # Mod log channel settings
            await db.execute("""
                CREATE TABLE IF NOT EXISTS mod_config (
                    guild_id INTEGER PRIMARY KEY,
                    log_channel_id INTEGER
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS upvotes (
                    user_id INTEGER NOT NULL,
                    showcase_id INTEGER NOT NULL
                )
                """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS thread_followers (
                    thread_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    PRIMARY KEY (thread_id, user_id)
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    channel_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    username TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    closed_at TEXT,
                    closed_by INTEGER,
                    status TEXT DEFAULT 'open',
                    transcript_url TEXT
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS ticket_participants (
                    ticket_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    added_by INTEGER NOT NULL,
                    added_at TEXT NOT NULL,
                    PRIMARY KEY (ticket_id, user_id),
                    FOREIGN KEY (ticket_id) REFERENCES tickets(id)
                )
            """)

            await db.commit()
    
    # Warning methods
    async def add_warning(self, guild_id: int, user_id: int, moderator_id: int, reason: str) -> int:
        timestamp = datetime.utcnow().isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "INSERT INTO warnings (guild_id, user_id, moderator_id, reason, timestamp) VALUES (?, ?, ?, ?, ?)",
                (guild_id, user_id, moderator_id, reason, timestamp)
            )
            await db.commit()
            return cursor.lastrowid
    
    async def get_warnings(self, guild_id: int, user_id: int) -> List[Dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM warnings WHERE guild_id = ? AND user_id = ? ORDER BY timestamp DESC",
                (guild_id, user_id)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def remove_warning(self, warning_id: int) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("DELETE FROM warnings WHERE id = ?", (warning_id,))
            await db.commit()
            return cursor.rowcount > 0
    
    async def clear_warnings(self, guild_id: int, user_id: int) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "DELETE FROM warnings WHERE guild_id = ? AND user_id = ?",
                (guild_id, user_id)
            )
            await db.commit()
            return cursor.rowcount
    
    # Mod actions log
    async def log_action(self, guild_id: int, action_type: str, user_id: int, 
                        moderator_id: int, reason: str = None, duration: int = None):
        timestamp = datetime.utcnow().isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO mod_actions (guild_id, action_type, user_id, moderator_id, reason, duration, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (guild_id, action_type, user_id, moderator_id, reason, duration, timestamp)
            )
            await db.commit()
    
    async def get_user_history(self, guild_id: int, user_id: int) -> List[Dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM mod_actions WHERE guild_id = ? AND user_id = ? ORDER BY timestamp DESC LIMIT 50",
                (guild_id, user_id)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    # Config methods
    async def set_log_channel(self, guild_id: int, channel_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO mod_config (guild_id, log_channel_id) VALUES (?, ?)",
                (guild_id, channel_id)
            )
            await db.commit()
    
    async def get_log_channel(self, guild_id: int) -> Optional[int]:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT log_channel_id FROM mod_config WHERE guild_id = ?",
                (guild_id,)
            )
            row = await cursor.fetchone()
            return row[0] if row else None
        
    async def log_upvote(self, user_id: int, showcase_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO upvotes (user_id, showcase_id) VALUES (?, ?)",
                (user_id, showcase_id)
            )
            await db.commit()

    async def get_upvotes(self, showcase_id: int) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT COUNT(*) FROM upvotes WHERE showcase_id = ?",
                (showcase_id,)
            )
            row = await cursor.fetchone()
            return row[0] if row else 0
        
    async def has_user_upvoted(self, user_id: int, showcase_id: int) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT 1 FROM upvotes WHERE user_id = ? AND showcase_id = ?",
                (user_id, showcase_id)
            )
            row = await cursor.fetchone()
            return row is not None
    
    async def remove_upvote(self, user_id: int, showcase_id: int) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "DELETE FROM upvotes WHERE user_id = ? AND showcase_id = ?",
                (user_id, showcase_id)
            )
            await db.commit()
            return cursor.rowcount > 0
        
    async def get_top_5_showcases(self) -> List[Dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT showcase_id, COUNT(*) as upvote_count
                FROM upvotes
                GROUP BY showcase_id
                ORDER BY upvote_count DESC
                LIMIT 5
                """
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    # Thread follower methods
    async def add_thread_follower(self, thread_id: int, user_id: int) -> bool:
        """Add a user as a follower of a thread. Returns True if added, False if already following."""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(
                    "INSERT INTO thread_followers (thread_id, user_id) VALUES (?, ?)",
                    (thread_id, user_id)
                )
                await db.commit()
                return True
            except sqlite3.IntegrityError:
                return False
    
    async def remove_thread_follower(self, thread_id: int, user_id: int) -> bool:
        """Remove a user as a follower of a thread. Returns True if removed, False if not following."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "DELETE FROM thread_followers WHERE thread_id = ? AND user_id = ?",
                (thread_id, user_id)
            )
            await db.commit()
            return cursor.rowcount > 0
    
    async def get_thread_followers(self, thread_id: int) -> List[int]:
        """Get all followers of a thread."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT user_id FROM thread_followers WHERE thread_id = ?",
                (thread_id,)
            )
            rows = await cursor.fetchall()
            return [row[0] for row in rows]
    
    async def is_following_thread(self, thread_id: int, user_id: int) -> bool:
        """Check if a user is following a thread."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT 1 FROM thread_followers WHERE thread_id = ? AND user_id = ?",
                (thread_id, user_id)
            )
            row = await cursor.fetchone()
            return row is not None
    
    # Ticket methods
    async def create_ticket(self, guild_id: int, channel_id: int, user_id: int, username: str) -> int:
        """Create a new ticket record and return the ticket ID"""
        timestamp = datetime.utcnow().isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "INSERT INTO tickets (guild_id, channel_id, user_id, username, created_at) VALUES (?, ?, ?, ?, ?)",
                (guild_id, channel_id, user_id, username, timestamp)
            )
            await db.commit()
            return cursor.lastrowid

    async def close_ticket(self, channel_id: int, closed_by: int, transcript_url: str = None) -> bool:
        """Close a ticket by channel ID"""
        timestamp = datetime.utcnow().isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "UPDATE tickets SET closed_at = ?, closed_by = ?, status = 'closed', transcript_url = ? WHERE channel_id = ?",
                (timestamp, closed_by, transcript_url, channel_id)
            )
            await db.commit()
            return cursor.rowcount > 0

    async def get_ticket_by_channel(self, channel_id: int) -> Optional[Dict]:
        """Get ticket info by channel ID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM tickets WHERE channel_id = ?",
                (channel_id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def get_open_tickets(self, guild_id: int) -> List[Dict]:
        """Get all open tickets for a guild"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM tickets WHERE guild_id = ? AND status = 'open' ORDER BY created_at DESC",
                (guild_id,)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_user_tickets(self, guild_id: int, user_id: int, limit: int = 10) -> List[Dict]:
        """Get recent tickets for a user"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM tickets WHERE guild_id = ? AND user_id = ? ORDER BY created_at DESC LIMIT ?",
                (guild_id, user_id, limit)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def add_ticket_participant(self, ticket_id: int, user_id: int, added_by: int) -> bool:
        """Add a participant to a ticket"""
        timestamp = datetime.utcnow().isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(
                    "INSERT INTO ticket_participants (ticket_id, user_id, added_by, added_at) VALUES (?, ?, ?, ?)",
                    (ticket_id, user_id, added_by, timestamp)
                )
                await db.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    async def remove_ticket_participant(self, ticket_id: int, user_id: int) -> bool:
        """Remove a participant from a ticket"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "DELETE FROM ticket_participants WHERE ticket_id = ? AND user_id = ?",
                (ticket_id, user_id)
            )
            await db.commit()
            return cursor.rowcount > 0

    async def get_ticket_stats(self, guild_id: int) -> Dict:
        """Get ticket statistics for a guild"""
        async with aiosqlite.connect(self.db_path) as db:
            # Total tickets
            cursor = await db.execute(
                "SELECT COUNT(*) FROM tickets WHERE guild_id = ?",
                (guild_id,)
            )
            total = (await cursor.fetchone())[0]

            # Open tickets
            cursor = await db.execute(
                "SELECT COUNT(*) FROM tickets WHERE guild_id = ? AND status = 'open'",
                (guild_id,)
            )
            open_count = (await cursor.fetchone())[0]

            # Closed tickets
            cursor = await db.execute(
                "SELECT COUNT(*) FROM tickets WHERE guild_id = ? AND status = 'closed'",
                (guild_id,)
            )
            closed_count = (await cursor.fetchone())[0]

            return {
                'total': total,
                'open': open_count,
                'closed': closed_count
            }