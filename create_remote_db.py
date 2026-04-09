import pymysql
import config
from sqlalchemy.engine.url import make_url


def main():
    url = make_url(config.SQLALCHEMY_DATABASE_URI)
    if not url.drivername.startswith("mysql"):
        raise SystemExit("SQLALCHEMY_DATABASE_URI must point to a MySQL database.")
    if not url.database:
        raise SystemExit("SQLALCHEMY_DATABASE_URI must include a database name.")

    connection_kwargs = {
        "host": url.host or "127.0.0.1",
        "user": url.username,
        "password": url.password,
        "port": int(url.port or 3306),
        "charset": "utf8mb4",
    }

    print(
        f"Connecting to MySQL server {connection_kwargs['host']}:{connection_kwargs['port']} "
        f"as {connection_kwargs['user']}..."
    )

    try:
        conn = pymysql.connect(**connection_kwargs)
        cursor = conn.cursor()
        print(f"Creating database '{url.database}' if not exists...")
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS `{url.database}` "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
        conn.commit()
        conn.close()
        print("Database created or verified successfully.")
    except Exception as exc:
        print(f"Error: {exc}")


if __name__ == "__main__":
    main()
