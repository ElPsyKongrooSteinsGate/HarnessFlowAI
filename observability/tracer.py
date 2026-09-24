class Tracer:
    def __init__(self):
        self.events = []

    async def flush(self) -> None:
        self.events.clear()
