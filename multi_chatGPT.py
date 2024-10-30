import streamlit as st
import os
from openai import AzureOpenAI
from PIL import Image
import base64

# Azure OpenAI設定
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),  
    api_version="2024-02-15-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

st.title("Azure OpenAI ChatGPT with Image Upload")

# チャット履歴と画像の初期化
if "messages" not in st.session_state:
    st.session_state.messages = []
if "images" not in st.session_state:
    st.session_state.images = []

# 画像をbase64エンコードする関数
def encode_image(image_file):
    return base64.b64encode(image_file.getvalue()).decode('utf-8')

# サイドバー
with st.sidebar:
    st.header("画像アップロード")
    uploaded_files = st.file_uploader("画像を選択してください", type=["jpg", "jpeg", "png"], key="uploader", accept_multiple_files=True)
    if uploaded_files:
        for uploaded_file in uploaded_files:
            image = Image.open(uploaded_file)
            encoded_image = encode_image(uploaded_file)
            if not any(img["name"] == uploaded_file.name for img in st.session_state.images):
                st.session_state.images.append({
                    "image": image,
                    "encoded": encoded_image,
                    "name": uploaded_file.name
                })
                st.success(f"画像 '{uploaded_file.name}' がアップロードされました。")
    
    st.subheader("アップロードされた画像")
    for idx, img_data in enumerate(st.session_state.images):
        st.image(img_data["image"], caption=img_data["name"], use_column_width=True)
        if st.button(f"削除 {img_data['name']}", key=f"delete_{idx}"):
            st.session_state.images.pop(idx)
            st.rerun()
    
    if st.button("すべての画像とチャット履歴をクリア"):
        st.session_state.messages = []
        st.session_state.images = []
        st.rerun()

    # 過去メッセージの数を選択
    past_message_count = st.slider("過去メッセージの数", min_value=1, max_value=20, value=10)
    # 温度設定
    temperature = st.slider("温度", min_value=0.0, max_value=1.0, value=0.5, step=0.1)

# メインエリア
# チャット履歴の表示
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ユーザー入力
if prompt := st.chat_input("What is up?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # メッセージリストの作成
    # 最新の入力メッセージと過去メッセージから指定数を含む
    num_messages_to_include = past_message_count * 2  # ユーザーとアシスタントのペアのメッセージ数に変換
    messages = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[-(num_messages_to_include + 1):]]
    
    # 画像がある場合、最初のメッセージに追加
    if st.session_state.images:
        image_contents = [
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img['encoded']}"}}
            for img in st.session_state.images
        ]
        messages[0]["content"] = [{"type": "text", "text": messages[0]["content"]}] + image_contents

    # Azure OpenAIからの応答を取得
    response = client.chat.completions.create(
        model="pm-GPT4o",  # デプロイしたモデル名
        messages=messages,
        temperature=temperature  # 温度パラメータの設定
    )

    # 応答の表示
    assistant_response = response.choices[0].message.content
    st.session_state.messages.append({"role": "assistant", "content": assistant_response})
    with st.chat_message("assistant"):
        st.markdown(assistant_response)

    st.rerun()
