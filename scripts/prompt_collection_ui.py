import streamlit as st

# Mock data for models
MODEL_DATA = {
    "Model A": "123",
    "Model B": "456",
    "Model C": "789",
}

# Reverse lookup for model ID to name
MODEL_ID_TO_NAME = {v: k for k, v in MODEL_DATA.items()}

def main():
    st.title("CivitAI Prompt Collector")

    # Input fields in horizontal layout
    st.header("収集ターゲットの指定")
    if "model_name" not in st.session_state:
        st.session_state["model_name"] = ""
    if "model_id" not in st.session_state:
        st.session_state["model_id"] = ""

    col1, col2 = st.columns(2)
    with col1:
        model_name = st.text_input("モデル名", st.session_state["model_name"])
        if model_name in MODEL_DATA:
            st.session_state["model_id"] = MODEL_DATA[model_name]
    with col2:
        model_id = st.text_input("モデルID", st.session_state["model_id"])
        if model_id in MODEL_ID_TO_NAME:
            st.session_state["model_name"] = MODEL_ID_TO_NAME[model_id]

    # Start collection button
    if st.button("収集開始"):
        st.write("収集を開始しました...")
        # Placeholder for collection logic
        st.write(f"モデル名: {st.session_state['model_name']}, モデルID: {st.session_state['model_id']}")

    # Status display
    st.header("収集ステータス")
    st.write("ステータス: 未実行")

    # Results display
    st.header("収集結果")
    st.write("収集されたデータはここに表示されます。")

if __name__ == "__main__":
    main()
