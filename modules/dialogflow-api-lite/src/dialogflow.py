import os
import sys
from uuid import uuid4

import google.cloud.dialogflow_v2 as dialogflow


class Intent:
    def __init__(self, intent_obj) -> None:
        self._intent_obj = intent_obj

        self._parent = None
        self._children = []

    @property
    def training_phrases(self):
        result = []
        for phrase in self._intent_obj.training_phrases:
            full_phrase = ""
            for part in phrase.parts:
                full_phrase += part.text
            result.append(full_phrase)
        return result

    @training_phrases.setter
    def training_phrases(self, phrases: list):
        training_phrases = []

        for phrase in phrases:
            parts = [{
                "text": phrase
            }]
            training_phrases.append({
                "type_": "EXAMPLE",
                "parts": parts
            })

        self.intent_obj.training_phrases = training_phrases

    @property
    def messages(self):
        result = []
        for message in self._intent_obj.messages:
            result.append(message.text.text)
        return result

    @property
    def has_messages(self):
        count = 0
        for message in self.messages:
            count += len(message)

        return count > 0

    @property
    def input_context_names(self):
        context_names = []

        for context in self._intent_obj.input_context_names:
            context_names.append(context.split("/")[-1])

        return context_names

    @property
    def intent_obj(self):
        return self._intent_obj

    def __repr__(self) -> str:
        return super().__repr__()

    def __str__(self) -> str:
        ret_val = ""

        ret_val += "=" * 80
        ret_val += f"Intent name: {self.intent_obj.name}"
        ret_val += f"Intent display_name: {self.intent_obj.display_name}"
        ret_val += f"Root followup intent: {self.intent_obj.root_followup_intent_name}"
        ret_val += (
            f"Parent followup intent: {self.intent_obj.parent_followup_intent_name}\n"
        )

        ret_val += "Input contexts:"
        for input_context_name in self.intent_obj.input_context_names:
            ret_val += f"\tName: {input_context_name}"

        ret_val += "Output contexts:"
        for output_context in self.intent_obj.output_contexts:
            ret_val += f"\tName: {output_context.name}"

        if self.intent_obj.action:
            ret_val += f"Action: {self.intent_obj.action}\n"

        if len(self.intent_obj.parameters) > 0:
            ret_val += "Parameters:"
            for param in self.intent_obj.parameters:
                ret_val += f"\tname: {param.name}"
                ret_val += f"\tdisplay_name: {param.display_name}"
                ret_val += (
                    f"\tentity_type_display_name: {param.entity_type_display_name}"
                )

                ret_val += f"\tvalue: {param.value}"

        if len(self.intent_obj.training_phrases) > 0:
            ret_val += "Training Phrases:"
            for phrase in self.intent_obj.training_phrases:
                full_phrase = ""
                for part in phrase.parts:
                    full_phrase += part.text
                    # ret_val += f"\t{part}")
                ret_val += f"\t{full_phrase}"

            ret_val += "=" * 80
            ret_val += "\n"
            ret_val += "\n"


class Dialogflow:
    def __init__(self, config) -> None:

        self.validate_config(config)

        self._config = config

        self.configure()

        self._clients = {
            "agents": dialogflow.AgentsClient(),
            "intents": dialogflow.IntentsClient(),
            "sessions": dialogflow.SessionsClient(),
            "contexts": dialogflow.ContextsClient(),
        }

        self._intents = {"name": {}, "display_name": {}}

        self._session_id = ""
        self._session_path = ""

    @property
    def project_id(self):
        return self._config.get("project_id", "")

    @property
    def credential(self):
        return self._config.get("credential", "")

    @property
    def agents_client(self):
        return self._clients.get("agents", None)

    @property
    def intents_client(self):
        return self._clients.get("intents", None)

    @property
    def sessions_client(self):
        return self._clients.get("sessions", None)

    @property
    def contexts_client(self):
        return self._clients.get("contexts", None)

    @property
    def intents(self):
        return self._intents

    def create_session(self, contexts=[]):
        self._session_id = uuid4().hex
        self._session_path = self.sessions_client.session_path(
            self.project_id, self._session_id
        )
        self.create_contexts_by_name(self._session_path, contexts)

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

    def get_intents(self):

        parent = self.agents_client.agent_path(self.project_id)

        intents = self.intents_client.list_intents(
            request={"parent": parent, "intent_view": 1}
        )

        for intent in intents:
            self._intents["name"][intent.name] = Intent(intent)
            self._intents["display_name"][intent.display_name] = self._intents["name"][
                intent.name
            ]

        return intents

    def update_intent(self, intent):
        intent.root_followup_intent_name = ""
        intent.followup_intent_info = ""

        request = {"intent": intent, "intent_view": 1}

        return self.intents_client.update_intent(request)

    def batch_update_intents(self, intents):

        for intent in intents:
            intent.root_followup_intent_name = ""
            intent.followup_intent_info = ""

        parent = self.agents_client.agent_path(self.project_id)
        request = {
            "parent": parent,
            "intent_batch_inline": {"intents": intents},
            "intent_view": 1,
        }

        operation = self.intents_client.batch_update_intents(request=request)

        return operation.result()

    def detect_intent(self, query, context_names):
        parsed_session_path = self.sessions_client.parse_session_path(
            self._session_path
        )
        contexts = []
        for context_name in context_names:
            contexts.append(
                {
                    "name": self.contexts_client.context_path(
                        project=parsed_session_path["project"],
                        session=parsed_session_path["session"],
                        context=context_name,
                    ),
                    "lifespan_count": 1,
                }
            )

        query_params = {"contexts": contexts}
        query_input = {"text": {"text": query, "language_code": "en"}}

        request = {
            "session": self._session_path,
            "query_params": query_params,
            "query_input": query_input,
        }

        return self.sessions_client.detect_intent(request=request)

    def list_contexts(self):
        request = {
            "parent": self._session_path,
        }

        return self.contexts_client.list_contexts(request=request)

    def create_context(self, parent, context):
        request = {"parent": parent, "context": {"name": context}}

        return self.contexts_client.create_context(request=request)

    def create_contexts(self, parent, contexts):
        for context in contexts:
            try:
                request = {"parent": parent, "context": {"name": context}}

                response = self.contexts_client.create_context(request=request)
            except Exception as e:
                pass

    def create_context_by_name(self, session_path, name):
        parsed_session_path = self.sessions_client.parse_session_path(session_path)
        context = self.contexts_client.context_path(
            project=parsed_session_path["project"],
            session=parsed_session_path["session"],
            context=name,
        )
        return self.create_context(session_path, context)

    def create_contexts_by_name(self, session_path, names):
        for name in names:
            response = self.create_context_by_name(session_path, name)

    def get_context(self, name):
        request = {"name": name}

        return self.contexts_client.get_context(request=request)

    def get_contexts(self, names):
        contexts = []
        for name in names:
            try:
                request = {"name": name}

                contexts.append(self.contexts_client.get_context(request=request))
            except Exception as e:
                pass
        return contexts

    def display_intents(self):

        for key in self._intents["name"]:
            intent = self._intents["name"][key]._intent_obj

            print("=" * 80)
            print(f"Intent name: {intent.name}")
            print(f"Intent display_name: {intent.display_name}")
            print(f"Root followup intent: {intent.root_followup_intent_name}")
            print(f"Parent followup intent: {intent.parent_followup_intent_name}\n")

            print("Input contexts:")
            for input_context_name in intent.input_context_names:
                print(f"\tName: {input_context_name}")

            print("Output contexts:")
            for output_context in intent.output_contexts:
                print(f"\tName: {output_context.name}")

            if intent.action:
                print(f"Action: {intent.action}\n")

            if len(intent.parameters) > 0:
                print("Parameters:")
                for param in intent.parameters:
                    print(f"\tname: {param.name}")
                    print(f"\tdisplay_name: {param.display_name}")
                    print(
                        f"\tentity_type_display_name: {param.entity_type_display_name}"
                    )
                    print(f"\tvalue: {param.value}")

            if len(intent.training_phrases) > 0:
                print("Training Phrases:")
                for phrase in intent.training_phrases:
                    full_phrase = ""
                    for part in phrase.parts:
                        full_phrase += part.text
                        # print(f"\t{part}")
                    print(f"\t{full_phrase}")

            print("=" * 80)
            print()
            print()

    def create_tree(self):
        for key in self.intents["name"]:
            intent = self.intents["name"][key]
            if intent._intent_obj.parent_followup_intent_name:
                intent._parent = self.intents["name"][
                    intent._intent_obj.parent_followup_intent_name
                ]
                intent._parent._children.append(intent)
                
    def train_agent(self):
        from google.cloud import dialogflow
        print("train_agent_start")
        agents_client = dialogflow.AgentsClient()
        parent = dialogflow.AgentsClient.common_project_path(self.project_id)
        response = agents_client.train_agent(
            request={"parent": parent}
        )
        print(response.done())


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

    df = Dialogflow(config)
    df.get_intents()
    # df.display_intents()

    query = "sounds great"

    intent_name = "system-generic-topic-transition-yes"
    intent = df._intents["display_name"][intent_name]
    contexts = intent.input_context_names

    df.create_session(contexts)

    print()
    print("*" * 80)
    print(f"Session ID: {df._session_id}")
    print("*" * 80)

    # print("*" * 80)
    # print("LIST CONTEXTS")
    # print("*" * 80)
    # for response in df.list_contexts():
    #     print(response)

    print()

    print("*" * 80)
    print("DETECT INTENT")
    print("*" * 80)

    response = df.detect_intent(query, contexts)
    print(response)
