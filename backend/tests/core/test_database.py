from core.database import make_async_url


class TestMakeAsyncUrl:
    def test_rewrites_mysql_scheme(self):
        assert (
            make_async_url("mysql://user:pass@localhost/app")
            == "mysql+aiomysql://user:pass@localhost/app"
        )

    def test_rewrites_pymysql_scheme(self):
        assert (
            make_async_url("mysql+pymysql://user:pass@localhost/app")
            == "mysql+aiomysql://user:pass@localhost/app"
        )

    def test_leaves_other_schemes_unchanged(self):
        url = "mysql+aiomysql://user:pass@localhost/app"
        assert make_async_url(url) == url
        assert make_async_url("sqlite+aiosqlite:///tmp.db") == "sqlite+aiosqlite:///tmp.db"
