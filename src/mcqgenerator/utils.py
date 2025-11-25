import os
import PyPDF2
import json
import traceback
import io


def read_file(file):
    # support file being either a path (str), an uploaded file-like object (streamlit), or a file object
    filename = getattr(file, "name", None) or str(file)
    filename_lower = filename.lower()

    if filename_lower.endswith(".pdf"):
        try:
            # If file has a read() method, read bytes and use a BytesIO wrapper
            if hasattr(file, "read"):
                data = file.read()
                # if Streamlit's UploadedFile, `read()` returns bytes
                stream = io.BytesIO(data if isinstance(data, (bytes, bytearray)) else data.encode("utf-8"))
                PdfClass = getattr(PyPDF2, "PdfReader", None) or getattr(PyPDF2, "PdfFileReader", None)
                if PdfClass is None:
                    raise Exception("PyPDF2 does not provide a PdfReader or PdfFileReader class in this installation")
                reader = PdfClass(stream)
            else:
                # treat file as a path
                PdfClass = getattr(PyPDF2, "PdfReader", None) or getattr(PyPDF2, "PdfFileReader", None)
                if PdfClass is None:
                    raise Exception("PyPDF2 does not provide a PdfReader or PdfFileReader class in this installation")
                reader = PdfClass(filename)

            text_chunks = []
            # two API styles: `pages` (list-like) or legacy getNumPages()/getPage(i)
            if hasattr(reader, "pages"):
                for page in reader.pages:
                    # new PyPDF2: page.extract_text()
                    page_text = ""
                    try:
                        page_text = page.extract_text() or ""
                    except Exception:
                        # fallback to str(page) if extract_text fails
                        page_text = ""
                    text_chunks.append(page_text)
            elif hasattr(reader, "getNumPages"):
                for i in range(reader.getNumPages()):
                    try:
                        p = reader.getPage(i)
                        page_text = p.extractText() or ""
                    except Exception:
                        page_text = ""
                    text_chunks.append(page_text)
            else:
                # unknown reader object — try string conversion
                try:
                    text_chunks.append(str(reader))
                except Exception:
                    pass

            return "\n".join(text_chunks)

        except Exception as e:
            # include original exception to make debugging easier
            raise Exception(f"error reading the PDF file: {e}")
        
    elif filename_lower.endswith(".txt"):
        if hasattr(file, "read"):
            data = file.read()
            if isinstance(data, (bytes, bytearray)):
                return data.decode("utf-8", errors="ignore")
            return data
        else:
            # treat file as path
            with open(filename, "r", encoding="utf-8", errors="ignore") as fh:
                return fh.read()
    
    else:
        raise Exception(
            "unsupported file format only pdf and text file suppoted"
            )

def get_table_data(quiz_str):
    try:
        # Accept either a dict or a string (possibly containing JSON with extra text).
        if isinstance(quiz_str, dict):
            quiz_dict = quiz_str
        else:
            # try parsing free-form LLM output robustly
            from json import JSONDecodeError

            try:
                quiz_dict = json.loads(quiz_str)
            except JSONDecodeError:
                # attempt to extract a JSON object from the surrounding text
                quiz_dict = extract_json_from_text(quiz_str)
        quiz_table_data=[]
        
        # iterate over the quiz dictionary and extract the required information
        for key,value in quiz_dict.items():
            mcq=value["mcq"]
            options=" || ".join(
                [
                    f"{option}-> {option_value}" for option, option_value in value["options"].items()
                 
                 ]
            )
            
            correct=value["correct"]
            quiz_table_data.append({"MCQ": mcq,"Choices": options, "Correct": correct})
        
        return quiz_table_data
        
    except Exception as e:
        traceback.print_exception(type(e), e, e.__traceback__)
        return False


def extract_json_from_text(text):
    """Try to extract a single JSON object or array from a longer string.

    This will look for fenced code blocks containing JSON, or the first well-formed
    JSON object/array starting at the first bracket. If extraction fails a
    ValueError is raised.
    """
    if not isinstance(text, str):
        raise ValueError("Expected text to be a string")

    s = text.strip()
    # first, look for fenced code block ```json ... ``` or ``` ... ```
    import re

    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", s, re.IGNORECASE)
    if m:
        candidate = m.group(1).strip()
        try:
            return json.loads(candidate)
        except Exception:
            # fall through and try other heuristics
            pass

    # next, find first bracket character that could start JSON
    start = None
    for i, ch in enumerate(s):
        if ch in '{[':
            start = i
            break
    if start is None:
        raise ValueError("No JSON object found in text")

    # attempt to find the matching closing bracket using a stack so we capture nested braces
    open_char = s[start]
    close_char = '}' if open_char == '{' else ']'
    depth = 0
    for j in range(start, len(s)):
        if s[j] == open_char:
            depth += 1
        elif s[j] == close_char:
            depth -= 1
            if depth == 0:
                candidate = s[start:j+1]
                try:
                    return json.loads(candidate)
                except Exception:
                    # if parsing fails, continue scanning for another closing position
                    continue

    # give up — try a last resort: attempt to extract single-line JSON-ish with regex
    m2 = re.search(r"(\{[\s\S]*\})", s)
    if m2:
        try:
            return json.loads(m2.group(1))
        except Exception:
            pass

    raise ValueError("Could not extract a valid JSON object from the text")


