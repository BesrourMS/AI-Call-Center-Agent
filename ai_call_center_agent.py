import openai
import json
import speech_recognition as sr
import io
import wave
import os
import pygame
import time
import datetime
import logging
from dotenv import load_dotenv
import asyncio
import aiohttp
from speech_recognition import UnknownValueError, RequestError
import pvporcupine
import azure.cognitiveservices.speech as speechsdk
import pyaudio
import struct

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
        pygame.mixer.init()
        self.load_config()
        self.session = None
        self.porcupine = None
        self.init_porcupine()
        self.speech_config = speechsdk.SpeechConfig(
            subscription=os.getenv('AZURE_SPEECH_KEY'),
            region=os.getenv('AZURE_SPEECH_REGION')
        )
        self.speech_config.speech_synthesis_voice_name = "en-US-JennyNeural"

    def load_config(self):
        """Load configuration settings from config.json."""
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
        except json.JSONDecodeError:
            logger.error("Error parsing config file. Using default settings.")

    def init_porcupine(self):
        """Initialize Porcupine for wake word detection."""
        try:
            access_key = os.getenv('PORCUPINE_ACCESS_KEY')
            if not access_key:
                raise ValueError("Porcupine access key not found in environment variables")
            self.porcupine = pvporcupine.create(
                access_key=access_key,
                keywords=["hey agent"]
            )
        except Exception as e:
            logger.error(f"Failed to initialize Porcupine: {e}")
            self.porcupine = None

    async def get_response(self, user_input):
        """Generate a response using OpenAI's chat completion API."""
        self.conversation_history.append({"role": "user", "content": user_input})
        messages = [{"role": "system", "content": "You are a helpful call center assistant."}]
        messages.extend(self.conversation_history[-5:])  # Keep last 5 messages for context

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
                response.raise_for_status()
                result = await response.json()
                ai_response = result['choices'][0]['message']['content']
                self.conversation_history.append({"role": "assistant", "content": ai_response})
                return ai_response
        except aiohttp.ClientError as e:
            logger.error(f"Network error in getting AI response: {e}")
            return "I'm sorry, I'm having trouble connecting. Please try again later."
        except Exception as e:
            logger.error(f"Unexpected error in getting AI response: {e}")
            return "I'm experiencing an issue. Please try again."

    async def handle_query(self, query):
        """Handle user queries based on keywords."""
        query_lower = query.lower()
        if "order status" in query_lower:
            return await self.check_order_status(query)
        elif "return policy" in query_lower:
            return self.explain_return_policy()
        elif "end call" in query_lower:
            return self.end_call()
        else:
            return await self.get_response(query)

    async def listen_for_wake_word(self):
        """Listen for the wake word using Porcupine or fallback method."""
        if not self.porcupine:
            logger.warning("Porcupine not initialized. Using default method.")
            return await self.default_listen_for_wake_word()

        pa = pyaudio.PyAudio()
        audio_stream = pa.open(
            rate=self.porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=self.porcupine.frame_length
        )

        try:
            while True:
                pcm = audio_stream.read(self.porcupine.frame_length)
                pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)
                keyword_index = self.porcupine.process(pcm)
                if keyword_index >= 0:
                    logger.info("Wake word detected!")
                    return True
        except Exception as e:
            logger.error(f"Error in Porcupine wake word detection: {e}")
            return False
        finally:
            audio_stream.close()
            pa.terminate()

    async def check_order_status(self, query):
        """Simulate checking order status."""
        await asyncio.sleep(1)  # Simulate network delay
        return "Your order #12345 is in transit and expected to arrive on Friday."

    def explain_return_policy(self):
        """Provide return policy information."""
        return "Our return policy allows returns within 30 days for a full refund if the item is in original condition."

    def end_call(self):
        """Offer further assistance before ending the call."""
        return "Thank you for calling. Anything else I can assist with?"

    async def transcribe_audio(self, audio_file):
        """Transcribe audio using OpenAI's Whisper API."""
        try:
            data = aiohttp.FormData()
            data.add_field('file', audio_file, filename='audio.wav', content_type='audio/wav')
            data.add_field('model', 'whisper-1')
            async with self.session.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {openai.api_key}"},
                data=data
            ) as response:
                response.raise_for_status()
                result = await response.json()
                return result.get("text", "")
        except Exception as e:
            logger.error(f"Error in transcribing audio: {e}")
            return None

    async def text_to_speech(self, text):
        """Convert text to speech using Azure Speech SDK."""
        try:
            speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=self.speech_config)
            result = await asyncio.to_thread(speech_synthesizer.speak_text, text)
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                audio_data = result.audio_data
                p = pyaudio.PyAudio()
                stream = p.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=24000,
                    output=True
                )
                await asyncio.to_thread(stream.write, audio_data)
                stream.stop_stream()
                stream.close()
                p.terminate()
            else:
                logger.error(f"Speech synthesis failed: {result.reason}")
        except Exception as e:
            logger.error(f"Error in text-to-speech: {e}")

    async def default_listen_for_wake_word(self):
        """Fallback method to listen for wake word using speech_recognition."""
        logger.info(f"Listening for wake word: '{self.wake_word}'")
        while True:
            try:
                with sr.Microphone() as source:
                    await asyncio.to_thread(self.recognizer.adjust_for_ambient_noise, source)
                    audio = await asyncio.to_thread(self.recognizer.listen, source, timeout=5)
                    text = await asyncio.to_thread(self.recognizer.recognize_google, audio)
                    if self.wake_word in text.lower():
                        logger.info("Wake word detected!")
                        return True
            except sr.WaitTimeoutError:
                pass
            except sr.UnknownValueError:
                pass
            except sr.RequestError as e:
                logger.error(f"Google Speech Recognition error: {e}")
            except Exception as e:
                logger.error(f"Error in wake word detection: {e}")
            await asyncio.sleep(0.1)

    async def listen_and_respond(self):
        """Listen for wake word, greet user, and respond to queries."""
        if not await self.listen_for_wake_word():
            return

        # Reset conversation history for new call
        self.conversation_history = []
        self.call_start_time = time.time()

        # Greet the user after wake word detection
        logger.info("Wake word detected. Greeting the user...")
        greeting = "Hello, how can I assist you today?"
        await self.text_to_speech(greeting)

        logger.info("Listening for query...")
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source)
                audio = await asyncio.to_thread(self.recognizer.listen, source, timeout=10)
            with io.BytesIO() as wav_file:
                wav_writer = wave.open(wav_file, "wb")
                wav_writer.setnchannels(1)
                wav_writer.setsampwidth(2)
                wav_writer.setframerate(16000)
                wav_writer.writeframes(audio.get_wav_data(convert_rate=16000, convert_width=2))
                wav_writer.close()
                wav_file.seek(0)
                transcription = await self.transcribe_audio(wav_file)
                if transcription:
                    logger.info(f"User said: {transcription}")
                    response = await self.handle_query(transcription)
                    logger.info(f"Agent: {response}")
                    await self.text_to_speech(response)
                else:
                    logger.warning("Failed to transcribe audio")
                    await self.text_to_speech("Sorry, I couldn't understand that. Please try again.")
        except sr.WaitTimeoutError:
            logger.warning("Listening timed out.")
            await self.text_to_speech("I didn't hear anything. Please try again.")
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            await self.text_to_speech("Sorry, an error occurred. Please try again later.")
        finally:
            self.call_duration += time.time() - self.call_start_time

    async def run(self):
        """Run the agent in a loop."""
        logger.info("AI Call Center Agent is running. Say the wake word to start.")
        async with aiohttp.ClientSession() as session:
            self.session = session
            while True:
                await self.listen_and_respond()

    def generate_report(self):
        """Generate a report of agent activity."""
        total_messages = len(self.conversation_history)
        user_messages = sum(1 for msg in self.conversation_history if msg["role"] == "user")
        ai_messages = sum(1 for msg in self.conversation_history if msg["role"] == "assistant")
        report = f"""
        Call Center Agent Report
        ------------------------
        Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        Total Call Duration: {self.call_duration:.2f} seconds
        Total Messages: {total_messages}
        User Messages: {user_messages}
        AI Responses: {ai_messages}
        """
        return report

    def __del__(self):
        """Cleanup Porcupine instance."""
        if self.porcupine:
            self.porcupine.delete()

async def main():
    """Main function to run the agent."""
    agent = AICallCenterAgent()
    try:
        await agent.run()
    except KeyboardInterrupt:
        logger.info("\nGenerating report...")
        report = agent.generate_report()
        print(report)
        logger.info("AI Call Center Agent shutting down. Goodbye!")

if __name__ == "__main__":
    asyncio.run(main())