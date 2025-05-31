
import streamlit as st
import pandas as pd

# Load data
ratings = pd.read_csv("ratings.csv")
metadata = pd.read_csv("metadata.csv")
df = ratings.merge(metadata, on="movie_id")

# Custom spooky CSS
st.markdown("""
    <style>
    body {
        background-image: url('https://www.transparenttextures.com/patterns/dark-mosaic.png');
        background-size: cover;
        color: #FF4444;
    }
    h1 {
        font-family: 'Creepster', cursive;
        font-size: 4em;
        text-shadow: 2px 2px 4px #000000;
    }
    @import url('https://fonts.googleapis.com/css2?family=Creepster&display=swap');
    </style>
""", unsafe_allow_html=True)

# App title
st.markdown("<h1>🩸 Horror Movie Club 🧟</h1>", unsafe_allow_html=True)

# User selector
users = df['username'].unique()
selected_user = st.selectbox("Select a user", users)
user_df = df[df['username'] == selected_user]

# Score calculations
q1 = user_df['score'].quantile(0.25)
q2 = user_df['score'].mean()
q3 = user_df['score'].quantile(0.75)

def closest_movie_to(value):
    return user_df.iloc[(user_df['score'] - value).abs().argsort()[:1]]

for label, quantile in [("Q1", q1), ("Q2", q2), ("Q3", q3)]:
    movie = closest_movie_to(quantile).iloc[0]
    st.subheader(f"{label} Benchmark Movie: {movie['official_title']} ({movie['year']})")
    st.image(movie['poster_url'], width=200)
    st.markdown(f"**Director:** {movie['director']}")
    st.markdown(f"**RT Score:** {movie['rt_score']}%")
    st.markdown(f"**Synopsis:** _{movie['synopsis']}_")
    st.markdown(f"[IMDb]({movie['imdb_url']}) | [Wikipedia]({movie['wiki_url']})")
    st.radio(f"Is this week's movie better than the {label} movie?", ["Yes", "No"], key=label)
