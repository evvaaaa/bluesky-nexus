from abc import ABC, abstractmethod
from tiled.client.stream import LiveChildCreated
from nexusformat import nexus


class SubscriptionBase(ABC):
    def __call__(self, update: LiveChildCreated):
        print(update.key, update.access_tags)

    @abstractmethod
    def process_nexus_structure(self, generated_structure: nexus.NXroot) -> None:
        """Abstract method where the nexus structure generated through this subscription
        can be processed in subclasses. For an example see `HdfWriterSubscription`."""
