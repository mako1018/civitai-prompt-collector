import streamlit as st

# モデル名とモデルIDの対応データ（修正済み）
MODEL_DATA = {
    "RealVisXL V5.0": {"id": "139562", "versions": ["v5.0"]},
    "Model A": {"id": "ID001", "versions": ["v1.0", "v1.1"]},
    "Model B": {"id": "ID002", "versions": ["v2.0", "v2.1"]},
    "Model C": {"id": "ID003", "versions": ["v3.0"]},
}

# セッション状態の初期化
if "model_name_input" not in st.session_state:
    st.session_state.model_name_input = ""
if "model_id_input" not in st.session_state:
    st.session_state.model_id_input = ""
if "model_version_input" not in st.session_state:
    st.session_state.model_version_input = ""
if "model_versions" not in st.session_state:
    st.session_state.model_versions = []
if "logs" not in st.session_state:
    st.session_state.logs = []
if "clear_flag" not in st.session_state:
    st.session_state.clear_flag = False

# ログ記録関数
def log_action(action, result=None):
    log_entry = {"action": action, "result": result}
    st.session_state.logs.append(log_entry)

# コールバック関数
def update_model_id():
    if st.session_state.model_name_input in MODEL_DATA:
        st.session_state.model_id_input = MODEL_DATA[st.session_state.model_name_input]["id"]
        st.session_state.model_versions = MODEL_DATA[st.session_state.model_name_input]["versions"]
        if st.session_state.model_versions:
            st.session_state.model_version_input = st.session_state.model_versions[0]
        log_action("モデル名入力", {"モデルID": st.session_state.model_id_input, "バージョン": st.session_state.model_versions})

def update_model_name():
    matched_name = [name for name, data in MODEL_DATA.items() if data["id"] == st.session_state.model_id_input]
    if matched_name:
        st.session_state.model_name_input = matched_name[0]
        st.session_state.model_versions = MODEL_DATA[matched_name[0]]["versions"]
        if st.session_state.model_versions:
            st.session_state.model_version_input = st.session_state.model_versions[0]
        log_action("モデルID入力", {"モデル名": st.session_state.model_name_input, "バージョン": st.session_state.model_versions})

# モデル情報クリアボタンの動作
def clear_model_info():
    st.session_state.clear_flag = True
    log_action("クリアボタン押下", "モデル情報をリセットしました")

# クリアフラグが立っている場合の処理
if st.session_state.clear_flag:
    st.session_state.model_name_input = ""
    st.session_state.model_id_input = ""
    st.session_state.model_version_input = ""
    st.session_state.model_versions = []
    st.session_state.clear_flag = False

# Streamlit UI
st.title("CivitAI Prompt Collector")

# モデル名、モデルID、モデルバージョンの横並び入力欄
st.write("モデル情報を入力してください:")
col1, col2, col3 = st.columns([2, 2, 2])
with col1:
    st.text_input(
        "モデル名",
        key="model_name_input",
        value=st.session_state.model_name_input,
        on_change=update_model_id
    )
with col2:
    st.text_input(
        "モデルID",
        key="model_id_input",
        value=st.session_state.model_id_input,
        on_change=update_model_name
    )
with col3:
    if st.session_state.model_versions:
        st.selectbox(
            "モデルバージョン",
            st.session_state.model_versions,
            key="model_version_input",
            index=st.session_state.model_versions.index(st.session_state.model_version_input)
                  if st.session_state.model_version_input in st.session_state.model_versions else 0
        )
        if st.session_state.model_version_input:
            log_action("バージョン選択", st.session_state.model_version_input)

# 収集開始ボタン
if st.button("収集開始"):
    st.session_state.collection_status = "収集中..."
    # ここで収集処理を実行（例: API呼び出しなど）
    st.session_state.collection_status = "収集完了！"
    st.session_state.collection_result = {
        "モデル名": st.session_state.model_name_input,
        "モデルID": st.session_state.model_id_input,
        "モデルバージョン": st.session_state.model_version_input,
    }
    log_action("収集開始", st.session_state.collection_result)

# モデル情報クリアボタン
if st.button("モデル情報クリア"):
    clear_model_info()

# 収集ステータス表示
if "collection_status" in st.session_state:
    st.write(f"ステータス: {st.session_state.collection_status}")

# 結果表示
if "collection_result" in st.session_state:
    st.write("収集結果:")
    st.json(st.session_state.collection_result)
