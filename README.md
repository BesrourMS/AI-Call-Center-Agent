# AI Call Center Agent

This project implements an AI-powered call center agent using OpenAI's GPT-3.5 and Whisper models. The agent can handle both text and voice inputs, provide responses using text-to-speech, and generate basic analytics reports.

## Features

- Voice input processing using OpenAI's Whisper model
- Text-based conversation handling using GPT-3.5
- Wake word detection for initiating conversations
- Text-to-speech functionality for spoken responses
- Basic analytics and reporting
- Handling of common scenarios like order status checks and return policy inquiries

## Prerequisites

Before you begin, ensure you have met the following requirements:

- Python 3.7 or higher
- An OpenAI API key

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/besrourms/ai-call-center-agent.git
   cd ai-call-center-agent
   ```

2. Install the required packages:
   ```
   pip install openai speech_recognition pyaudio wave gtts pygame
   ```

3. Set up your OpenAI API key:
   - Open the `ai_call_center_agent.py` file
   - Replace `'your-api-key-here'` with your actual OpenAI API key

## Usage

To run the AI Call Center Agent:

1. Navigate to the project directory
2. Run the following command:
   ```
   python ai_call_center_agent.py
   ```
3. The agent will start and listen for the wake word "hey agent"
4. Once the wake word is detected, speak your query
5. The agent will process your query and respond verbally

To stop the agent, use the keyboard interrupt (Ctrl+C). The agent will generate a basic report before shutting down.

## Configuration

You can modify the following parameters in the `AICallCenterAgent` class:

- `wake_word`: Change the wake word (default is "hey agent")
- `model`: Change the GPT model used for text processing (default is "gpt-3.5-turbo")

## Contributing

Contributions to this project are welcome. Please fork the repository and submit a pull request with your changes.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This is a demonstration project and is not intended for production use without further development and security considerations.

## Contact

If you have any questions or feedback, please open an issue in this repository.
