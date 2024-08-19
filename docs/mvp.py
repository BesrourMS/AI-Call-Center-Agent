import openai
import json
import speech_recognition as sr
import io
import wave
import os
from gtts import gTTS
import pygame
import time
import datetime
import logging
from dotenv import load_dotenv
from threading import Thread
from queue import Queue
import asyncio
import aiohttp

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set up your OpenAI API key
openai.api_key = os.getenv('OPENAI_API_KEY')

class AICallCenterAgent:
    def __init__(self):
        self.conversation_history = []
        self.recognizer = sr.Recognizer()
        self.wake_word = "hey agent"
        self.call_duration = 0
        self.call_start_time = None
        self.audio_queue = Queue()
        pygame.mixer.init()
        self.load_config()
        self.session = None

    def load_config(self):
        """ Load configuration settings. """
        config_path = 'config.json'
        if not os.path.isfile(config_path):
            logger.warning("Config file not found. Using default settings.")
            return

        try:
            with open(config_path, 'r') as config_file:
                config = json.load(config_file)
                self.wake_word = config.get('wake_word', self.wake_word)
                self.model = config.get('model', 'gpt-3.5-turbo')
                self.language = config.get('language', 'en')
                self.max_tokens = config.get('max_tokens', 150)
                self.temperature = config.get('temperature', 0.7)
                self.knowledge_base_url = config.get('knowledge_base_url')
        except json.JSONDecodeError:
            logger.error("Error parsing config file. Using default settings.")

    async def fetch_relevant_info(self, query):
        """Fetch relevant information from an external knowledge base or API."""
        try:
            async with self.session.get(
                self.knowledge_base_url,
                params={"query": query},
                headers={"Authorization": f"Bearer {os.getenv('KNOWLEDGE_BASE_API_KEY')}"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get('data')
                else:
                    logger.warning(f"Failed to retrieve information: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching relevant information: {e}")
            return None

    async def get_response(self, user_input):
        """ Get response from OpenAI API asynchronously, with RAG integration. """
        # First, fetch relevant data from the knowledge base
        relevant_info = await self.fetch_relevant_info(user_input)
        if relevant_info:
            system_message = f"You are a helpful AI call center agent. Use the following information to assist the customer: {relevant_info}"
        else:
            system_message = "You are a helpful AI call center agent. Provide concise and accurate responses to customer queries."

        self.conversation_history.append({"role": "user", "content": user_input})
        messages = [
            {"role": "system", "content": system_message},
        ] + self.conversation_history

        try:
            async with self.session.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {openai.api_key}"},
                json={
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": self.max_tokens,
                    "temperature": self.temperature,
                }
            ) as response:
                result = await response.json()
                ai_response = result['choices'][0]['message']['content']
                self.conversation_history.append({"role": "assistant", "content": ai_response})
                return ai_response
        except Exception as e:
            logger.error(f"Error in getting AI response: {e}")
            return "I'm sorry, I'm having trouble processing your request. Could you please try again?"

    async def handle_query(self, query):
        """ Handle user queries based on keywords, integrating RAG. """
        if "order status" in query.lower():
            return await self.check_order_status(query)
        elif "return policy" in query.lower():
            return self.explain_return_policy()
        elif "end call" in query.lower():
            return self.end_call()
        else:
            return await self.get_response(query)

    async def check_order_status(self, query):
        """ Check order status asynchronously, possibly using RAG. """
        # Simulating an API call to an order management system
        await asyncio.sleep(1)  # Simulating network delay
        return "I've checked your order status. Your order #12345 is currently in transit and expected to arrive on Friday."

    def explain_return_policy(self):
        """ Provide return policy information. """
        return "Our return policy allows you to return any item within 30 days of purchase for a full refund, provided the item is in its original condition."

    def end_call(self):
        """ End the call and offer further assistance. """
        return "Thank you for calling. Is there anything else I can help you with before we end the call?"

    async def transcribe_audio(self, audio_file):
        """ Transcribe audio file using OpenAI's Whisper model asynchronously. """
        try:
            async with self.session.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {openai.api_key}"},
                data={"model": "whisper-1"},
                files={"file": audio_file}
            ) as response:
                result = await response.json()
                return result.get("text")
        except Exception as e:
            logger.error(f"Error in transcribing audio: {e}")
            return None

    def text_to_speech(self, text):
        """ Convert text to speech and play it. """
        try:
            tts = gTTS(text=text, lang=self.language)
            with io.BytesIO() as audio_file:
                tts.write_to_fp(audio_file)
                audio_file.seek(0)
                pygame.mixer.music.load(audio_file)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
        except Exception as e:
            logger.error(f"Error in text-to-speech: {e}")

    async def listen_for_wake_word(self):
        """ Continuously listen for the wake word. """
        logger.info(f"Listening for wake word: '{self.wake_word}'")
        while True:
            try:
                with sr.Microphone() as source:
                    self.recognizer.adjust_for_ambient_noise(source)
                    audio = self.recognizer.listen(source, timeout=5)
                    text = self.recognizer.recognize_google(audio).lower()
                    if self.wake_word in text:
                        logger.info("Wake word detected!")
                        return True
            except sr.WaitTimeoutError:
                pass
            except Exception as e:
                logger.error(f"Error in wake word detection: {e}")
            await asyncio.sleep(0.1)  # Prevent blocking the event loop

    async def listen_and_respond(self):
        """ Listen for a query and respond accordingly. """
        if not await self.listen_for_wake_word():
            return

        self.call_start_time = time.time()
        logger.info("Wake word detected. Listening for query...")
        
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source)
                audio = self.recognizer.listen(source, timeout=10)

            with io.BytesIO() as wav_file:
                wav_writer = wave.open(wav_file, "wb")
                wav_writer.setnchannels(1)
                wav_writer.setsampwidth(2)
                wav_writer.setframerate(16000)
                wav_writer.writeframes(audio.get_wav_data())
                wav_writer.close()

                wav_file.seek(0)
                transcription = await self.transcribe_audio(wav_file)
                if transcription:
                    logger.info(f"User said: {transcription}")
                    response = await self.handle_query(transcription)
                    logger.info(f"Agent: {response}")
                    self.text_to_speech(response)
                else:
                    logger.warning("Failed to transcribe audio")
                    self.text_to_speech("Sorry, I couldn't understand that. Could you please try again?")

        except sr.WaitTimeoutError:
            logger.warning("Listening timed out. Please try again.")
        except Exception as e:
            logger.error(f"An error occurred: {e}")
        finally:
            self.call_duration += time.time() - self.call_start_time

    async def run(self):
        """ Start the agent and listen for the wake word in a loop. """
        logger.info("AI Call Center Agent is running. Say the wake word to start.")
        async with aiohttp.ClientSession() as session:
            self.session = session
            while True:
                await self.listen_and_respond()

    def generate_report(self):
        """ Generate a report summarizing the agent's activity. """
        total_messages = len(self.conversation_history)
        user_messages = sum(1 for msg in self.conversation_history if msg["role"] == "user")
        ai_messages = sum(1 for msg in self.conversation_history if msg["role"] == "assistant")
        
        report = f"""
        Call Summary:
        - Total Messages Exchanged: {total_messages}
        - User Messages: {user_messages}
        - AI Messages: {ai_messages}
        - Total Call Duration: {datetime.timedelta(seconds=self.call_duration)}

        Conversation Log:
        """
        for msg in self.conversation_history:
            report += f"{msg['role'].capitalize()}: {msg['content']}\n"

        return report

# Initialize and run the AI Call Center Agent
agent = AICallCenterAgent()
asyncio.run(agent.run())