import streamlit as st
import st_yled
from openai import OpenAI
import re

st.set_page_config(page_title="Dungeon Story Game", layout="wide")#this code comes from Openai
st_yled.init()
st_yled.set("button", "background_color", "#8ab7fa")

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

if "started" not in st.session_state:
    st.session_state.started = False

if "player_name" not in st.session_state:
    st.session_state.player_name = ""

if "HP" not in st.session_state:
    st.session_state.HP = 100

if "Attackpower" not in st.session_state:
    st.session_state.Attackpower = 10

if "shield" not in st.session_state:
    st.session_state.shield = 10

if "specialability" not in st.session_state:
    st.session_state.specialability = []

if "Inventory" not in st.session_state:
    st.session_state.Inventory = []

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "current_text" not in st.session_state:
    st.session_state.current_text = ""

if "current_choices" not in st.session_state:
    st.session_state.current_choices = []

if "turn" not in st.session_state:
    st.session_state.turn = 0

if "last_result" not in st.session_state:
    st.session_state.last_result = ""

# this is from Openai to keep the output in Json
def extract_choices(text):
    """
    从模型输出里提取 1/2/3 三个 choice
    """
    pattern = r'1\.\s*["“]?(.*?)["”]?\s*2\.\s*["“]?(.*?)["”]?\s*3\.\s*["“]?(.*?)["”]?'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return [match.group(1).strip(), match.group(2).strip(), match.group(3).strip()]
    return []

def extract_background(text):
    patterns = [
        r'next_background:\s*["“]?(.*?)["”]?\s*choice:',
        r'background:\s*["“]?(.*?)["”]?\s*choice:',
        r'backgound:\s*["“]?(.*?)["”]?\s*choice:'
    ]


def update_stats_from_text(text):
    #from AI:\s*(\d+)
    hp_match = re.search(r'HP:\s*(\d+)', text, re.IGNORECASE)
    attack_match = re.search(r'Attackpower:\s*(\d+)', text, re.IGNORECASE)
    shield_match = re.search(r'shield:\s*(\d+)', text, re.IGNORECASE)

    if hp_match:
        st.session_state.HP = int(hp_match.group(1))
    if attack_match:
        st.session_state.Attackpower = int(attack_match.group(1))
    if shield_match:
        st.session_state.shield = int(shield_match.group(1))

def get_first_scene():
    system1 = """
    You are a Game Master persona that runs the dungeon crawler.

    Task:
    Give a SHORT BACKGROUND first.
    Then give exactly THREE choices about actions/behaviors.

    RULE:
    - It must give exactly THREE choices.
    - Please give out a short background.
    - Output format should be plain text only.
    - Do NOT write markdown code fences.
    - Do NOT write explanations outside the structure.
    RULE:
    - You MUST provide exactly 3 choices.
    - Each choice MUST be a full sentence.
    - DO NOT leave any choice empty.
    - DO NOT write "3." without content.
    - If unsure, still create a reasonable choice.

    Use this structure exactly:

    background:
    "..."

    choice:
    1. "..."
    2. "..."
    3. "..."
    """

    messages = [
        {"role": "system", "content": system1}
    ]

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages
    )

    text = response.choices[0].message.content
    st.session_state.current_text = text
    st.session_state.current_choices = extract_choices(text)
    st.session_state.chat_history = [
        {"role": "system", "content": system1},
        {"role": "assistant", "content": text}
    ]

def get_followup(choice_picked):
    prev_scene = st.session_state.current_text

    followup = f"""
    You are the Game Master resolving the player's chosen action based on the story so far.

    You MUST:
    1) Read the previous scene and the three choices.
    2) Read the player's selected choice.
    3) Describe what happens next briefly.
    4) Update the player's stats (HP, Attackpower, shield) if needed.
    5) Then present the next scene AND exactly THREE new choices.
    RULE:
    - You MUST provide exactly 3 choices.
    - Each choice MUST be a full sentence.
    - DO NOT leave any choice empty.
    - DO NOT write "3." without content.
    - If unsure, still create a reasonable choice.

    Output format (plain text only, no JSON, no braces, no code fences):

    result:
    "..."

    status_update:
    HP: {st.session_state.HP}
    Attackpower: {st.session_state.Attackpower}
    shield: {st.session_state.shield}
    specialability: {st.session_state.specialability}
    Inventory: {st.session_state.Inventory}

    next_background:
    "..."

    choice:
    1. "..."
    2. "..."
    3. "..."
    """

    user_message = f"""
    Player state now:
    specialability: {st.session_state.specialability}
    shield: {st.session_state.shield}
    Attackpower: {st.session_state.Attackpower}
    HP: {st.session_state.HP}
    Inventory: {st.session_state.Inventory}

    Previous scene (with the 3 choices):
    {prev_scene}

    Player chose:
    {choice_picked}

    Resolve the choice and continue.
    """

    messages = [
        {"role": "system", "content": followup},
        {"role": "user", "content": user_message}
    ]

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages
    )

    text = response.choices[0].message.content

    st.session_state.chat_history.append({"role": "user", "content": choice_picked})
    st.session_state.chat_history.append({"role": "assistant", "content": text})

    st.session_state.current_text = text
    st.session_state.current_choices = extract_choices(text)
    update_stats_from_text(text)

    result_match = re.search(r'result:\s*["“]?(.*?)["”]?\s*status_update:', text, re.DOTALL | re.IGNORECASE)
    if result_match:
        st.session_state.last_result = result_match.group(1).strip()
    else:
        st.session_state.last_result = "The story continues."

def restart_game():
    st.session_state.started = False
    st.session_state.player_name = ""
    st.session_state.HP = 100
    st.session_state.Attackpower = 10
    st.session_state.shield = 10
    st.session_state.specialability = []
    st.session_state.Inventory = []
    st.session_state.chat_history = []
    st.session_state.current_text = ""
    st.session_state.current_choices = []
    st.session_state.turn = 0
    st.session_state.last_result = ""


st_yled.title("Dungeon Story Game", color="#2d1dbdff")


if not st.session_state.started:
    # this code from OpenAI: with st_yled.container()
    with st_yled.container(
        background_color="#4e29ca",
        padding="20px"
    ):
       name = st_yled.text_input("Enter your character name to begin.", color="#f86515ff")

    if st_yled.button("Start Game", color="#3255c6ff"):
            if not name.strip():
                st.warning("Enter your name please.")
            else:
                st.session_state.player_name = name.strip() # .strip is from openai
                st.session_state.started = True
                get_first_scene()
                st.rerun()


else:
    col1, col2 = st.columns([2, 1])

    # background section
    with col1:
        with st_yled.container(
            background_color="#1a1a2e",
            border_color="#f9ce6a",
            padding="20px"
        ):
            st_yled.subheader("Background",color="#159df8ff")
            st_yled.write(extract_background(st.session_state.current_text),color="#f8651500")

        st.write("")

        # result section
        if st.session_state.last_result:
            with st_yled.container(
                background_color="#2f1b2f",
                border_color="#6a0572",
                padding="15px"
            ):
                st_yled.write(f"Result: {st.session_state.last_result}",color="#f0efefff")

        st.write("")

        # choice section
        with st_yled.container(
            background_color="#16213e",
            border_color="#0f3460",
            padding="20px"
        ):
            st_yled.subheader("Choice",color="#cef815bc")

            if len(st.session_state.current_choices) == 3:
                st.write(st.session_state.current_choices)
                selected_choice = st_yled.radio(
                    "Choose one action:",
                    st.session_state.current_choices,
                    key=f"choice_{st.session_state.turn}",
                    color="#76c2f9bc"
                ) # those  line from openai
            

                if st_yled.button("Confirm Choice", color="#fff94de2"):
                    get_followup(selected_choice)
                    st.session_state.turn += 1
                    st.rerun()
            else:
                st.error("Could not read 3 choices from the model output.")

    # value of character section
    with col2:
        with st_yled.container(
            background_color="#0f172a",
            border_color="#38bdf8",
            padding="20px"
        ):
            st_yled.subheader("Value of Character",color="#38bdf8")
            st_yled.write(f"Name: {st.session_state.player_name}",color="#38bdf8")
            st_yled.write(f"HP: {st.session_state.HP}",color="#38bdf8")
            st_yled.write(f"Attack: {st.session_state.Attackpower}",color="#38bdf8")
            st_yled.write(f"Shield: {st.session_state.shield}",color="#38bdf8")
            st_yled.write(f"Special Ability: {st.session_state.specialability}",color="#38bdf8")
            st_yled.write(f"Inventory: {st.session_state.Inventory}",color="#38bdf8")

        st.write("")

        if st_yled.button("Restart", color="#cd2323"):
            restart_game()
            st.rerun()

            






























