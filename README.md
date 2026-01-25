## SQL quiz app!
an application designed to support ijc212 students with their exam preparation :) 

~~ignore the fact I didn't complete nor deploy the app in time for the exam...~~

<br>

this is a streamlit web app, that:
- accepts an SQLite database file
- allows the user to select a handful of SQL query topics they would like to be tested on
- generates a quiz of questions based on their specific database schema and data
- marks the user's answers, and generates specific feedback when the user was wrong

<br>

the app uses:
- streamlit for UI
- huggingface to provide a model (API key required from user)
- langchain to handle prompts and outputs from the model
- .toml configuration files

<br>

**TBC** ways to run this app:
- fork it! and use `streamlit run app.py` in the terminal
- docker!
- streamlit community cloud [link]
- huggingface spaces [link]

<br>

*none* of this code is ai-generated / 'vibe-coded'! (it's just a result of many painful hours scrolling through stackoverflow and streamlit documentation)
