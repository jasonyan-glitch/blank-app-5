import streamlit as st
import st_yled
from openai import OpenAI


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

if "choices" not in st.session_state:
    st.session_state.choices = []

if "turn" not in st.session_state:
    st.session_state.turn = 0

if "last_result" not in st.session_state:
    st.session_state.last_result = ""

if "generated" not in st.session_state:
    st.session_state.generated = False

if st.session_state.started == False: 
    with st_yled.container (
        background_color = "#0e1f39d3",
        padding="30px"
    ) :
        name=st_yled.text_input("Your name",color="#2079ff")
        if st_yled.button("Start",color= "#418cfc"):
            if not name:
                st.warning("Name!!!Please")
            else: 
                st.session_state.name = name
                st.session_state.started = True

if st.session_state.started == True and not st.session_state.generated:
    system=f""" 
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
        {"role": "system", "content": system}
    ]

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages
    )

    text = response.choices[0].message.content

    #from AI
    bg = text.split("background:")[1].split("choice:")[0]
    c = text.split("choice:")[1]

    st.session_state.chat_history.extend([
        {"role": "system", "content": system},
        {"role": "assistant", "content": text}
    ])
    
    with st_yled.container (
        background_color = "#0c4498d2",
        padding="30px"
    ) :
        st.title("Background/first round")
        st_yled.write(bg,color="#80dd0ed2")
    with st_yled.container (
        background_color = "#0462f0d2",
        padding="40px"
    ):
        
        ch=c.split("\n")
        cho=[
            ch[1],
            ch[2],
            ch[3]
        ] 

        choice = st.radio(
            "Choose your action:",
            cho,
            key="choice_0"
        )

        if st_yled.button("Generate"):
            if not choice:
                st.warning("Enter your choices:")
            else:
                st.session_state.choices = choice
                st.session_state.chat_history.append(
                    {"role": "user", "content": f"I choose: {choice}"}
                )
                st.session_state.turn += 1
                st.session_state.generated = True
        
if st.session_state.turn >=1 :
    follow_up= f""" 
        You are the Game Master resolving the player's chosen action based on the story so far.

        You MUST:
        1) Read:{st.session_state.chat_history}.
        2) Read the player's selected choice:({st.session_state.choices}).
        3) Describe what happens next briefly.
        4) Update the player's stats (HP, Attackpower, shield) if needed.
        5) Then present the NEXT SCENE AND exactly THREE new choices.
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

        Information(All the detail): {st.session_state.chat_history}

        Player choice:{st.session_state.choices}

        Resolve the choice and continue.
    """
    messages1 = [
        {"role": "system", "content": follow_up},
        {"role": "user", "content": user_message}
    ]

    response1 = client.chat.completions.create(
        model="gpt-4o",
        messages=messages1
    )

    text1 = response1.choices[0].message.content
    
    #these two from openAI
    result = text1.split("result:")[1].split("status_update:")[0].strip().strip('"')
    status1 = text1.split("status_update:")[1].split("next_background:")[0]
    
    
    bg1 = text1.split("next_background:")[1].split("choice:")[0]
    c1 = text1.split("choice:")[1]

    
    st.session_state.chat_history.append({"role": "assistant", "content": text1})
    
    col1, col2 = st.columns(2)
    with col1:
        with st_yled.container (
            background_color = "#521cc9bd",
            padding="30px"
        ) :
            st.title("Plot")
            st_yled.write(bg1,color="#76dd0eae")
        
        with st_yled.container (
            background_color = "#521cc9bd",
            padding="30px"
        ) :
            st.title("Choices")
            ch1=c1.split("\n")
            choice_lines = c1.split("\n")
            cho1 = []

            for line in choice_lines:
                line = line.strip()
                if line.startswith("1.") or line.startswith("2.") or line.startswith("3."):
                    cho1.append(line[2:].strip().replace('"', ""))

            choice1 = st.radio(
                "Choose your action:",
                cho1,
                key=f"choice_{st.session_state.turn}"
                )
    with col2:
        with st_yled.container (
            background_color = "#3f1cc9bb",
            padding="30px"
        ) :
            st.title("status")
            st_yled.write(f"Name: {st.session_state.player_name}",color="#38bdf8")
            st_yled.write(f"HP: {st.session_state.HP}",color="#38bdf8")
            st_yled.write(f"Attack: {st.session_state.Attackpower}",color="#38bdf8")
            st_yled.write(f"Shield: {st.session_state.shield}",color="#38bdf8")
            st_yled.write(f"Special Ability: {st.session_state.specialability}",color="#38bdf8")
            st_yled.write(f"Inventory: {st.session_state.Inventory}",color="#38bdf8")
            
        if st_yled.button("Choose"):
            if not choice1:
                st.warning("Enter your choices:")
            else:
                st.session_state.turn +=1
                st.session_state.choices = choice1
                st.session_state.chat_history.append({"role": "user", "content": f"I choose: {choice1}"})
    
                    












