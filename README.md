## SQL quiz app

an application designed to support students with their SQL exam preparation :) 

<br>

this is a streamlit web app, that:
- accepts an SQLite database file
- allows the user to select a handful of SQL query topics they would like to be tested on
- generates a quiz of questions based on their specific database schema and data
- marks the user's answers, and generates specific feedback when the user was wrong

<br>

the app uses:
- streamlit for UI
- huggingface to provide a model (API key required from user) & langchain to handle prompts and outputs from the model
- sqlalchemy to handle database interactions (currently only sqlite supported)
- .toml configuration files

<br>

ways to run/use this app:
- fork/clone it! and use `streamlit run app.py` in the terminal
- streamlit community cloud! -> [\[link\]](https://sql-quiz-app.streamlit.app/)
- others TBC...

<br>

it was built using python version 3.11.4

### note

*none* of this code was 'vibe-coded' / ai-generated! (it's the result of many painful hours spent on stackoverflow and sqlalchemy docs)

if you happen to try it and encounter any bugs, let me know!
