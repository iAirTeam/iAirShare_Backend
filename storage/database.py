from flask_sqlalchemy.extension import sa

from storage.integrated.shared import sqlalchemy


class FileDBModelV2:
    """
     Actually Onlyacat who know the detail was getting ready for 中考 currently...
        It will be hard to impl
    """

    class FileDBModel(sqlalchemy.Model):
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.Text)
        file_id = sa.Column(sa.String(128), unique=True)
        property = sa.Column(sa.JSON)
        access_token = sa.Column(sa.Text)

    class DirectoryDBModel(sqlalchemy.Model):
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.Text)
        pointer = sa.Column(sa.Integer, sa.ForeignKey('DirectoryDBModel'))
        access_token = sa.Column(sa.Text)
        property = sa.Column(sa.JSON)

    class DisplayDBModel(sqlalchemy.Model):
        id = sa.Column(sa.Integer, primary_key=True)
        list = sa.Column()

class FileDBModelV1:
    class RepoDBModel(sqlalchemy.Model):
        id = sa.Column(sa.Integer, primary_key=True)
        repo_name = sa.Column(sa.Text, unique=True)
        access_token = sa.Column(sa.Text)
        mapping = sa.Column(sa.JSON)


RepoDBModel = FileDBModelV1.RepoDBModel
