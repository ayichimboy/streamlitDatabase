# Import Libraries

import streamlit as st   
import numpy as np              
import pandas as pd                   
import matplotlib.pyplot as plt         
from dotenv import load_dotenv
import os          
from datetime import datetime 
from openai import OpenAI

load_dotenv()

# Check ENV variables

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ----------------------------------------
if OPENAI_API_KEY:
    print("Key Successfully Loaded ✅")
else:
    print("Key Not Loaded Successfully 😔")
    
# ------------------------------------- 
# This function will do ...

def get_recommendations(df,child_name=None, meal_type= None, min_perecent=70, top_n=3):
    
    if df.empty():
        return pd.DataFrame()

    dfx = df[(df["child_name"] == child_name) & (df["meal_type"] == meal_type)]
    
    grouped = (
        dfx.groupby("food")["amount_consumed"]
        .mean()
        .reset_index()
        .rename(columns = {"amount_consumed":"avg_percent"})   
    )
    
    good = grouped[grouped["avg_percent"] >= min_perecent]
    
    results = good.sort_values("avg_percent", ascending=False).head(top_n) 
    
    return results


def ai_recommendation(df):
    
    client = OpenAI()
    # client = OpenAI(api_key=st.secrets[OPENAI_API_KEY])
    st.header("AI Food Picker")
    
    if df.empty:
        st.info("No meal data yet. Log some meals first.")
        return
    
    query = st.write(
    "Make Meals Recommendation Based on the Most Food Eaten by Kiddo"
    )
    meal_type = st.selectbox(
    "Meal Type", Constant.MealType,
    )
    child_name = st.selectbox(
                "Child's name",
                Constant.ChildName,
            )

    summary_list = get_recommendations(df,child_name=child_name, meal_type= meal_type, min_perecent=70, top_n=3)
    
    foods_str = ", ".join(summary_list[:-1]) + f" and {summary_list[-1]}"

    prompt = f"""
    You are a helpful assistant.

    Return ONE short sentence recommending these foods for a meal.

    Meal type: {meal_type}
    Foods: {foods_str}

    Rules:
    - Answer with ONE sentence only.
    - Do not add extra explanation.
    """

    response = client.chat.completions.create(
        model="gpt-4.1-mini",  # or "chatgpt-mini" depending on your setup
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=40,
    )

    return response.choices[0].message.content.strip()

with st.spinner("Thinking..."):
    

        reply = ai_recommendation(df)

        st.subheader("AI Suggestion")
        st.write(reply)

#