from ..models.user import AbstractNomadicodeUser


class User(AbstractNomadicodeUser):
    class Meta(AbstractNomadicodeUser.Meta):
        abstract = False
        db_table = "nomadicode_auth_user"
