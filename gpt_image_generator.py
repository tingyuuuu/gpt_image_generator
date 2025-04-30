import openai
import requests
import os
import pandas as pd
import chardet
import time
import json

# 設定 OpenAI API 金鑰
# 這寫法可能會提高資安風險，僅適合臨時key使用
OPENAI_API_KEY = "your_key"

# 初始化 OpenAI 客戶端
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# 設定圖片 & JSON 儲存位置
save_folder = "your_path"
json_file_path = os.path.join(save_folder, "generated_images.json")
os.makedirs(save_folder, exist_ok=True)  # 確保資料夾存在

# 讀取 CSV 檔案
csv_file_path = "your_path"

# 偵測編碼
with open(csv_file_path, "rb") as f:
    result = chardet.detect(f.read(100000))  # 讀取部分內容偵測
    encoding_detected = result["encoding"]

print(f"偵測到的 CSV 編碼：{encoding_detected}")

try:
    df = pd.read_csv(csv_file_path, encoding=encoding_detected)
except Exception as e:
    print(f"無法讀取 CSV：{e}")
    exit()

# 可選擇只處理前n筆資料
#amount = n
#df = df.head(amount)

# 確保 "text" 欄位存在
if "text" not in df.columns:
    print("錯誤：CSV 檔案中找不到 'text' 欄位，請確認檔案格式！")
    exit()

#print(f"讀取到 {len(df)} 筆資料（已限制為n筆），開始生成 meme 圖片並即時寫入 JSON 檔案...")
print(f"讀取到 {len(df)} 筆資料，開始生成 meme 圖片並即時寫入 JSON 檔案...")

# 如果 JSON 檔案已存在，讀取舊資料，避免覆蓋
if os.path.exists(json_file_path):
    with open(json_file_path, "r", encoding="utf-8") as json_file:
        try:
            json_data = json.load(json_file)
        except json.JSONDecodeError:
            json_data = []  # 若 JSON 損壞則重置
else:
    json_data = []

# 取得已經儲存的 ID，避免重複
existing_ids = {entry["ID"] for entry in json_data}

# 遍歷 CSV 檔案
for index, row in df.iterrows():
    try:
        text_content = str(row["text"]).strip()  # 讀取 "text" 欄位
        if not text_content:
            print(f"跳過第 {index+1} 行（內容為空）")
            continue

        # 確保 ID 唯一
        meme_id = index + 1
        if meme_id in existing_ids:
            print(f"跳過第 {meme_id} 張圖片（已存在於 JSON）")
            continue

        # 格式化輸入內容
        formatted_prompt = (
            f'"{text_content}"'
        )
        # 字串可自由設置

        print(f"生成第 {meme_id} 張 meme 圖片，描述內容：\n{text_content}")

        # 使用 DALL·E 3 生成圖片
        response = client.images.generate(
            model="dall-e-3",
            prompt=formatted_prompt,
            n=1,
            size="1024x1024"
        )

        # 取得圖片 URL
        image_url = response.data[0].url
        print(f"圖片已生成：{image_url}")

        # 下載圖片
        image_data = requests.get(image_url).content

        # 設定檔名
        timestamp = int(time.time())  # 生成唯一時間戳
        image_filename = f"meme_{meme_id}_{timestamp}.png"
        image_path = os.path.join(save_folder, image_filename)

        # 儲存圖片
        with open(image_path, "wb") as file:
            file.write(image_data)

        print(f"圖片已儲存至：{image_path}")

        # 將圖片資訊即時寫入 JSON
        new_entry = {
            "ID": meme_id,
            "caption": text_content,
            "image": image_filename
        }
        json_data.append(new_entry)

        # 立即寫入 JSON 檔案
        with open(json_file_path, "w", encoding="utf-8") as json_file:
            json.dump(json_data, json_file, indent=4, ensure_ascii=False)

        print(f"JSON 檔案已更新！")

    except Exception as e:
        print(f"生成第 {index+1} 張圖片時發生錯誤：{e}")

print("所有 meme 圖片已生成完成！")
