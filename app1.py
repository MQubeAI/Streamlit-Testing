import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
import streamlit as st
import openai
import speech_recognition as sr
from llama_index.llms.openai import OpenAI
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
import time
import os
from dotenv import load_dotenv

load_dotenv()
# Set up Streamlit app
st.set_page_config(page_title="FenerGPT", page_icon="images/Fener_logo.png", layout="wide", initial_sidebar_state="auto", menu_items=None)

OPENAI_API_KEY= os.getenv("OPENAI_API_KEY")

# Voice-to-Text Functionality

def record_and_convert_to_text(language_code):
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        # st.write("Listening...")
        audio = recognizer.listen(source)
        try:
            text = recognizer.recognize_google(audio, language=language_code)
            # st.write(f"You said: {text}")
            return text
        except sr.UnknownValueError:
            st.write("Google Speech Recognition could not understand the audio.")
            return ""
        except sr.RequestError as e:
            st.write(f"Could not request results from Google Speech Recognition service; {e}")
            return ""


# Load and authenticate user
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)
    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days'],
        config['preauthorized']
    )

    name, authentication_status, username = authenticator.login()

    if authentication_status:
        col1,col2 = st.sidebar.columns(2)
        s = f"<h1 style='font-size:32px;'>FenerGPT</h1>"
        with col1:
            st.image("images/Fener_logo.png",width=100)
        with col2:
            # st.title("FenerGPT")
            st.markdown(s, unsafe_allow_html=True)
        st.sidebar.divider()

        authenticator.logout('Logout', 'sidebar')
        st.sidebar.write(f'Welcome *{name}*')



        # tab1, tab2, tab3 = st.sidebar.tabs(["Home", "About", "Contact"])

        player_detail_opt = st.sidebar.radio(
            "Player Detail:",
            ["Manual Input","Passport"],
            captions=[
                "Provide all the player input manually",
                "Upload the Player passport",
            ],
            index=0,
        )

        st.title("Player Contract AI Bot")

        if "messages" not in st.session_state.keys():  # Initialize the chat messages history
            st.session_state.messages = [
                {
                    "role": "assistant",
                    "content": "Welcome, FenerGPT AI is ready to draft a player contract.",
                }
            ]

        @st.cache_resource(show_spinner=False)
        def load_data():
            reader = SimpleDirectoryReader(input_dir="data/", recursive=True)
            docs = reader.load_data()
            Settings.llm = OpenAI(
                model="gpt-3.5-turbo",
                temperature=0.2,
                system_prompt="""You are an expert on 
                the Player contract generation for Fenerbahçe Football Club. This Contract contains the principles and defines the legal relationship between the Player and Club.
                Following Important Inputs: \n
                1. Name of the Player: Can be Annonymous if user ask to fill it later. \n
                2. Contract starting date and ending date: (contract ending date should be stg 31.5.202X we can do it during demo) (contract starting date should be before ending date… we can put some controls like this) (contract ending date cannot be after 5 years from starting date. FIFA RSTP 18.2)\n
                3. Guarantee fee: information season by season. User can say total amount and number of installments. The system should understand the payment information and write it the way specified in the template \n
                Optional Inputs: \n
                1. Nationality of the Player (Optional) \n
                2. Passport Number (Optional) \n
                3. Address and Email (Optional) \n
                4. Contract Signature Date (Optional) \n
                5. Attendance Fee (Optional): Verify the logic of the fees given before generating the contract \n
                6. Bonuses (Optional): Verify the inclusion of bonuses. \n
                7. Signing on Fee (Optional): Verify inclusion of the signing fee. \n
                8. Other Benefits (Optional): Verify if any clauses added. \n

                Please make sure you will have all the must input from above before generating the contract. You have to follow the FIFA RSTP and Turkish Football regulation while writing the contract. Do not hallucinate any clauses. Also Validate the following logic. \n
                Validation logic for the Contract starting date and ending date: \n
                Contract starting date must be less than ending date. \n
                Validation logic for the Attendance Fee: \n
                Squad Condition: Starting 11 fees is greater than the Bench and bench fees is greater than Out of Squad \n
                Playing Condition: Total minutes is 90min. If fees is mentioned by minute make sure all the 90min fees are recorded. Following options : Starting minute minimum minutes played / total minutes played / get a card / scored a goal / assisted a goa. \n
                Match Result: Win fees is greater than Draw and Draw result fees wll more than Lose. \n

                The Contract should have 8 Articles: (If the content of the relevant item is empty, the next item replaces it.) \n
                1. The Parties \n
                2. Definitions \n
                3. Subject of the Contract \n
                4. Term of the Contract \n
                5. Obligations of the Player \n
                6. Obligations of the Club \n
                    a. Salary of the Player \n
                        1. First Season \n
                        2. Second Season \n
                        3. Third Season \n
                    b. Attendance Fee \n
                        1. First Season \n
                        2. Second Season \n
                        3. Third Season \n
                    c. Bonuses \n
                        1. First Season \n
                        2. Second Season \n
                        3. Third Season \n
                    d. Signing on Fee \n
                    e. Other Benefits \n
                        1. Flight Tickets \n
                        2. House \n
                        3. Car \n
                7. Force Majeure \n
                8. Miscellaneous \n""",
            )
            index = VectorStoreIndex.from_documents(docs)
            return index

        index = load_data()

        if player_detail_opt == "Passport":
            chat_box = st.chat_input("What do you want to do?")
            if "uploader_visible" not in st.session_state:
                st.session_state["uploader_visible"] = False
            def show_upload(state:bool):
                st.session_state["uploader_visible"] = state
                
            with st.chat_message("system"):
                cols= st.columns((3,1,1))
                cols[0].write("Do you want to upload a Player Passport?")
                cols[1].button("yes", use_container_width=True, on_click=show_upload, args=[True])
                cols[2].button("no", use_container_width=True, on_click=show_upload, args=[False])

            if st.session_state["uploader_visible"]:
                with st.chat_message("system"):
                    file = st.file_uploader("Upload your data")
                    if file:
                        with st.spinner("Processing your file"):
                             time.sleep(5) #<- dummy wait for demo. 

        else:

            if "chat_engine" not in st.session_state.keys():  # Initialize the chat engine
                st.session_state.chat_engine = index.as_chat_engine(
                    chat_mode="condense_plus_context", verbose=True, streaming=True,
                    context_prompt=(
                    "You are a FenerGPT, expert on the Player contract generation for Fenerbahçe Football Club."
                    "Here are the tempalte of Contract documents for the context:\n"
                    "{context_str}"
                    "Following Important Inputs: \n"
                    "1. Name of the Player: Can be Annonymous if user ask. \n"
                    "2. Contract starting date and ending date: (contract ending date should be stg 31.5.202X) (contract starting date should be before ending date… we can put some controls like this) (contract ending date cannot be after 5 years from starting date. FIFA RSTP 18.2)\n"
                    "3. Guarantee fee: information season by season. User can say total amount and number of installments. The system should understand the payment information and write it the way specified in the template \n"
                    "Optional Inputs: \n"
                    "1. Nationality of the Player \n"
                    "2. Passport Number \n"
                    "3. Address and Email \n"
                    "4. Contract Signature Date \n"
                    "5. Attendance Fee: Verify inclusion; prompt the user if omitted Ensure correct understanding and application of conditions \n"
                    "6. Bonuses: Verify inclusion; prompt the user if omitted. Ensure correct understanding and application of conditions \n"
                    "7. Signing on Fee: Verify inclusion; prompt the user if omitted \n"
                    "8. Other Benefits: Verify inclusion; prompt the user if omitted \n"
                    "Instruction: Use the previous chat history, or the context above, to interact and help the user.\n"

                ),
                )

            prompt = st.chat_input("Ask a question")

            # Voice input button with Language Selection
            st.sidebar.subheader("Voice Input Settings")
            language = st.sidebar.radio("Select the language for voice input:", options=["English", "Turkish"], index=0)
            language_code = "en-US" if language == "English" else "tr-TR"

            if st.button("Start Voice Recording"):
                with st.spinner("Recording..."):
                    voice_input = record_and_convert_to_text(language_code)
                    if voice_input:
                        prompt = voice_input

            if prompt:
                st.session_state.messages.append({"role": "user", "content": prompt})

            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.write(message["content"])

            if st.session_state.messages[-1]["role"] != "assistant":
                with st.chat_message("assistant"):
                    response_stream = st.session_state.chat_engine.stream_chat(prompt)
                    st.write_stream(response_stream.response_gen)
                    message = {"role": "assistant", "content": response_stream.response}
                    st.session_state.messages.append(message)
