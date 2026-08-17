class PersistenceError(Exception):
    """Base error for Learning Ecosystem persistence."""


class NotFoundError(PersistenceError):
    def __init__(self, entity: str, entity_id: str) -> None:
        super().__init__(f"{entity} not found: {entity_id}")
        self.entity = entity
        self.entity_id = entity_id


class MasteryNotJustifiedError(PersistenceError):
    """AT-07: mastery requires more than a single repeated definition."""
