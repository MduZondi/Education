import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from PIL import Image
import json
import re
import random

# Set up Streamlit
st.set_page_config(page_title='PersonaLearn: Your Personalized Learning Assistant', page_icon='🧠', layout="wide")

# Custom CSS for a dark purple theme
st.markdown("""
    <style>
    .stApp {
        background-color: #2A0A29;
        color: #FFFFFF;
    }
    .stButton>button {
        color: #FFFFFF;
        background-color: #6A0DAD;
        border-radius: 5px;
    }
    .stTextInput>div>div>input {
        color: #FFFFFF;
        background-color: #3D1A3D;
    }
    .stTextArea>div>div>textarea {
        color: #FFFFFF;
        background-color: #3D1A3D;
    }
    </style>
    """, unsafe_allow_html=True)

# Header with logo
logo_path = os.path.join("c:/Users/Nkululeko Luthuli/Documents", "Translogo.png")
if os.path.exists(logo_path):
    logo = Image.open(logo_path)
    col1, col2 = st.columns([1, 5])
    with col1:
        st.image(logo, width=100)
    with col2:
        st.title('PersonaLearn: Your Personalized Learning Assistant 🧠')
else:
    st.title('PersonaLearn: Your Personalized Learning Assistant 🧠')

# Initialize session state
if 'user_info' not in st.session_state:
    st.session_state.user_info = {}
if 'learning_topic' not in st.session_state:
    st.session_state.learning_topic = ""
if 'personalized_content' not in st.session_state:
    st.session_state.personalized_content = ""
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'quiz_questions' not in st.session_state:
    st.session_state.quiz_questions = []
if 'quiz_score' not in st.session_state:
    st.session_state.quiz_score = 0
if 'current_question' not in st.session_state:
    st.session_state.current_question = 0
if 'wrong_answers' not in st.session_state:
    st.session_state.wrong_answers = []

# API Key Input
google_api_key = st.text_input("Enter your Google API Key to start:", type="password")

# Initialize the ChatGoogleGenerativeAI model
if google_api_key:
    llm = ChatGoogleGenerativeAI(model='gemini-pro', google_api_key=google_api_key)

# Function to gather user information
def gather_user_info():
    st.subheader("Let's get to know you better!")
    if 'personal_info' not in st.session_state.user_info:
        answer = st.text_area("Tell me about your favorite hobby or interest. What makes it special to you?", key='personal_info')
        if answer:
            st.session_state.user_info['personal_info'] = answer
            st.success("Great! Thanks for sharing. Let's start learning!")
        else:
            st.stop()

# Function to generate personalized learning content
def generate_personalized_content(topic, user_info):
    prompt = f"""
    You are an expert educator specialized in creating personalized learning experiences. 
    Your task is to explain topics using analogies and examples that relate to the learner's interests, 
    experiences, and emotions. Make the content engaging, memorable, and easy to understand.

    Explain the following topic: {topic}
    
    Use this information about the learner to create personalized analogies and explanations:
    
    {user_info['personal_info']}
    
    Provide a comprehensive explanation of the topic, using analogies and examples that relate to the learner's interests, experiences, and emotions.
    """
    
    with st.spinner('Generating personalized learning content...'):
        response = llm.invoke(prompt)
        content = response.content
    
    st.session_state.chat_history.append(("assistant", content))
    return content

def generate_quiz_questions(topic, content, difficulty, num_questions):
    prompt = f"""
    Based on the following learning content about {topic}, create a quiz with {num_questions} multiple-choice questions. 
    Each question should have 4 options with only one correct answer. 
    The difficulty level should be {difficulty}.
    Format the output as a JSON string representing a list of dictionaries, where each dictionary represents a question with the following keys:
    - 'question': The question text
    - 'options': A list of 4 possible answers
    - 'correct_answer': The index of the correct answer (0-3)

    Learning content:
    {content}

    Generate the quiz questions and return them as a valid JSON string without any markdown formatting:
    """

    with st.spinner('Generating quiz questions...'):
        try:
            response = llm.invoke(prompt)

            # Remove any unexpected formatting (e.g., markdown code blocks)
            json_string = re.sub(r'^```json\s*|\s*```$', '', response.content.strip())
            json_string = re.sub(r'`+', '', json_string)  # Remove stray backticks
            json_string = re.sub(r'(?<!: )"(\w+)"(?=\s*:)', r'"\1"', json_string)  # Ensure keys are quoted correctly

            # Try to parse the response as JSON
            quiz_questions = json.loads(json_string)

            # Validate the structure of the quiz questions
            if not isinstance(quiz_questions, list) or len(quiz_questions) != num_questions:
                raise ValueError(f"Invalid quiz structure: expected a list of {num_questions} questions")

            for q in quiz_questions:
                if not all(key in q for key in ['question', 'options', 'correct_answer']):
                    raise ValueError("Invalid question structure: missing required keys")
                if not isinstance(q['options'], list) or len(q['options']) != 4:
                    raise ValueError("Invalid options: expected a list of 4 options")
                if not isinstance(q['correct_answer'], int) or q['correct_answer'] not in range(4):
                    raise ValueError("Invalid correct_answer: expected an integer 0-3")

                # Randomize the position of the correct answer
                correct_index = q['correct_answer']
                options = q['options']
                random.shuffle(options)
                q['correct_answer'] = options.index(q['options'][correct_index])
                q['options'] = options

            return quiz_questions
        except json.JSONDecodeError as e:
            st.error(f"Failed to parse quiz questions as JSON. Error: {str(e)}")
        except ValueError as e:
            st.error(f"Invalid quiz structure. Error: {str(e)}")
        except Exception as e:
            st.error(f"An unexpected error occurred: {str(e)}")

        st.error("Failed to generate valid quiz questions. Please try again.")
        return []

# Function to display and handle quiz
def run_quiz():
    if st.session_state.current_question < len(st.session_state.quiz_questions):
        question = st.session_state.quiz_questions[st.session_state.current_question]
        st.subheader(f"Question {st.session_state.current_question + 1}")
        st.write(question['question'])
        
        answer = st.radio("Choose your answer:", question['options'], key=f"q_{st.session_state.current_question}")
        
        if st.button("Submit Answer"):
            if question['options'].index(answer) == question['correct_answer']:
                st.success("Correct! Well done!")
                st.session_state.quiz_score += 1
            else:
                st.error(f"Sorry, that's not correct. The right answer is: {question['options'][question['correct_answer']]}")
                st.session_state.wrong_answers.append((question['question'], question['options'][question['correct_answer']]))
            
            st.session_state.current_question += 1
            st.rerun()
    else:
        st.success(f"Quiz completed! Your score: {st.session_state.quiz_score}/{len(st.session_state.quiz_questions)}")
        if st.session_state.wrong_answers:
            st.markdown("### Solutions to Incorrect Answers")
            for q, correct_answer in st.session_state.wrong_answers:
                st.write(f"**Question:** {q}")
                st.write(f"**Correct Answer:** {correct_answer}")
        if st.button("Restart Quiz"):
            st.session_state.current_question = 0
            st.session_state.quiz_score = 0
            st.session_state.wrong_answers = []
            st.rerun()

# Menu
menu = ["Home", "Learn", "Quiz", "Chat History"]
choice = st.sidebar.selectbox("Menu", menu)

if choice == "Home":
    st.subheader("Welcome to PersonaLearn!")
    st.write("Select 'Learn' from the menu to start your personalized learning journey.")

elif choice == "Learn":
    gather_user_info()

    if 'personal_info' in st.session_state.user_info:
        st.session_state.learning_topic = st.text_input("What would you like to learn about today?")
        
        if st.session_state.learning_topic and st.button("Generate Personalized Learning Content"):
            st.session_state.personalized_content = generate_personalized_content(st.session_state.learning_topic, st.session_state.user_info)
            st.markdown("## Your Personalized Learning Content")
            st.write(st.session_state.personalized_content)
            
        if st.session_state.personalized_content:
            # Option to ask follow-up questions
            follow_up = st.text_input("Any follow-up questions?")
            if follow_up and st.button("Get Answer"):
                st.session_state.chat_history.append(("human", follow_up))
                
                follow_up_prompt = f"""
                Based on the previous explanation and the user's personal information, answer the following follow-up question:
                
                Question: {follow_up}
                
                User's interest: {st.session_state.user_info['personal_info']}
                
                Provide a detailed answer, continuing to use personalized analogies and examples.
                Previous context:
                {st.session_state.chat_history[-2][1]}
                """
                
                with st.spinner('Generating answer...'):
                    response = llm.invoke(follow_up_prompt)
                    answer = response.content
                
                st.session_state.chat_history.append(("assistant", answer))
                st.write(answer)

elif choice == "Quiz":
    if st.session_state.personalized_content:
        if not st.session_state.quiz_questions:
            st.markdown("### Quiz Settings")
            
            # Allow user to select quiz difficulty
            difficulty = st.selectbox("Select quiz difficulty:", ["Easy", "Medium", "Hard"], key="quiz_difficulty")
            
            # Allow user to set the number of questions
            num_questions = st.slider("Select the number of questions:", min_value=3, max_value=20, value=5, key="quiz_num_questions")
            
            if st.button("Generate Quiz"):
                # Generate quiz questions based on the selected difficulty and number of questions
                st.session_state.quiz_questions = generate_quiz_questions(st.session_state.learning_topic, st.session_state.personalized_content, difficulty, num_questions)
                st.session_state.current_question = 0
                st.session_state.quiz_score = 0
                st.session_state.wrong_answers = []
        
        if st.session_state.quiz_questions:
            st.markdown("## Quiz Time!")
            st.write("Let's test your understanding with a quick quiz.")
            run_quiz()
    else:
        st.warning("Please generate learning content first before taking the quiz.")

elif choice == "Chat History":
    st.subheader("Conversation History")
    for role, message in st.session_state.chat_history:
        if role == "human":
            st.write("You:", message)
        else:
            st.write("Assistant:", message)

# Reset button
if st.sidebar.button("Start Over"):
    st.session_state.user_info = {}
    st.session_state.learning_topic = ""
    st.session_state.personalized_content = ""
    st.session_state.chat_history = []
    st.session_state.quiz_questions = []
    st.session_state.quiz_score = 0
    st.session_state.current_question = 0
    st.session_state.wrong_answers = []
    st.rerun()
