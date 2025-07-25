class UnknownTempPropertyClass(Exception):
    """
    Raised when a temp property class is not found.
    """

    def __init__(self, name: str):
        self.name = name
        super().__init__(f"Unknown temp property class: {name}")
