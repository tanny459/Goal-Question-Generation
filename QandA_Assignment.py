import streamlit as st
import pandas as pd
import openai
import json

# Set your OpenAI API key
openai.api_key = ['Provide your key here']

# Load user info from CSV
user_info = pd.read_csv('user_info.csv')

def create_account(user_info):
    st.subheader("Create Account")
    username = st.text_input("Enter username:")
    password = st.text_input("Enter password:", type="password")
    if st.button("Create Account"):
        if username in user_info['User_Name'].values:
            st.error("Username already taken. Please choose a different name.")
        else:
            # Update user_info
            new_user = pd.DataFrame({'User_Name': [username], 'Password': [password], 'GoalNQuestions': [{}]})
            user_info = user_info.append(new_user, ignore_index=True)
            user_info.to_csv('user_info.csv', index=False)
            st.success("Account created successfully! Please log in.")
    return user_info
    
def login(user_info):
    st.subheader("Log In")
    username = st.text_input("Enter username:")
    password = st.text_input("Enter password:", type="password")
    if st.button("Log In"):
        user = user_info[(user_info['User_Name'] == username) & (user_info['Password'] == password)]
        if not user.empty:
            st.session_state['user_authenticated'] = True
            st.session_state['username'] = username
            st.success(f"Welcome, {username}!")
            goals = user['GoalNQuestions'].iloc[0]
            if goals:
                options = st.selectbox("Choose an option:", ["View Previous Goals", "Set New Goal"])
                if options == "View Previous Goals":
                    view_previous_goals(user)
                elif options == "Set New Goal":
                    set_new_goal(user_info, user)
            else:
                st.info("No previous goals found.")
                if st.button("Set New Goal"):
                    set_new_goal(user_info, user)
        else:
            st.error("Invalid username or password.")

def view_previous_goals(user):
    goals = eval(user['GoalNQuestions'].iloc[0])
    if goals:
        st.subheader("Previous Goals:")
        for goal, questions in goals.items():
            st.write(f"**Goal:** {goal}")
            st.write("**Questions Generated:**")
            for i, question in enumerate(questions, start=1):
                st.write(f"{i}. {question}")

    else:
        st.info("No previous goals found.")

def set_new_goal(user):
    st.subheader("Set New Goal")
    goal = st.text_area("Enter your goal for the survey:", height=100)
    if st.button("Generate Survey Questions"):
        goals_dict = eval(user['GoalNQuestions'].iloc[0])
        if goal in goals_dict:
            confirm_option = st.radio("This goal is already present in the database. Do you want to continue?", ("Go ahead", "Abort"))
            if confirm_option == "Abort":
                st.info("Please enter a new goal.")
                return
        st.success("New goal set successfully!")
        llm_response = getLLMResponse("gpt-4-1106-preview", 4096, goal)
        
        # Display the generated survey questions
        st.info("Questions based on Goal:-")
        if llm_response:
            st.subheader("Generated Survey Questions:")
            questions_with_scores = [f"{question} (Score: {score})" for question, score in llm_response.items()]
            for i, question_with_score in enumerate(questions_with_scores, start=1):
                st.write(f"{i}. {question_with_score}")

        # Update user_info
        st.info("Updating the database with goal and its questions!!!!")
        user_index = user.index[0]
        current_questions = eval(user_info.at[user_index, 'GoalNQuestions'])
        current_questions[goal] = questions_with_scores
        user_info.at[user_index, 'GoalNQuestions'] = current_questions
        user_info.to_csv('user_info.csv', index=False)

def getLLMResponse(model_name, output_token_limit, Context_goal):
    content = str(Context_goal) 
    
    sys_role_description = "You are an excellent Question Generation model. Your task is to create question based on the goals set by the user."
    
    user_prompt =  "You are provided goal from users which can be(product managers, user researchers, market researchers, SMB owners etc) and returns a dictionary of questions for a survey that will help reach the goal and aslo provide the relevance score(The metric to calculate the Relevance of the question woth respect to goal) to each question based on the goal.\n\n#### Exaple Goal ####\nConduct a quarterly survey of 100 financial services decision-makers to gather insights for product development.\n\n#### Question Generated of Above Goal ####\n{'What factors influence your decision-making process when considering financial services products?': 90, 'How satisfied are you with the current range of financial services products available in the market?': 76, 'What improvements would you like to see in financial services products in the future?': 44, 'How frequently do you engage with financial services products on a quarterly basis?': 78, 'Which aspects of financial services products are most important to you when making a purchasing decision?': 69}\n\n#### Important Instructions ####\nGenerated question must be proper and meainingful.\nYou can generate maximum of 20 questions, but question must cover every expect of the mentioned goal by the user.\nDo not use Apostrophe(') while generating the questions.\nDon't attach extra text in the output and only give the sub-sections.\nDon't attach extrta text or information in the output list just strictly follow the output format."+ Context_goal
    
    conversation = [{"role": "system", "content": sys_role_description}, {"role": "user", "content": user_prompt}]
    response = openai.ChatCompletion.create(
    model=model_name,
    messages = conversation,
    temperature=0,
    max_tokens=output_token_limit,
    top_p=0)
    
    survey_questions = response['choices'][0]['message']['content']
    print("survey_questions: ", survey_questions)
    survey_questions = eval(survey_questions)
    
    return survey_questions

def main():
    st.set_page_config(page_title="Survey Question Generator", page_icon=":clipboard:", layout="wide")

    st.title("Survey Question Generator")

    user_info = pd.read_csv('user_info.csv')

    if 'user_authenticated' not in st.session_state:
        st.session_state['user_authenticated'] = False

    if st.session_state['user_authenticated']:
        username = st.session_state['username']
        st.success(f"Welcome back, {username}!")
        user = user_info[user_info['User_Name'] == username]
        goals = user['GoalNQuestions'].iloc[0]
        if goals:
            options = st.selectbox("Choose an option:", ["View Previous Goals", "Set New Goal"])
            if options == "View Previous Goals":
                view_previous_goals(user)
            elif options == "Set New Goal":
                set_new_goal(user)
        else:
            st.info("No previous goals found.")
            if st.button("Set New Goal"):
                set_new_goal(user)
    else:
        login_or_create_account(user_info)

def login_or_create_account(user_info):
    st.subheader("Log In or Create Account")
    login_option = st.selectbox("Choose an option:", ["Log In", "Create Account"])
    
    if login_option == "Log In":
        login(user_info)
    elif login_option == "Create Account":
        create_account(user_info)

if __name__ == "__main__":
    main()

