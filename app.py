import streamlit as st 
from openai import OpenAI
import os 
from datetime import date 

st.title("Daily Health Tracker")
st.caption("A health app designed to motivate, not shame you. No medical advice provided.")

client = OpenAI(api_key=os.environ.get('DEEPSEEK_API_KEY'), base_url="https://api.deepseek.com")

if "openai_model" not in st.session_state:
    st.session_state.openai_model = "deepseek-chat"

if "messages" not in st.session_state:
	st.session_state.messages = []
if "diary" not in st.session_state:
	st.session_state.diary = []
if "last_checkin_date" not in st.session_state:
	st.session_state.last_checkin_date = None
if "streak" not in st.session_state:
	st.session_state.streak = 0
if "reflection" not in st.session_state:
	st.session_state.reflection = False 
if "today_log" not in st.session_state:
    st.session_state.today_log = {
        "steps": None,
        "water_oz": None,
        "calories": None,
        "active_minutes": None,
        "workout": None,
        "notes": None,
        "diary": None,
	} 

today = date.today()
checked_in_today = (st.session_state.last_checkin_date == today)
st.caption(f"Streak: {st.session_state.streak} day(s)" + ("checked off" if checked_in_today else""))

with st.sidebar:
	st.subheader("Today's stats")

	st.session_state.today_log["steps"] = st.number_input("Steps", min_value = 0, value = int(st.session_state.today_log["steps"] or 0))
	st.session_state.today_log["water_oz"] = st.number_input("Water (oz)", min_value = 0, value = int(st.session_state.today_log["water_oz"] or 0))
	st.session_state.today_log["calories"] = st.number_input("Calories (optional)", min_value = 0, value = int(st.session_state.today_log["calories"] or 0))
	st.session_state.today_log["active_minutes"] = st.number_input("Active minutes", min_value = 0, value = int(st.session_state.today_log["active_minutes"] or 0))
	st.session_state.today_log["workout"] = st.text_input("Workout (optional)", value = st.session_state.today_log["workout"])
	st.session_state.today_log["notes"] = st.text_area("Notes (optional)", value = st.session_state.today_log["notes"])

# mode 
mode = st.selectbox("Mode", ["Beginner", "Intermediate", "Advanced"])

# system prompt 
def system_prompt(mode):
	base = """
You are a supportive, non-judgemental health and fitness check-in assistant. Do not give medical advice. Do not diagnose or prescribe extreme dieting or unsafe exercise. Aviod labeling food as "good/bad" or something that should be "earned." Do not ever mention starving or extreme exercise. Be realistic, kind, and concise.

Your job:
- Help user reflect on day 
- Offer 2-5 simple suggestions 
- Use gentle questions 

If user expresses guilt/shame/avoidance be encouraging and understanding. Reduce pressure.

OUTPUT FORMAT: Output TWO sections in this exact order:
SECTION 1: USER_MESSAGE
A supportive response (3-8 sentences) + 2-5 bullet suggestions (optional) + one/two gentle follow-up questions.


"""

	if mode == "Beginner":
		style = """
Beginner: Very friendly and motivating. Simple suggestions. Avoid numbers. Step count/numbers related to exercise are alright, but avoid calories unless user mentions them.
"""

	elif mode == "Intermediate": 
		style = """
Intermediate: Reference numbers the user shares. Do not set strict targets. Calories are okay, but don't remind user about specific number of calories. Offer options such as simple routines, snack ideas, or healthy swaps.
"""

	else:
		style = """
Advanced: focus on consistency, planning, recovery, future plans. Avoid strict prescriptions. Numbers are ok to discuss, but be courteous, respectful, and caring.
"""
	return base + "\n" + style 

st.subheader("Today")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Steps", "—" if st.session_state.today_log["steps"] is None else str(st.session_state.today_log["steps"]))
c2.metric("Water (oz)", "—" if st.session_state.today_log["water_oz"] is None else str(st.session_state.today_log["water_oz"]))
c3.metric("Calories", "—" if st.session_state.today_log["calories"] is None else str(st.session_state.today_log["calories"]))
c4.metric("Active min", "—" if st.session_state.today_log["active_minutes"] is None else str(st.session_state.today_log["active_minutes"]))

if not st.session_state.messages:
	st.session_state.messages.append({"role" : "assistant", "content" : "Tell me how your health was today. Walk me through what you ate, how you worked out, and how you felt. We'll go from there."})

# render chat history
for message in st.session_state.messages:
	with st.chat_message(message["role"]):
		st.markdown(message["content"])

prompt = st.chat_input("Type your check-in here")

if prompt:
	st.session_state.messages.append({"role": "user", "content": prompt})
	with st.chat_message("user"):
        	st.markdown(prompt)

	log = st.session_state.today_log 
	stats_context = (
		"Today's logged stats:\n"
		f" - Steps: {log['steps']}\n"
		f" - Water (oz): {log['water_oz']}\n"
        	f"- Calories (optional): {log['calories']}\n"
        	f"- Active minutes: {log['active_minutes']}\n"
        	f"- Workout: {log['workout']}\n"
        	f"- Notes: {log['notes']}\n"
	)

	reflection_context = ""
	if st.session_state.reflection:
		reflection_context = """
	The user has chosen reflection mode. The user wants you to do a concise summary about their patterns, emotions, and gentle encouragement. Focus on the bigger picture of health rather than small metrics.
	"""

	messages_for_model = [
		{"role" : "system", "content" : system_prompt(mode) + reflection_context}, 
		*st.session_state.messages[-6:],
		{"role" : "user", "content" : stats_context + "\n\nMy check-in: " + prompt}
	
	]

	with st.chat_message("assistant"):
		with st.spinner("Thinking..."):
			response = client.chat.completions.create(
				model = st.session_state.openai_model,
				messages = messages_for_model,
				temperature = 0.5,
			)

			reply = response.choices[0].message.content
			st.markdown(reply)

			# save assistant response
			st.session_state.messages.append({"role": "assistant", "content": reply}),
			st.session_state.reflection = False 

	if st.button("Reflection") and st.session_state.messages:
		st.session_state.reflection = True
		st.session_state.messages.append({"role" : "user", "content" : "Please give me a reflection summary."})
		st.rerun()

	st.divider()
	col1, col2 = st.columns(2)
	with col1:
		if checked_in_today:
			st.success("You already checked in today")
		else:
			if st.button("Complete today"):
				st.session_state.last_checkin_date = today
				st.session_state.streak += 1
				st.rerun()
	with col2:
		if st.button("New day / reset chat"):
			st.session_state.messages = []
			st.session_state.today_log = {"steps": None,"water_oz": None,"calories": None,"active_minutes": None,"workout": None,"notes": None,"diary": None,}
			st.rerun()













