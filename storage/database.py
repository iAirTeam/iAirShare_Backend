import sqlalchemy as sa

from utils.var import database


class FileDBModelV2:
    class FileDBModel(database.Model):
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.Text)
        file_id = sa.Column(sa.String(128), unique=True)
        property = sa.Column(sa.JSON)
        access_token = sa.Column(sa.Text)

    class DirectoryDBModel(database.Model):
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.Text)
        pointer = sa.Column(sa.Integer, sa.ForeignKey('DirectoryDBModel'))
        access_token = sa.Column(sa.Text)
        property = sa.Column(sa.JSON)

    class DisplayDBModel(database.Model):
        id = sa.Column(sa.Integer, primary_key=True)
        list = sa.Column()


class FileDBModelV1:
    class RepoDBModel(database.Model):
        id = sa.Column(sa.Integer, primary_key=True)
        repo_name = sa.Column(sa.Text, unique=True)
        access_token = sa.Column(sa.Text)
        mapping = sa.Column(sa.JSON)


RepoDBModel = FileDBModelV1.RepoDBModel
