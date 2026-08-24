from dataclasses import dataclass


@dataclass
class ProviderStats:

    provider: str

    fetched: int = 0

    returned: int = 0

    duplicates: int = 0

    fresh: int = 0

    exported: int = 0