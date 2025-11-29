# import libararies
import sqlite3
import pandas as pd                
import streamlit as st                           
import os
from dotenv import load_dotenv
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

      
# create sql database
class Constant:
    NameDatabase = "mymealtracker.db"
    ChildName = ["Essence", "Gabriella"]
    MealType = [ "Breakfast", "Lunch", "Dinner"]

def sql_connect():
    return sqlite3.connect(Constant.NameDatabase)

# Create Database --- 📈📊  
def createDatabase():
    if Constant.NameDatabase:
        
        conn = sqlite3.connect(Constant.NameDatabase)
        c = conn.cursor()
        
        c.execute(
        """
        CREATE TABLE IF NOT EXISTS meals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_timestamp TEXT,
            child_name TEXT,
            meal_type TEXT,
            food TEXT,
            amount_consumed INTEGER,
            care_giver TEXT)
            """
        )

        conn.commit()
        conn.close()
        
# Query -- 📖📗

def insert_query(event_timestamp, child_name, meal_type, food, amount_consumed, care_giver):
    conn = sql_connect()
    cursor = conn.cursor()
    
    insert_table = """
    INSERT INTO meals(event_timestamp, child_name, meal_type, food, amount_consumed, care_giver)
    VALUES(?, ?, ?, ?, ?, ?)
    """
    cursor.execute(insert_table, 
                   (event_timestamp, child_name, meal_type, food, amount_consumed, care_giver)
                   )
    conn.commit()
    conn.close()  
    
# Meals --🍇🍍🍎
def load_meals():
    conn = sql_connect()
    df = pd.read_sql_query("SELECT * FROM meals", conn)
    conn.close()
    
    if not df.empty:
        df["event_timestamp"] = pd.to_datetime(df["event_timestamp"], errors= "coerce")
    return df
           
# AI Recommendation ---- 🖲️💽🧑🏾‍💻

def get_recommendations(df, child_name=None, meal_type=None, min_percent=70, top_n=3):
    
    if df.empty:
        return pd.DataFrame()

    dfx = df[(df["child_name"] == child_name) & (df["meal_type"] == meal_type)]
    
    grouped = (
        dfx.groupby("food")["amount_consumed"]
        .mean()
        .reset_index()
        .rename(columns = {"amount_consumed":"avg_percent"})   
    )
    
    good = grouped[grouped["avg_percent"] >= min_percent]
    results = good.sort_values("avg_percent", ascending=False).head(top_n) 
    return results

# AI RECOMENDATION -- 📦☑️                   
def ai_recommendation(df, child_name, meal_type):
    
    # client = OpenAI()
    # client = OpenAI(api_key=st.secrets[OPENAI_API_KEY])
    client = OpenAI(api_key=OPENAI_API_KEY)
    st.header("AI Food Picker")
    
    if df.empty:
        st.info("No meal data yet. Log some meals first.")
        return
    
    # st.markdown("Make Meals Recommendation Based on the Most Food Eaten by Kiddos")
    
    # meal_type = st.selectbox(
    # "Meal Type", Constant.MealType,
    # )
    
    # child_name = st.selectbox(
    #             "Child's name",
    #             Constant.ChildName,
    #         )

    summary_df = get_recommendations(df,
                                       child_name=child_name, 
                                       meal_type= meal_type, 
                                       min_percent=70, 
                                       top_n=3
                                       )
    foods = summary_df["food"].tolist()

    if len(foods) == 0:
        st.info("Not enough data yet to make a recommendation for this child and meal type.")
        return

    elif len(foods) == 1:
        foods_str = foods[0]
    elif len(foods) == 2:
        foods_str = " and ".join(foods)
    else:
        foods_str = ", ".join(foods[:-1]) + f" and {foods[-1]}"


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
        model="gpt-4.1-mini",  
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=40,
    )

    return response.choices[0].message.content.strip()
     
        
# Streamlit set up -- 🚣🏾‍♀️🤽🏾‍♀️💦
def main():
    st.set_page_config(page_title="Kids Meals Database", page_icon="📝")
    
    createDatabase()
    
    st.title("Log Kid's Data")
    page = st.sidebar.radio(
        "Navigate",
        ["Log Meal", "History", "AI Recommendation"]
    )
    
    if page == "Log Meal":
        st.header("Log a Meal")
        
        with st.form("meal_form"):
            
            child_name = st.selectbox(
                "Child's name",
                Constant.ChildName,
            )
            meal_type = st.selectbox(
                "Meal Type",
                Constant.MealType,
            )
            food = st.text_area(
                "What did they eat?",
                "Pepperoni Pizza",
            )
            amount_consumed = st.slider(
                "About what percent of food did the kiddo eat?",
                min_value = 0,
                max_value = 100,
                value = 50,
                step = 5
            )
            care_giver = st.selectbox(
                "Care Giver Name",
                ["Gabriel", "Nahja"]
            )
            
            event_time = st.time_input("Time", datetime.now().time())
            event_date = st.date_input("Date", datetime.now().date()) 
            
            event_timestamp = datetime.combine(event_date, event_time)
            
            submitted = st.form_submit_button("Save Meal")
    
            # event_timestamp, child_name, meal_type, food, amount_consumed, care_giver
            
            if submitted:
                insert_query(
                    event_timestamp = event_timestamp.isoformat(),
                    child_name=child_name,
                    meal_type=meal_type,
                    food=food.strip(),
                    amount_consumed=float(amount_consumed),
                    care_giver = care_giver,
                )
                st.success("Meal saved ✅")
    
    elif page == "History":
        st.header("Meal History")

        df = load_meals()
        if df.empty:
            st.info("No meals logged yet.")
        else:
            kids = ["All"] + sorted(df["child_name"].dropna().unique().tolist())
            kid_filter = st.selectbox("Filter by child", kids)

            if kid_filter != "All":
                df = df[df["child_name"] == kid_filter]

            meal_types = ["All"] + sorted(
                df["meal_type"].dropna().unique().tolist()
            )
            meal_filter = st.selectbox("Filter by meal type", meal_types)

            if meal_filter != "All":
                df = df[df["meal_type"] == meal_filter]

            # Date range filter
            if not df["event_timestamp"].isna().all():
                min_date = df["event_timestamp"].min().date()
                max_date = df["event_timestamp"].max().date()
                start_date, end_date = st.date_input(
                    "Filter by date range",
                    value=(min_date, max_date),
                )
                mask = (df["event_timestamp"].dt.date >= start_date) & (
                    df["event_timestamp"].dt.date <= end_date
                )
                df = df[mask]

            df_show = df.sort_values("event_timestamp", ascending=False)
            st.dataframe(df_show)

            # Optional: export to CSV
            csv = df_show.to_csv(index=False)
            st.download_button(
                "Download as CSV",
                data=csv,
                file_name="meals_history.csv",
                mime="text/csv",
            )
            
    elif page == "AI Recommendation":
        
        st.header("AI Recommendation")

        data = load_meals()
        
        if data.empty:
            st.info("No meal data yet. Log some meals first.")
            st.stop()

        # Step 1 — Select child
        child_name = st.selectbox(
            "Select Child",
            Constant.ChildName
        )

        # Step 2 — Select meal type
        meal_type = st.selectbox(
            "Select Meal Type",
            Constant.MealType
        )

        # Step 3 — Button to generate recommendation
        if st.button("Get AI Suggestion"):
            with st.spinner("Thinking... 🤔🧠"):
                reply = ai_recommendation(
                    data, 
                    child_name=child_name, 
                    meal_type=meal_type
                )

                if reply:
                    st.subheader("AI Suggestion")
                    st.write(reply)
        else:
            st.info("Select the child + meal type, then click the button.")
                    
        
if __name__ == "__main__":
    main()
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    