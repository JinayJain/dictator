import argparse
import logging
import os
import signal
import subprocess
import sys
import time

from deepgram import DeepgramClient, FileSource, PrerecordedOptions
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def type_text(text: str):
    logger.info(f"Typing: {text}")
    result = subprocess.run(["xdotool", "type", text], capture_output=True, text=True)

    if result.stderr:
        logger.error(f"xdotool error: {result.stderr}")


def begin():
    lockfile = "/tmp/dictator.pid"

    # Write PID to lockfile
    with open(lockfile, "w") as f:
        f.write(str(os.getpid()))

    # Global variables
    recording_process = None

    def cleanup_and_exit(signum=None, frame=None):
        logger.info("Received shutdown signal")
        print("\nStopping recording...")

        time.sleep(0.5)

        nonlocal recording_process
        if recording_process:
            logger.debug("Stopping recording process...")
            recording_process.terminate()
            recording_process.wait()  # Wait for process to fully terminate

            audio_file = "/tmp/dictator_recording.wav"
            if os.path.exists(audio_file) and os.path.getsize(audio_file) > 0:
                logger.info("Transcribing audio...")
                transcript = transcribe_audio_file(audio_file)

                if transcript:
                    logger.info("Typing transcript...")
                    print(f"Transcript: {transcript}")
                    type_text(transcript)
                else:
                    logger.warning("No transcript generated")

                # Clean up the audio file
                os.remove(audio_file)
            else:
                logger.warning("No audio data recorded")

        # Remove lockfile
        if os.path.exists(lockfile):
            os.remove(lockfile)
        sys.exit(0)

    # Register signal handlers
    signal.signal(signal.SIGTERM, cleanup_and_exit)
    signal.signal(signal.SIGINT, cleanup_and_exit)

    try:
        # Start audio recording using parec, saving to tmp file
        audio_file = "/tmp/dictator_recording.wav"
        logger.info("Starting audio recording...")
        recording_process = subprocess.Popen(
            [
                "parec",
                "--file-format=wav",  # output WAV format
                "--format=s16le",  # 16-bit little-endian
                "--rate=16000",  # 16kHz sample rate
                "--channels=1",  # mono
                audio_file,  # output to file
            ]
        )

        logger.info("Recording started. Use 'dictator end' to stop and transcribe.")
        print("Recording started. Use 'dictator end' to stop and transcribe.")

        # Keep running until signal received
        while True:
            signal.pause()

    except KeyboardInterrupt:
        cleanup_and_exit()
    except Exception as e:
        logger.error(f"Error: {e}")
        cleanup_and_exit()


def transcribe_audio_file(audio_file_path: str) -> str:
    try:
        # Create Deepgram client
        deepgram = DeepgramClient()

        # Prepare options for transcription
        options = PrerecordedOptions(
            model="nova-3",
            language="en-US",
            punctuate=True,
            smart_format=True,
        )

        custom_options = {
            "mip_opt_out": "true",
        }

        # Read the audio file
        with open(audio_file_path, "rb") as audio_file:
            payload: FileSource = {
                "buffer": audio_file,
            }
            # Transcribe the audio file
            response = deepgram.listen.rest.v("1").transcribe_file(
                payload, options, addons=custom_options
            )

        # Extract transcript from response
        if response.results and response.results.channels:
            transcript = response.results.channels[0].alternatives[0].transcript
            return transcript.strip()
        else:
            logger.error("No transcription results found")
            return ""

    except Exception as e:
        logger.error(f"Transcription error: {e}")
        return ""


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
