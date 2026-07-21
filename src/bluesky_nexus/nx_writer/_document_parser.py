from event_model import EventDescriptor, Configuration, DataKey, Event
import h5py

@dataclass
class ParsedNxData:
    name: str
    data = ParsedNxData



@dataclass
class ParsedNxGroup:
    name: str
    data = 

class ParsedDevice:
    def __init__(self, object_key: str) -> None:
        self.object_key = object_key
        self._schema: dict | None = None
        self._signals: dict[str, str] = {}
        self._data = {}
        self._structure = {}
        self.nx_class = {}

    def _generate_default_structure(
        self, configuration_keys: list[str], data_keys: list[str]
    ):
        self._structure = {
            "configuration": {
                k.lstrip(self._object_key).lstrip("-").lstrip("_"): k
                for k in configuration_keys
            },
            "data": {
                k.lstrip(self._object_key).lstrip("-").lstrip("_"): k for k in data_keys
            },
        }

        self.nx_class = "NXobject"

    def write_into_group(group: h5py.Group, structure: dict | None = None):
        structure = structure or self._structure
        for key_value  in self.

    def _get_patched_schema(self, unpatched_schema: dict) -> dict:
        """Replaces $obj with the object key name."""

        patched_schema = {}
        for key, value in unpatched_schema.items():
            if isinstance(value, dict):
                value = self._get_patched_schema(value)
            elif isinstance(value, str):
                value = value.replace("{obj}", self.object_key)
            if isinstance(key, str):
                key = key.replace("{obj}", self.object_key)
            patched_schema[key] = value

        return patched_schema

    def descriptor(self, descriptor: EventDescriptor) -> None:
        hints = descriptor.get("hints", {}).get(self.object_key, {})
        configuration: dict[str, Configuration] = descriptor.get("configuration", {})
        data_keys: dict[str, DataKey] = descriptor["data_keys"]

        if "NX_schema" in hints:
            schema = self._get_patched_schema(hints["NX_schema"])
            self.nx_class = schema.pop("nx_class", "NXobject")
            self._structure = schema
        else:
            self._generate_default_structure(list(configuration), list(data_keys))

        self._data = {}
        for _, device_configuration in configuration.items():
            for data_key, value in device_configuration.items():
                self._data[data_key] = [value]

        for data_key in data_keys:
            self._data[data_key] = []

    def event(self, event: Event):
        """Parse an event for data and store it."""
        for data_key, data in event["data"].items():
            if data_key in self._data:
                self._data[data_key].append(data)

    def event_page(self, event: Event):
        """Parse an event descriptor for data and store it."""
        for data_key, data in event["data"].items():
            if data_key in self._data:
                self._data[data_key] += data
