"""Simple example script to exercise the MCQ generator chain.

This script will try to import the chain from the package and run it.
If an OpenAI API key is not found it will explain how to set it. The script is
useful to test the project from the command line.
"""
import os
import json
from dotenv import load_dotenv

load_dotenv()

OPENAI_KEY = os.getenv("OPENAI_API_KEY")

def main():
    if not OPENAI_KEY:
        print("No OPENAI_API_KEY found. Create a .env file containing OPENAI_API_KEY=sk-... or set the environment variable and re-run.")
        return

    # sample input
    TEXT = "Photosynthesis is the process by which plants convert sunlight into chemical energy."
    RESPONSE_JSON = {
        "1": {"mcq": "Which process converts light to chemical energy in plants?",
              "options": {"a": "Respiration", "b": "Transpiration", "c": "Photosynthesis", "d": "Fermentation"},
              "correct": "c"}
    }

    try:
        from src.mcqgenerator.MCQGenerator import generate_evaluate_chain

        inputs = {
            "text": TEXT,
            "number": 1,
            "subject": "biology",
            "tone": "simple",
            "response_json": json.dumps(RESPONSE_JSON),
        }

        print("Calling generator — this will make an OpenAI request and incur token usage.")
        out = generate_evaluate_chain(inputs)
        print("Result (raw):")
        print(out)

        # try to parse the quiz portion robustly
        try:
            quiz = out.get("quiz")
            from src.mcqgenerator.utils import extract_json_from_text, get_table_data

            if isinstance(quiz, str):
                parsed = None
                try:
                    parsed = json.loads(quiz)
                except Exception:
                    parsed = extract_json_from_text(quiz)
            else:
                parsed = quiz

            print("Parsed quiz:")
            print(json.dumps(parsed, indent=2))

            # show a simple table-like print
            table = get_table_data(parsed)
            if table:
                print("\nTabular view:\n")
                for row in table:
                    print(row)

        except Exception as e:
            print("Could not parse quiz response into JSON/table:", e)

    except ImportError as exc:
        msg = str(exc)
        if "langchain_community" in msg or "langchain-community" in msg:
            print("Missing package 'langchain-community'. Install with: python -m pip install langchain-community")
        else:
            print("ImportError:", exc)
    except Exception as exc:
        msg = str(exc).lower()
        # friendly handling for insufficient quota / 429
        if "insufficient_quota" in msg or "exceeded your current quota" in msg or "429" in msg or "quota" in msg:
            print("OpenAI reported insufficient quota (429). Please check your OpenAI billing and usage at https://platform.openai.com/account/usage")
            print("Falling back to demo sample response so you can inspect the output without calling the API.")
            print("Sample response:")
            print(json.dumps(RESPONSE_JSON, indent=2))
        else:
            print("Error: failed to run generator. Be sure all requirements are installed and your OPENAI_API_KEY is valid.")
            print(type(exc), exc)


if __name__ == "__main__":
    main()
