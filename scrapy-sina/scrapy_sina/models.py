from peewee import MySQLDatabase, Model
from peewee import AutoField, CharField, DateTimeField, TextField
from scrapy.utils.project import get_project_settings

settings = get_project_settings()
db = MySQLDatabase(database=settings.get("MYSQL_DATABASE"),
                   host=settings.get("MYSQL_HOST"),
                   port=settings.get("MYSQL_PORT"),
                   user=settings.get("MYSQL_USERNAME"),
                   password=settings.get("MYSQL_PASSWORD"))


class SinaNews(Model):
    id = AutoField()
    title = CharField(unique=True)
    publish_time = DateTimeField()
    content = TextField()
    spider_time = DateTimeField()

    class Meta:
        database = db
        db_table = "ai_news"