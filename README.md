# AI Call Center Agent

This project implements an AI-powered call center agent using OpenAI's GPT-3.5 and Whisper models. The agent can handle both text and voice inputs, provide responses using text-to-speech, and generate basic analytics reports.

## Features

- Asynchronous operation for improved performance
- Voice input processing using OpenAI's Whisper model
- Text-based conversation handling using GPT-3.5
- Wake word detection for initiating conversations
- Text-to-speech functionality for spoken responses
- Basic analytics and reporting
- Handling of common scenarios like order status checks and return policy inquiries
- Configurable AI parameters

## Prerequisites

Before you begin, ensure you have met the following requirements:

- Python 3.7 or higher
- An OpenAI API key

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/ai-call-center-agent.git
   cd ai-call-center-agent
   ```

2. Install the required packages:
   ```
   pip install openai speech_recognition pyaudio wave gtts pygame python-dotenv aiohttp
   ```

3. Set up your OpenAI API key:
   - Create a `.env` file in the project root
   - Add your OpenAI API key to the `.env` file:
     ```
     OPENAI_API_KEY=your-api-key-here
     ```

## Configuration

Create a `config.json` file in the project root with the following structure:

```json
{
  "wake_word": "hey agent",
  "model": "gpt-3.5-turbo",
  "language": "en",
  "max_tokens": 150,
  "temperature": 0.7
}
```

You can modify these parameters to customize the agent's behavior:

- `wake_word`: The phrase to activate the agent (default: "hey agent")
- `model`: The GPT model to use for text processing (default: "gpt-3.5-turbo")
- `language`: The language for text-to-speech output (default: "en" for English)
- `max_tokens`: Maximum number of tokens in the AI's response (default: 150)
- `temperature`: Controls the randomness of the AI's responses (default: 0.7)

## Usage

To run the AI Call Center Agent:

1. Navigate to the project directory
2. Run the following command:
   ```
   python main.py
   ```
3. The agent will start and listen for the wake word "hey agent"
4. Once the wake word is detected, speak your query
5. The agent will process your query and respond verbally

To stop the agent, use the keyboard interrupt (Ctrl+C). The agent will generate a basic report before shutting down.

## Example Interactions

Here are some example interactions you can try with the AI Call Center Agent:

1. Checking order status:
   - You: "Hey agent, what's the status of my order?"
   - Agent: *Provides information about a simulated order*

2. Inquiring about return policy:
   - You: "Hey agent, can you explain the return policy?"
   - Agent: *Explains the return policy*

3. General inquiries:
   - You: "Hey agent, how can I track my shipment?"
   - Agent: *Provides information on shipment tracking*

## Troubleshooting

If you encounter any issues:

1. Ensure all dependencies are correctly installed
2. Check that your OpenAI API key is correctly set in the `.env` file
3. Verify that your microphone is working and properly configured
4. Check the console output for any error messages or logs

## Contributing

Contributions to this project are welcome. Please fork the repository and submit a pull request with your changes.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This is a demonstration project and is not intended for production use without further development and security considerations.

## Contact

If you have any questions or feedback, please open an issue in this repository.
