import streamlit as st
import st_yled
import json
import re
from openai import OpenAI

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
st.set_page_config(page_title="Shadow Castle Adventure", layout="wide")
st_yled.init()

if "started" not in st.session_state:
    st.session_state.started = False

if "scene" not in st.session_state:
    st.session_state.scene = ""

if "choices" not in st.session_state:
    st.session_state.choices = []

if "result" not in st.session_state:
    st.session_state.result = ""

if "hp" not in st.session_state:
    st.session_state.hp = 100

if "attack" not in st.session_state:
    st.session_state.attack = 15

if "defense" not in st.session_state:
    st.session_state.defense = 10
# This application is a dungeon adventure game where the player explores a cursed castle.
# The player enters a character name, starts the game, and chooses one of the generated actions each turn.

# The expected user input is a character name and then selecting one of the provided radio choices.

# AI-assisted styling: used ChatGPT to suggest a dark fantasy color palette and visual layout.

st.set_page_config(page_title="Shadow Castle Adventure", layout="wide")

SYSTEM_PROMPT = """
You are the game master of a dungeon adventure game.

You must always respond ONLY in valid JSON.
Do not include markdown.
Do not include code fences.
Do not include explanations outside JSON.

Return this exact JSON structure:
{
  "scene": "A short immersive scene description in 3-5 sentences.",
  "choices": ["choice 1", "choice 2", "choice 3"],
  "stat_changes": {
    "hp": 0,
    "attack": 0,
    "defense": 0
  },
  "result": "A short sentence describing what changed."
}

Rules:
- Continue the story based on previous events.
- Always provide exactly 3 choices.
- Keep scenes short and readable.
- Choices should be clear actions.
- stat_changes values must be small integers, usually between -15 and 15.
- Avoid ending the whole game too quickly.
- If the player reaches 0 HP, still return valid JSON and describe defeat.
- Maintain a dark fantasy dungeon tone.
"""

def safe_parse_json(text):
    """
    Try to parse model output safely.
    Handles code fences and extra text if they appear accidentally.
    """
    text = text.strip()

    # remove markdown fences if present
    text = re.sub(r"^```json\s*", "", text)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    # try direct parse first
    try:
        return json.loads(text)
    except:
        pass

    # extract first {...} block
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        candidate = match.group(0)
        return json.loads(candidate)

    raise ValueError("Could not parse JSON response.")

def validate_response(data):
    """
    Ensure required keys exist and have usable values.
    """
    if "scene" not in data or not isinstance(data["scene"], str):
        raise ValueError("Missing or invalid 'scene'.")

    if "choices" not in data or not isinstance(data["choices"], list) or len(data["choices"]) != 3:
        raise ValueError("Missing or invalid 'choices'.")

    if "stat_changes" not in data or not isinstance(data["stat_changes"], dict):
        data["stat_changes"] = {"hp": 0, "attack": 0, "defense": 0}

    for key in ["hp", "attack", "defense"]:
        if key not in data["stat_changes"] or not isinstance(data["stat_changes"][key], int):
            data["stat_changes"][key] = 0

    if "result" not in data or not isinstance(data["result"], str):
        data["result"] = "The adventure continues."

    return data

def get_gm_response(messages):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.9
    )

    raw_text = response.choices[0].message.content
    data = safe_parse_json(raw_text)
    data = validate_response(data)
    return raw_text, data

def initialize_game(player_name):
    st.session_state.started = True
    st.session_state.player_name = player_name
    st.session_state.hp = 100
    st.session_state.attack = 15
    st.session_state.defense = 10
    st.session_state.result = ""
    st.session_state.game_over = False

    st.session_state.messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"""
Start a new dungeon adventure for a player named {player_name}.

Current stats:
HP: 100
Attack: 15
Defense: 10

Generate the opening dungeon scene.
"""
        }
    ]

    raw_text, data = get_gm_response(st.session_state.messages)

    st.session_state.messages.append({"role": "assistant", "content": raw_text})
    st.session_state.scene = data["scene"]
    st.session_state.choices = data["choices"]
    st.session_state.result = data["result"]

def apply_stat_changes(changes):
    st.session_state.hp += changes["hp"]
    st.session_state.attack += changes["attack"]
    st.session_state.defense += changes["defense"]

    if st.session_state.hp < 0:
        st.session_state.hp = 0
    if st.session_state.attack < 0:
        st.session_state.attack = 0
    if st.session_state.defense < 0:
        st.session_state.defense = 0

    if st.session_state.hp == 0:
        st.session_state.game_over = True

def process_choice(choice):
    user_message = f"""
Player name: {st.session_state.player_name}
Player chose: {choice}

Current stats before this turn:
HP: {st.session_state.hp}
Attack: {st.session_state.attack}
Defense: {st.session_state.defense}

Continue the story and determine small stat changes based on the action.
"""

    st.session_state.messages.append({"role": "user", "content": user_message})

    raw_text, data = get_gm_response(st.session_state.messages)
    st.session_state.messages.append({"role": "assistant", "content": raw_text})

    apply_stat_changes(data["stat_changes"])

    st.session_state.scene = data["scene"]
    st.session_state.choices = data["choices"]
    st.session_state.result = data["result"]

    if st.session_state.hp == 0:
        st.session_state.scene += " Your strength is gone, and darkness closes in around you."

def restart_game():
    keys_to_clear = [
        "started", "player_name", "hp", "attack", "defense",
        "scene", "choices", "messages", "result", "game_over"
    ]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

# ---------- session state defaults ----------
if "started" not in st.session_state:
    st.session_state.started = False

# ---------- title ----------
st.markdown(
    """
    <h1 style='text-align: center; color: #d8bfd8; font-size: 44px; margin-bottom: 8px;'>
    Shadow Castle Adventure
    </h1>
    """,
    unsafe_allow_html=True
)

# ---------- start page ----------
if not st.session_state.started:
    st.markdown(
        """
        <h3 style='text-align: center; color: #b0c4de; margin-top: 0;'>
        Enter a cursed dungeon where every choice shapes your survival.
        </h3>
        """,
        unsafe_allow_html=True
    )

    with st_yled.container(
        background_color="#1a1a2e",
        border_color="#53354a",
        padding="24px"
    ):
        st.write("Enter your character name to begin the adventure.")
        player_name = st.text_input("Character Name")

        if st.button("Start Game"):
            if player_name.strip():
                try:
                    initialize_game(player_name.strip())
                    st.rerun()
                except Exception as e:
                    st.error(f"Could not start the game: {e}")
            else:
                st.warning("Please enter a character name.")

# ---------- main game page ----------
else:
    col1, col2 = st.columns([2.2, 1])

    with col1:
        with st_yled.container(
            background_color="#1a1a2e",
            border_color="#4a0e0e",
            padding="22px"
        ):
            st.markdown(
                f"""
                <div style='color: #f8f8ff; font-size: 20px; line-height: 1.7;'>
                {st.session_state.scene}
                </div>
                """,
                unsafe_allow_html=True
            )

        st.write("")

        if st.session_state.game_over:
            st.error("Game Over")
        else:
            choice = st.radio(
                "Choose your action:",
                st.session_state.choices,
                key="current_choice"
            )

            if st.button("Confirm Choice"):
                try:
                    process_choice(choice)
                    st.rerun()
                except Exception as e:
                    st.error(f"Something went wrong while continuing the story: {e}")

        if st.session_state.result:
            st.info(st.session_state.result)

    with col2:
        with st_yled.container(
            background_color="#16213e",
            border_color="#0f3460",
            padding="20px"
        ):
            st.markdown(
                f"""
                <h3 style='color: #e6e6fa; margin-top: 0;'>Character Stats</h3>
                <p style='color: white; font-size: 18px; line-height: 1.8;'>
                <b>Name:</b> {st.session_state.player_name}<br>
                <b>HP:</b> {st.session_state.hp}<br>
                <b>Attack:</b> {st.session_state.attack}<br>
                <b>Defense:</b> {st.session_state.defense}
                </p>
                """,
                unsafe_allow_html=True
            )

        st.write("")

        if st.button("Restart Game"):
            restart_game()
            st.rerun()

        st.write("")
        st.caption("Each turn is generated dynamically by AI.")