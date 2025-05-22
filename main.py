from deepgram import DeepgramClient, LiveOptions, LiveTranscriptionEvents, Microphone
from dotenv import load_dotenv

load_dotenv()

# We will collect the is_final=true messages here so we can use them when the person finishes speaking
is_finals = []


def main():
    try:
        # Create Deepgram client
        deepgram = DeepgramClient()
        dg_connection = deepgram.listen.live.v("1")

        # Event handlers
        def on_open(self, open, **kwargs):
            print("Connection Open")

        def on_message(self, result, **kwargs):
            global is_finals
            sentence = result.channel.alternatives[0].transcript
            if len(sentence) == 0:
                return
            if result.is_final:
                is_finals.append(sentence)
                if result.speech_final:
                    utterance = " ".join(is_finals)
                    print(f"Speech Final: {utterance}")
                    is_finals = []
                else:
                    print(f"Is Final: {sentence}")
            else:
                print(f"Interim Results: {sentence}")

        def on_close(self, close, **kwargs):
            print("Connection Closed")

        def on_error(self, error, **kwargs):
            print(f"Handled Error: {error}")

        # Set up event handlers
        dg_connection.on(LiveTranscriptionEvents.Open, on_open)
        dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
        dg_connection.on(LiveTranscriptionEvents.Close, on_close)
        dg_connection.on(LiveTranscriptionEvents.Error, on_error)

        # Configure transcription options
        options = LiveOptions(
            model="nova-3",
            language="en-US",
            smart_format=True,
            encoding="linear16",
            channels=1,
            sample_rate=16000,
            interim_results=True,
            utterance_end_ms="1000",
            vad_events=True,
            endpointing=300,
        )

        print("\n\nPress Enter to stop recording...\n\n")

        # Start the connection
        if dg_connection.start(options) is False:
            print("Failed to connect to Deepgram")
            return

        # Create and start microphone
        microphone = Microphone(dg_connection.send)
        microphone.start()

        # Wait for user input to stop
        input("")

        # Clean up
        microphone.finish()
        dg_connection.finish()

        print("Finished")

    except Exception as e:
        print(f"Could not open socket: {e}")
        return


if __name__ == "__main__":
    main()
