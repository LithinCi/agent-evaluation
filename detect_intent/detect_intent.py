import sys
import os
from time import sleep

class DetectIntentCli():

    def __init__(self) -> None:        

        self.agent_name = "Haru-SmallTalk-All-Topics-Lithin-Evaluation-2"
        self.project_id = 'haru-smalltalk-all-topics-hywn'  # test agent
        self.key_file = os.path.dirname(
            os.path.abspath(os.path.dirname(__file__))) + '/service_files/haru-smalltalk-all-topics-hywn-198188184bf2.json'
        self.test_intent_display_name = "Default Fallback Intent"
        

    def detect_intent(self,query,intent_) : 

        sys.path.append(f"{os.path.dirname(__file__)}/../modules/dialogflow-api-lite/src")
        from dialogflow import Dialogflow
        config = {"project_id": self.project_id,
                    "credential": self.key_file}
        df = Dialogflow(config)
        # df.train_agent()
        df.get_intents()
        intent = df._intents["display_name"][intent_]
        contexts = intent.input_context_names
        print("input intent: ",intent_)
        print("contexts: ",contexts)
        
        df.create_session(contexts)
        sleep(1)
        response = df.detect_intent(query,contexts)
        print("response : ",response)
        _response = response.query_result.intent.display_name
        _conf= response.query_result.intent_detection_confidence
        
        print("query : ",query)
        print("response : ",response.query_result.fulfillment_text)
        print("parameters : ","{}".format(response.query_result.parameters))
        print("Intent detected : ",_response)
        print("Intent confidence : ",_conf)
        print("\n")
        

if __name__ == "__main__":

    detect_intent = DetectIntentCli()
    query = "My name is tony"
    intent_names  = "says-name"
    # intent_no  = "topic-books-hear-poem-no"
    detect_intent.detect_intent(query,intent_names)