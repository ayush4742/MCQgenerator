import os
import json
from dotenv import load_dotenv
import streamlit as st

load_dotenv()

st.set_page_config(page_title="MCQ Generator", layout="wide", initial_sidebar_state="expanded")

# Small theme and layout polish
st.markdown(
	"""
	<style>
	/* modest card / layout improvements */
	.reportview-container .sidebar .sidebar-content {padding-top: 1rem}
	.stApp { background-color: #0f1720; color: #e6eef6; }
	.big-title { font-size:28px; font-weight:700; }
	.muted { color: #9aa7b2; }
	.result-card { background: linear-gradient(90deg, #0f1720, #111827); padding: 12px; border-radius: 8px; }
	</style>
	""",
	unsafe_allow_html=True,
)

st.markdown("<div class='big-title'>🧠 Automated MCQ Generator — demo</div>", unsafe_allow_html=True)
st.write("Create multiple-choice quizzes from text or uploaded files. Use the sidebar to control generation settings.")

OPENAI_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_KEY:
	st.warning("No OpenAI API key found. Place your key in a .env file as OPENAI_API_KEY to enable generation.")
	st.info("You can still paste sample text and use the demo UI without generating (mock mode).")

with st.sidebar:
	st.header("Settings")
	num_questions = st.number_input("Number of MCQs", value=3, min_value=1, max_value=20)
	subject = st.text_input("Subject", value="general knowledge")
	tone = st.selectbox("Tone", options=["simple", "normal", "academic", "funny"], index=1)
	model_choice = st.selectbox("Model", options=["gpt-3.5-turbo", "gpt-3.5-turbo-0613", "gpt-4"], index=0, help="Choose the model to use for generation (gpt-3.5-turbo is cheaper).")
	temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.7, step=0.05)
	use_api = st.checkbox("Use OpenAI (requires API key)", value=bool(OPENAI_KEY))
	estimate_cost = st.checkbox("Show cost estimate (approx)", value=False)

uploaded = st.file_uploader("Upload a .txt or .pdf file (optional)", type=["txt", "pdf"], help="PDF and TXT supported. Scanned PDFs may not extract text well.")
text_area = st.text_area("Or paste text here (used if no file is uploaded)", height=250)

if uploaded is not None:
	try:
		from src.mcqgenerator.utils import read_file

		TEXT = read_file(uploaded)
	except Exception as e:
		st.error(f"Could not read uploaded file: {e}")
		TEXT = ""
else:
	TEXT = text_area

if TEXT:
	# preview extracted text to the user so they can confirm
	with st.expander("Preview extracted / pasted text", expanded=False):
		st.write(TEXT[:8000])
		st.caption(f"Length: {len(TEXT)} characters — shown first 8k chars")

	# word/token estimate
	words = len(TEXT.split())
	est_tokens = int(words * 1.33)  # rough tokens estimate (approx)
	if 'estimate_cost' in locals() and estimate_cost:
		st.info(f"Approx words: {words}, approx tokens: {est_tokens}")

sample_response = {
	"1": {"mcq": "Which gas do plants use in photosynthesis?",
		  "options": {"a": "Oxygen", "b": "Carbon Dioxide", "c": "Nitrogen", "d": "Hydrogen"},
		  "correct": "b"}
}

col1, col2 = st.columns([1, 1])
with col1:
	run = st.button("Generate MCQs", use_container_width=True)
with col2:
	st.write("\n")
	if estimate_cost and TEXT:
		# very rough example rates - we provide only an approximate token count (do not charge user)
		if model_choice and "3.5" in model_choice:
			per_k = 0.002
		else:
			per_k = 0.03
		est_cost = (est_tokens / 1000.0) * per_k
		st.caption(f"Est. cost for input: ${est_cost:.5f} (approx)")

if run:
	if not TEXT or len(TEXT.strip()) < 10:
		st.error("Please provide some input text (upload a file or paste text).")
	else:
		if use_api and not OPENAI_KEY:
			st.error("OpenAI key not found. Uncheck 'Use OpenAI' or add OPENAI_API_KEY to .env.")
		else:
			st.spinner("Generating...")
			try:
				# set chosen model and temp so MCQGenerator picks it up on import
				os.environ["OPENAI_MODEL"] = model_choice
				os.environ["OPENAI_TEMP"] = str(temperature)
				# Use the chain only if requested; handle missing API and fallback to sample
				if use_api:
					from src.mcqgenerator.MCQGenerator import generate_evaluate_chain

					inputs = {
						"text": TEXT,
						"number": int(num_questions),
						"subject": subject,
						"tone": tone,
						"response_json": json.dumps(sample_response),
					}
					try:
						result = generate_evaluate_chain(inputs)
					except ImportError as ie:
						# specific guidance for missing langchain_community
						msg = str(ie)
						if "langchain_community" in msg or "langchain-community" in msg:
							st.error("Missing optional package 'langchain-community'. Install it in your env: `python -m pip install langchain-community` and restart the app.")
						else:
							st.error(f"Import error when attempting generation: {msg}")
						# stop further processing of generation
						raise
					except Exception as gen_e:
						# detect OpenAI quota / rate-limit style errors and fallback to demo mode
						msg = str(gen_e).lower()
						if "insufficient_quota" in msg or "exceeded your current quota" in msg or "429" in msg or "quota" in msg:
							st.error(
								"OpenAI quota exceeded (429 insufficient_quota). The request was rejected by OpenAI — check your account usage and billing."
							)
							st.info("Falling back to demo sample output so the UI remains usable. To fix: add funds/update billing or wait for the quota to reset.")
							parsed_quiz = sample_response
						else:
							# re-raise for other errors which will be caught below
							raise

					quiz = result.get("quiz")
					# sometimes quiz may be a JSON string
					try:
						parsed_quiz = json.loads(quiz) if isinstance(quiz, str) else quiz
					except Exception:
						parsed_quiz = quiz
					st.success("Generated quiz (see table below)")
				else:
					parsed_quiz = sample_response
					st.info("Demo (mock) mode — no API used. Using a small sample response to show results.")

				# Convert to table via helper
				from src.mcqgenerator.utils import get_table_data, extract_json_from_text

				# parsed_quiz might be a dict or a raw string containing JSON with extra text
				try:
					table_data = get_table_data(parsed_quiz)
				except Exception as tb_err:
					# if parsing failed, try to help the user by extracting a JSON block
					try:
						if isinstance(parsed_quiz, str):
							parsed_quiz = extract_json_from_text(parsed_quiz)
							table_data = get_table_data(parsed_quiz)
						else:
							raise
					except Exception as ex2:
						st.error(f"Json Parse Error: {ex2}. The model output may not be valid JSON — raw output below:")
						st.code(quiz)
						raise
				import pandas as pd

				if table_data:
					df = pd.DataFrame(table_data)
					st.markdown("### Results")
					st.dataframe(df)
					st.download_button("Download CSV", df.to_csv(index=False), file_name="mcqs.csv")

					# --- interactive per-question UI ---
					st.markdown("---")
					st.subheader("Review & edit generated questions")

					# ensure session state stores the current quiz for editing/regenerate operations
					if "quiz_dict" not in st.session_state:
						st.session_state.quiz_dict = parsed_quiz if isinstance(parsed_quiz, dict) else json.loads(parsed_quiz)
						st.session_state.accepted = {k: False for k in st.session_state.quiz_dict.keys()}
						st.session_state.editing = {k: False for k in st.session_state.quiz_dict.keys()}

					def save_edit(qid, new_mcq, new_options, new_correct):
						st.session_state.quiz_dict[qid]["mcq"] = new_mcq
						st.session_state.quiz_dict[qid]["options"] = new_options
						st.session_state.quiz_dict[qid]["correct"] = new_correct
						st.session_state.editing[qid] = False

					def accept_question(qid):
						st.session_state.accepted[qid] = True

					def regenerate_question(qid):
						# regenerate only this question using quiz_chain with number=1
						try:
							from src.mcqgenerator.MCQGenerator import generate_evaluate_chain
							sample = {"1": {"mcq": "updated mcq", "options": {"a": "choice", "b": "choice", "c": "choice", "d": "choice"}, "correct": "a"}}

							inputs_single = {
								"text": TEXT,
								"number": 1,
								"subject": subject,
								"tone": tone,
								"response_json": json.dumps(sample),
							}

							with st.spinner(f"Regenerating question {qid}..."):
								single_out = generate_evaluate_chain(inputs_single)

							# quiz_chain returns a dictionary-like output where quiz is present as string
							if isinstance(single_out, dict):
								raw_quiz = single_out.get("quiz")
							else:
								raw_quiz = single_out

							# parse quiz for the single generated question
							try:
								if isinstance(raw_quiz, str):
									parsed_single = json.loads(raw_quiz)
								else:
									parsed_single = raw_quiz
							except Exception:
								from src.mcqgenerator.utils import extract_json_from_text
								parsed_single = extract_json_from_text(raw_quiz)

							# parsed_single must be a dict with key '1'
							new_q = parsed_single.get("1") if isinstance(parsed_single, dict) else None
							if new_q:
								st.session_state.quiz_dict[qid] = new_q
								st.success(f"Question {qid} regenerated")
							else:
								st.error("Regeneration returned unexpected format")

						except ImportError as impx:
							st.error("Missing quiz_chain implementation. Make sure MCQGenerator + its dependencies are installed.")
						except Exception as ex:
							st.error(f"Regenerate failed: {ex}")

					# Render interactive question blocks
					for qid in sorted(st.session_state.quiz_dict.keys(), key=lambda x: int(x)):
						q = st.session_state.quiz_dict[qid]
						st.markdown(f"#### Question {qid}")
						cols = st.columns([7, 1, 1, 1])
						with cols[0]:
							if st.session_state.editing.get(qid, False):
								new_mcq = st.text_area(f"Edit MCQ {qid}", value=q.get("mcq", ""), key=f"edit_mcq_{qid}")
								# edit options
								opts = q.get("options", {})
								new_opts = {}
								new_opts["a"] = st.text_input(f"a) option {qid}", value=opts.get("a", ""), key=f"opt_a_{qid}")
								new_opts["b"] = st.text_input(f"b) option {qid}", value=opts.get("b", ""), key=f"opt_b_{qid}")
								new_opts["c"] = st.text_input(f"c) option {qid}", value=opts.get("c", ""), key=f"opt_c_{qid}")
								new_opts["d"] = st.text_input(f"d) option {qid}", value=opts.get("d", ""), key=f"opt_d_{qid}")
								new_correct = st.selectbox("Correct option", options=["a", "b", "c", "d"], index=["a","b","c","d"].index(q.get("correct","a")), key=f"correct_{qid}")
								if st.button("Save edit", key=f"save_{qid}"):
									save_edit(qid, new_mcq, new_opts, new_correct)
							else:
								st.markdown(f"**Q:** {q.get('mcq', '')}")
								opts_display = "\n".join([f"**{k}**: {v}" for k, v in q.get("options", {}).items()])
								st.markdown(opts_display)
								st.markdown(f"**Answer:** {q.get('correct','')} ")

						with cols[1]:
							st.write(" ")
							if st.button("Edit", key=f"btn_edit_{qid}"):
								st.session_state.editing[qid] = not st.session_state.editing.get(qid, False)

						with cols[2]:
							st.write(" ")
							if st.button("Accept", key=f"btn_accept_{qid}"):
								accept_question(qid)
								st.success(f"Accepted question {qid}")

						with cols[3]:
							st.write(" ")
							if st.button("Regenerate", key=f"btn_regen_{qid}"):
								regenerate_question(qid)

					# show accepted status
					accepted_list = [k for k, v in st.session_state.accepted.items() if v]
					if accepted_list:
						st.success(f"Accepted questions: {', '.join(sorted(accepted_list, key=lambda x:int(x)))}")

					# allow downloading the updated quiz after edits/regenerations
					try:
						if st.session_state.quiz_dict:
							updated_table = get_table_data(st.session_state.quiz_dict)
							if updated_table:
								import pandas as _pd
								updated_df = _pd.DataFrame(updated_table)
								st.download_button("Download updated CSV", updated_df.to_csv(index=False), file_name="mcqs_updated.csv")
					except Exception:
						# silently ignore if conversion fails
						pass
					st.download_button("Download CSV", df.to_csv(index=False), file_name="mcqs.csv")
				else:
					st.warning("Could not convert the returned quiz into a table. Raw output below:")
					with st.expander("Raw LLM output"):
						st.code(quiz)
						st.json(parsed_quiz) if isinstance(parsed_quiz, dict) else st.text(parsed_quiz)

			except Exception as e:
				st.error(f"Generation failed: {e}")

st.markdown("---")
st.caption("Streamlit demo for the Automated MCQ Generator. If you want a sample script instead, run `run_example.py`.")
