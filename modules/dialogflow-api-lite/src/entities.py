import re
import sys
import os

import google.cloud.dialogflow_v2 as dialogflow


class EntityType:
    def __init__(self, entity_obj=None) -> None:

        self._entity_obj = entity_obj
        self._value_map = {}

        for value in self.values:
            self._value_map[value.value] = value

    @property
    def name(self):
        return self._entity_obj.name

    @property
    def display_name(self):
        return self._entity_obj.display_name

    @property
    def values(self):
        values = []
        for value in self._entity_obj.entities:
            values.append(value)
        return values

    @property
    def synonyms(self, value):
        return (
            self._value_map[value].synonyms
            if hasattr(self._value_map[value], "synonyms")
            else None
        )

    @property
    def kind(self):
        return self._entity_obj.kind

    @property
    def enable_fuzzy_extraction(self):
        return self._entity_obj.enable_fuzzy_extraction

    def enable_synonyms(self, value):
        self._entity_obj.kind = (
            dialogflow.Kind.KIND_MAP if value else dialogflow.Kind.KIND_LIST
        )


class EntityClient:
    def __init__(self, config) -> None:

        self.validate_config(config)

        self._config = config

        self.configure()

        self._client = dialogflow.EntityTypesClient()

        self._entities = {"name": {}, "display_name": {}}

    def configure(self):

        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.credential
        os.environ["GOOGLE_CLOUD_PROJECT"] = self.project_id

    def validate_config(self, config):
        if not config:
            raise Exception("Config not found!")

        try:
            keys = ["project_id", "credential"]
            for key in keys:
                config[key]
        except Exception as e:
            raise Exception("Config validation failed! Please provide a valid config.")

    @property
    def project_id(self):
        return self._config.get("project_id", "")

    @property
    def credential(self):
        return self._config.get("credential", "")

    @property
    def parent(self):
        return f"projects/{self.project_id}/agent"

    @property
    def entity_types_client(self):
        return self._client

    def batch_create(self):
        pass

    def batch_create_types(self):
        pass

    def batch_delete(self):
        pass

    def batch_delete_types(self):
        pass

    def batch_update(self):
        pass

    def batch_update_types(self, entity_types):

        request = {
            "parent": self.parent,
            "entity_type_batch_inline": {"entity_types": entity_types},
        }

        operation = self._client.batch_update_entity_types(request=request)

        return operation.result()

    def create(self, entity_type):

        request = {
            "parent": self.parent,
            "entity_type": entity_type,
        }

        return self._client.create_entity_type(request=request)

    def update(self, entity_type):

        request = {
            "entity_type": entity_type,
        }

        return self._client.update_entity_type(request=request)

    def delete(self):
        pass

    def get(self):
        pass

    def list(self):

        request = {"parent": self.parent}

        page_result = self.entity_types_client.list_entity_types(request=request)

        for response in page_result:
            entity = EntityType(response)

            self._entities["name"][entity.name] = entity
            self._entities["display_name"][entity.display_name] = entity


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--project_id", dest="project_id", type=str, help="Google Cloud Project Id"
    )
    parser.add_argument(
        "--credential",
        dest="credential",
        type=str,
        help="Path to Google Cloud Project credential",
    )

    args = parser.parse_args()

    config = {"project_id": args.project_id, "credential": args.credential}

    client = EntityClient(config)
    client.list()

    entity = {
        "display_name": "movie-titles",
        "kind": "KIND_LIST",
        "entities": [
            {"value": "Harry Potter"},
            {"value": "The Matrix"},
            {"value": "Avengers"},
        ],
    }

    print(client.create(entity))
