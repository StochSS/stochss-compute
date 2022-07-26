class ResourceException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
        print('Missing or misconfigured resources.')