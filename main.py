import argparse
import os
import signal
import subprocess
import sys

from deepgram import DeepgramClient, LiveOptions, LiveTranscriptionEvents, Microphone
from dotenv import load_dotenv

load_dotenv()


def type(text: str):
    subprocess.run(["xdotool", "type", text])


def begin():
    lockfile = "/tmp/dictator.pid"

    # Write PID to lockfile
    with open(lockfile, "w") as f:
        f.write(str(os.getpid()))

    # Global variables for cleanup
    microphone = None
    dg_connection = None

    def cleanup_and_exit(signum=None, frame=None):
        print("\nStopping transcription...")
        if microphone:
            microphone.finish()
        if dg_connection:
            dg_connection.finish()
        # Remove lockfile
        if os.path.exists(lockfile):
            os.remove(lockfile)
        sys.exit(0)

    # Register signal handlers
    signal.signal(signal.SIGTERM, cleanup_and_exit)
    signal.signal(signal.SIGINT, cleanup_and_exit)

    try:
        # Create Deepgram client
        deepgram = DeepgramClient()

        # Get WebSocket connection
        dg_connection = deepgram.listen.websocket.v("1")

        # Event handler for transcription results
        def on_message(self, result, **kwargs):
            sentence = result.channel.alternatives[0].transcript
            if len(sentence) > 0 and result.is_final:
                print(f"Transcript: {sentence}")
                type(sentence + " ")

        # Register event handler
        dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)

        # Configure transcription options
        options = LiveOptions(
            model="nova-3",
            language="en-US",
            encoding="linear16",
            channels=1,
            sample_rate=16000,
            punctuate=True,
            smart_format=True,
        )

        # Start WebSocket connection
        dg_connection.start(options)

        # Create and start microphone
        microphone = Microphone(dg_connection.send)
        microphone.start()

        print("Transcription started. Use 'dictator end' to stop.")

        # Keep running until signal received
        while True:
            signal.pause()

    except KeyboardInterrupt:
        cleanup_and_exit()
    except Exception as e:
        print(f"Error: {e}")
        cleanup_and_exit()


def end():
    lockfile = "/tmp/dictator.pid"

    if not os.path.exists(lockfile):
        print("No running dictator process found.")
        return

    try:
        # Read PID from lockfile
        with open(lockfile, "r") as f:
            pid = int(f.read().strip())

        # Check if process is still running
        try:
            os.kill(pid, 0)  # Signal 0 checks if process exists
        except ProcessLookupError:
            print("Dictator process is not running (stale lockfile).")
            os.remove(lockfile)
            return

        # Send SIGTERM to gracefully stop the process
        os.kill(pid, signal.SIGTERM)
        print("Sent stop signal to dictator process.")

    except (ValueError, FileNotFoundError, PermissionError) as e:
        print(f"Error stopping dictator: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", type=str, choices=["begin", "end"])

    args = parser.parse_args()

    if args.command == "begin":
        begin()
    elif args.command == "end":
        end()


if __name__ == "__main__":
    main()
