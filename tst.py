import streamlit as st
import st_yled

# Initialize styling - set for each app page
st_yled.init()

# Style all buttons globally with a lightblue background
st_yled.set("button", "background_color", "lightblue")

# Use enhanced elements to style the (text) color of a single button
st_yled.button("Styled Button", color="white")

# Or the color of the title
st_yled.title("Welcome!", color="#331ac3ff")

# Add st_yled components - like a badge card
st_yled.badge_card_one(
    badge_text="New",
    badge_icon=":material/star:",
    title="Featured Item",
    text="Check out this amazing feature",
)