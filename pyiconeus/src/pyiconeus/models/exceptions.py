class BadFile(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message
    
    def __str__(self) -> str:
        return f"{self.message}"
