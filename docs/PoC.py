import openai
import speech_recognition as sr
import io
import wave
import os
from gtts import gTTS
import pygame
import asyncio
import aiohttp
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Pygame mixer for audio playback
pygame.mixer.init()

# Set up OpenAI API key
openai.api_key = os.getenv('OPENAI_API_KEY')

class AICallCenterAgent:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.wake_word = "hey agent"
        self.conversation_history = []
        self.model = 'gpt-3.5-turbo'
        self.language = 'en'
        self.max_tokens = 150
        self.temperature = 0.7
        self.session = None

    async def get_response(self, user_input):
        """ Get response from OpenAI API asynchronously. """
        self.conversation_history.append({"role": "user", "content": user_input})
        messages = [
            {"role": "system", "content": "You are a helpful AI call center agent."},
        ] + self.conversation_history

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

    def text_to_speech(self, text):
        """ Convert text to speech and play it. """
        tts = gTTS(text=text, lang=self.language)
        with io.BytesIO() as audio_file:
            tts.write_to_fp(audio_file)
            audio_file.seek(0)
            pygame.mixer.music.load(audio_file)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)

    async def listen_for_wake_word(self):
        """ Continuously listen for the wake word. """
        logger.info(f"Listening for wake word: '{self.wake_word}'")
        while True:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source)
                audio = self.recognizer.listen(source, timeout=5)
                try:
                    text = self.recognizer.recognize_google(audio).lower()
                    if self.wake_word in text:
                        logger.info("Wake word detected!")
                        return True
                except sr.UnknownValueError:
                    logger.warning("Could not understand the audio.")
                except sr.RequestError as e:
                    logger.error(f"Could not request results; {e}")

            await asyncio.sleep(0.1)

    async def listen_and_respond(self):
        """ Listen for a query and respond accordingly. """
        if not await self.listen_for_wake_word():
            return

        logger.info("Wake word detected. Listening for query...")

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
            transcription = self.recognizer.recognize_google(audio)
            if transcription:
                logger.info(f"User said: {transcription}")
                response = await self.get_response(transcription)
                logger.info(f"Agent: {response}")
                self.text_to_speech(response)
            else:
                logger.warning("Failed to transcribe audio")
                self.text_to_speech("Sorry, I couldn't understand that. Could you please try again?")

    async def run(self):
        """ Start the agent and listen for the wake word in a loop. """
        async with aiohttp.ClientSession() as session:
            self.session = session
            while True:
                await self.listen_and_respond()

async def main():
    """ Main function to run the agent asynchronously. """
    agent = AICallCenterAgent()
    try:
        await agent.run()
    except KeyboardInterrupt:
        logger.info("AI Call Center Agent shutting down. Goodbye!")

if __name__ == "__main__":
    asyncio.run(main())
