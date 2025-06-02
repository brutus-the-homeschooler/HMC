
import streamlit as st
import pandas as pd
st.markdown("""
    <style>
    body {
        background-image: url("https://i.imgur.com/I2OijBf.png");
        background-size: cover;
        background-attachment: fixed;
        background-repeat: no-repeat;
        background-position: center;
    }
    </style>
""", unsafe_allow_html=True)

# Load data
ratings = pd.read_csv("ratings.csv")
metadata = pd.read_csv("metadata.csv", encoding="ISO-8859-1")
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
unlocked_users = ratings[ratings['unlock'] == 1]['username'].unique()

selected_user = st.selectbox("Select a user", unlocked_users)

# Join and filter merged dataframe for selected user
user_df = df[df['username'] == selected_user]
# Get the current (latest) movie from metadata
current_movie = metadata.loc[metadata['movie_id'].idxmax()]

# Display "Our Next Movie" section
st.markdown("## 🍿 Our Next Movie Is...")
st.image(current_movie['poster_url'], width=300)
st.markdown(f"### **{current_movie['official_title']}**")
st.markdown(f"**Synopsis:** _{current_movie['synopsis']}_")

# Links
# Links as Markdown
st.markdown(
    f"[🎬 IMDb]({current_movie['imdb_url']}) &nbsp;&nbsp;|&nbsp;&nbsp; [📚 Wikipedia]({current_movie['wiki_url']})",
    unsafe_allow_html=True
)

# Embed YouTube trailer
st.video(current_movie["trailer_url"])


prediction_placeholder = st.empty()  # Reserve a space for prediction text

# Score calculations
q1 = user_df['score'].quantile(0.25)
q2 = user_df['score'].mean()
q3 = user_df['score'].quantile(0.75)

def closest_movie_to(value):
    return user_df.iloc[(user_df['score'] - value).abs().argsort()[:1]]

for label, quantile in [("Q1", q1), ("Q2", q2), ("Q3", q3)]:
    movie = closest_movie_to(quantile).iloc[0]
    friendly_labels = {
    "Q1": "👎 Lower-Rated Benchmark",
    "Q2": "🤷 Middle-Rated Benchmark",
    "Q3": "👍 Higher-Rated Benchmark"
}

    st.subheader(f"{friendly_labels[label]}: {movie['official_title']} ({movie['year']})")

    st.image(movie['poster_url'], width=200)
    st.markdown(f"**Director:** {movie['director']}")
    st.markdown(f"**RT Score:** {movie['rt_score']}%")
    st.markdown(f"**Synopsis:** _{movie['synopsis']}_")
    st.markdown(f"[IMDb]({movie['imdb_url']}) | [Wikipedia]({movie['wiki_url']})")
    st.radio(f"Do you think this week's movie is better than *{movie['official_title']}*?", ["Yes", "No"], key=label)
# Capture user answers from radios
q1_answer = st.session_state["Q1"]
q2_answer = st.session_state["Q2"]
q3_answer = st.session_state["Q3"]

# Use the reserved placeholder to display at the top
prediction_placeholder.markdown("### 🧠 Predicted Score Range")

if "Q1" in st.session_state and "Q2" in st.session_state and "Q3" in st.session_state:
    q1_answer = st.session_state["Q1"]
    q2_answer = st.session_state["Q2"]
    q3_answer = st.session_state["Q3"]

    if q1_answer == "No":
        prediction = f"Less than {q1:.1f}"
    elif q1_answer == "Yes" and q2_answer == "No":
        prediction = f"Between {q1:.1f} and {q2:.1f}"
    elif q2_answer == "Yes" and q3_answer == "No":
        prediction = f"Between {q2:.1f} and {q3:.1f}"
    elif all(ans == "Yes" for ans in [q1_answer, q2_answer, q3_answer]):
        prediction = f"Greater than {q3:.1f}"
    else:
        prediction = "Unable to predict based on your answers."

    prediction_placeholder.markdown(
        f"Based on your answers, we think this week's movie score will be: **{prediction}**"
    )

with st.sidebar:
    st.markdown("## 🎬 Your Ratings")

    if not user_df.empty:
        for _, row in user_df.sort_values(by="score", ascending=False).iterrows():
            st.markdown(f"- **{row['official_title']}** {row['score']}")
    else:
        st.markdown("No ratings found.")

    # Divider
    st.markdown("---")

    # Collapsible section for all movies
    with st.expander("📚 Show All Movies", expanded=False):
        for _, row in metadata.sort_values("movie_id").iterrows():
            st.image(row["poster_url"], width=200, height=350)
            st.markdown(f"**{row['official_title']}**")
        
        # Conditional link builder
            links = f"[IMDb]({row['imdb_url']}) | [Wikipedia]({row['wiki_url']})"
            if pd.notna(row.get("osu_library_link")) and row["osu_library_link"].strip() != "":
                links += f" | [📚 OSU Library]({row['osu_library_link']})"

            st.markdown(links)
            st.markdown("---")


