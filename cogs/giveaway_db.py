import aiomysql

DB_HOST = "sql001.hostmybot.net"
DB_USER = "u2377_9k1Ld53S4E"
DB_PASS = "DVc8+t%^=JfUxG!gAb4zb4+rA"
DB_NAME = "s2377_SentriX"
DB_PORT = 3306


async def get_db():
    return await aiomysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        db=DB_NAME,
        port=DB_PORT,
        autocommit=True
    )


async def setup_tables():
    db = await get_db()
    cur = await db.cursor()

    # Main giveaway table
    await cur.execute("""
        CREATE TABLE IF NOT EXISTS giveaways (
            id INT AUTO_INCREMENT PRIMARY KEY,
            channel_id BIGINT NOT NULL,
            message_id BIGINT,
            sponsor VARCHAR(255),
            prize VARCHAR(255),
            description TEXT,
            start_time DATETIME,
            end_time DATETIME,
            winners INT,
            image LONGBLOB,
            launched BOOLEAN DEFAULT 0,
            ended BOOLEAN DEFAULT 0
        )
    """)

    # Entry table
    await cur.execute("""
        CREATE TABLE IF NOT EXISTS giveaway_entries (
            id INT AUTO_INCREMENT PRIMARY KEY,
            giveaway_id INT NOT NULL,
            user_id BIGINT NOT NULL,
            UNIQUE KEY (giveaway_id, user_id)
        )
    """)

    await cur.close()
    db.close()