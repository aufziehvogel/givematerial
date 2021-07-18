class User:
    def __init__(self, user_id: str, name: str, **kwargs):
        self.id = user_id
        self.display_name = name

        self.wanikani_token = kwargs.get('wanikani_token', None)
        self.last_wanikani_update = kwargs.get('last_wanikani_update', None)

    @property
    def is_active(self) -> bool:
        return True

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def is_anonymous(self) -> bool:
        return False

    def get_id(self) -> str:
        return self.id
