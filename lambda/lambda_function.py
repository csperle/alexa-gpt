import logging
import ask_sdk_core.utils as ask_utils
import openai
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response

# Set your OpenAI API key
openai.api_key = "PUT YOUR OPEN API KEY HERE"

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool

        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Hallo, hier ist Joshua"
        
        # Reset chat history in session
        session_attr = handler_input.attributes_manager.session_attributes
        session_attr["chat_history"] = []
        
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class GptQueryIntentHandler(AbstractRequestHandler):
    """Handler for Gpt Query Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("GptQueryIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        query = handler_input.request_envelope.request.intent.slots["query"].value
        
        # Get chat history from session
        session_attr = handler_input.attributes_manager.session_attributes
        chat_history = session_attr["chat_history"]
        
        response = generate_gpt_response(chat_history, query)

        # Add to chat history
        session_attr["chat_history"].append((query, response))
        
        return (
                handler_input.response_builder
                    .speak(response)
                    .ask("Hast Du noch eine Frage?")
                    .response
            )

class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Generic error handling to capture any syntax or routing errors."""
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(exception, exc_info=True)

        speak_output = "Das habe ich nicht verstanden. Bitte versuche es erneut."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or
                ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Okay, Joshua Ende."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

def generate_gpt_response(chat_history, new_question):
    try:
        messages = [{"role": "system", "content": "Du bist Joshua, ein freundlicher, stets hilfreicher Assistent."}]
        
        for question, answer in chat_history[-10:]:
            messages.append({"role": "user", "content": question})
            messages.append({"role": "assistant", "content": answer})
        
        messages.append({"role": "user", "content": new_question + "\nAntworte als Joshua und fasse Dich kurz und knapp."})
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=100,
            n=1,
            stop=None,
            temperature=0.5
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f"Error generating response: {str(e)}"

sb = SkillBuilder()

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(GptQueryIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()
