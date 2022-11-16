from copy import copy
import sys
import os
import copy

paths = {}
paths["workspace"]      = f"{os.path.dirname(__file__)}/../.."
paths["db"]             = f"{paths['workspace']}/db"
paths["modules"]        = f"{paths['workspace']}/modules"
paths["dialogflow"]     = f"{paths['modules']}/dialogflow-api-lite"


sys.path.append(f"{paths['dialogflow']}/src/")

import re
import spacy
nlp = spacy.load('en_core_web_sm')

from dialogflow import Dialogflow


def add_patterns(config,intent_list,category):

    df = Dialogflow(config)
    records = {}
    df.get_intents()

    intents = df.intents["name"]
    new_intents = []

    patterns = config['patterns']

    param_added_flag = False
    parameters = [
        {
            "display_name": "any",
            "value": "$any",
            "entity_type_display_name": "@sys.any",
            "mandatory": False,
            "prompts": [],
            "is_list": False,
        },
        {
            "display_name": "any1",
            "value": "$any1",
            "entity_type_display_name": "@sys.any",
            "mandatory": False,
            "prompts": [],
            "is_list": False,
        },
    ]

    for key in patterns:
        records[key] = []
    # intent = None
    for intent__ in intents:
        intent = intents[intent__].intent_obj
        if intent.display_name in intent_list :
            if not intent.is_fallback:
                print(intent.display_name)
                for key in patterns:
                    pattern = f"-\s*{key}$"
                    # print(pattern)
                    result = re.search(pattern, intent.display_name)
                    if result:
                        new_intent = copy.deepcopy(intent)
                        new_intents.append(new_intent)
                        if not param_added_flag:
                            intent.parameters.extend(parameters)
                            param_added_flag = True
                        # print(patterns[key])
                        record = {
                            "original": intent,
                            "wrapped": word_wrapper(new_intent, patterns[key],category),
                        }
                        records[key].append(record)
    response = df.batch_update_intents(new_intents)
        
    # for key in intents:
    #     intent = intents[key].intent_obj

    #     if not intent.is_fallback:
    #         for key in patterns:
    #             pattern = f"-\s*{key}$"
    #             result = re.search(pattern, intent.display_name)
    #             if result:
    #                 new_intent = copy.deepcopy(intent)
    #                 new_intents.append(new_intent)
    #                 if not param_added_flag:
    #                     intent.parameters.extend(parameters)
    #                     param_added_flag = True
    #                 record = {
    #                     "original": intent,
    #                     "wrapped": word_wrapper(new_intent, patterns[key]),
    #                 }
    #                 records[key].append(record)

    # response = df.batch_update_intents(new_intents)

    return records

def word_wrapper(intent, word_list,category):
    for word in word_list:
        part = {"text": word, "entity_type": "", "alias": "", "user_defined": False}

        phrases = get_wrapped_phrases(part,category)
        intent.training_phrases.extend(phrases)

    return intent

def entity_wrapper(intent, entity_list):
    for entity in entity_list:
        part = {
            "text": "ENTITY",
            "entity_type": entity,
            "alias": "entity",
            "user_defined": True,
        }
        phrases = get_wrapped_phrases(part)
        intent.training_phrases.extend(phrases)

    return intent

def get_wrapped_phrases(part_main,category):
    part_any_pre = {
        "text": "ANY",
        "entity_type": "@sys.any",
        "alias": "any",
        "user_defined": True,
    }
    part_any_post = {
        "text": "ANY",
        "entity_type": "@sys.any",
        "alias": "any1",
        "user_defined": True,
    }
    part_space = {"text": " "}

    if category == "Common_patterns" : 
        return [
            {"type_": "EXAMPLE", "parts": [part_main], "times_added_count": 1},
        ]
    elif category == "Begin" : 
        return [{
                "type_": "EXAMPLE",
                "parts": [part_main, part_space, part_any_pre],
                "times_added_count": 1,
            },]
    elif category == "Mid" : 
        return [{
                "type_": "EXAMPLE",
                "parts": [
                    part_any_pre,
                    part_space,
                    part_main,
                    part_space,
                    part_any_post,
                ],
                "times_added_count": 1,
            },]
    elif category == "End" : 
        return [{
                "type_": "EXAMPLE",
                "parts": [part_any_pre, part_space, part_main],
                "times_added_count": 1,
            },]
    
        


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

    config = {
        "project_id": args.project_id,
        "credential": args.credential,
        "patterns": {
            "yes": [ "yes", "yeah", "yep", "yeap" ],
            "no": [ "no" ]
        }
    }

    add_patterns(config)