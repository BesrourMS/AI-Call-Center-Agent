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

# Set up your OpenAI API key
openai.api_key = 'your-api-key-here'

class AICallCenterAgent:
    def __init__(self):
        self.conversation_history = []
        self.recognizer = sr.Recognizer()
        self.wake_word = "hey agent"
        self.call_duration = 0
        self.call_start_time = None
        pygame.mixer.init()

    def get_response(self, user_input):
        self.conversation_history.append({"role": "user", "content": user_input})
        messages = [
            {"role": "system", "content": "You are a helpful AI call center agent. Provide concise and accurate responses to customer queries."},
        ] + self.conversation_history

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages
            )
            ai_response = response.choices[0].message['content']
            self.conversation_history.append({"role": "assistant", "content": ai_response})
            return ai_response
        except Exception as e:
            print(f"Error in getting AI response: {e}")
            return "I'm sorry, I'm having trouble processing your request. Could you please try again?"

    def handle_query(self, query):
        if "order status" in query.lower():
            return self.check_order_status(query)
        elif "return policy" in query.lower():
            return self.explain_return_policy()
        else:
            return self.get_response(query)

    def check_order_status(self, query):
        # Placeholder for order status check
        return "I've checked your order status. Your order #12345 is currently in transit and expected to arrive on Friday."

    def explain_return_policy(self):
        return "Our return policy allows you to return any item within 30 days of purchase for a full refund, provided the item is in its original condition."

    def transcribe_audio(self, audio_file):
        try:
            with open(audio_file, "rb") as file:
                transcript = openai.Audio.transcribe("whisper-1", file)
            return transcript["text"]
        except Exception as e:
            print(f"Error in transcribing audio: {e}")
            return None

    def text_to_speech(self, text):
        try:
            tts = gTTS(text=text, lang='en')
            tts.save("response.mp3")
            pygame.mixer.music.load("response.mp3")
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            os.remove("response.mp3")
        except Exception as e:
            print(f"Error in text-to-speech: {e}")

    def listen_for_wake_word(self):
        print(f"Listening for wake word: '{self.wake_word}'")
        while True:
            try:
                with sr.Microphone() as source:
                    self.recognizer.adjust_for_ambient_noise(source)
                    audio = self.recognizer.listen(source, timeout=5)
                    text = self.recognizer.recognize_google(audio).lower()
                    if self.wake_word in text:
                        print("Wake word detected!")
                        return True
            except sr.WaitTimeoutError:
                pass
            except Exception as e:
                print(f"Error in wake word detection: {e}")

    def listen_and_respond(self):
        if not self.listen_for_wake_word():
            return

        self.call_start_time = time.time()
        print("Wake word detected. Listening for query...")
        
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
                with open("temp_audio.wav", "wb") as f:
                    f.write(wav_file.read())

            transcription = self.transcribe_audio("temp_audio.wav")
            if transcription:
                print(f"You said: {transcription}")
                response = self.handle_query(transcription)
                print(f"Agent: {response}")
                self.text_to_speech(response)
            else:
                print("Sorry, I couldn't understand that. Could you please try again?")
                self.text_to_speech("Sorry, I couldn't understand that. Could you please try again?")

        except sr.WaitTimeoutError:
            print("Listening timed out. Please try again.")
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            if os.path.exists("temp_audio.wav"):
                os.remove("temp_audio.wav")
            self.call_duration += time.time() - self.call_start_time

    def run(self):
        print("AI Call Center Agent is running. Say the wake word to start.")
        while True:
            self.listen_and_respond()

    def generate_report(self):
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

# Example usage
agent = AICallCenterAgent()

try:
    agent.run()
except KeyboardInterrupt:
    print("\nGenerating report...")
    report = agent.generate_report()
    print(report)
    print("AI Call Center Agent shutting down. Goodbye!")
