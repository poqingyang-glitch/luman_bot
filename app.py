import os
import sys
from flask import Flask, request, abort, render_template
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# 建立 Flask 應用程式實例
app = Flask(__name__)

# 從環境變數中取得您的 LINE 憑證
# 這部分我們稍後會在 Heroku 上設定，本地測試請用 .env
CHANNEL_ACCESS_TOKEN = 'QNR5aMydxFXzE+2TYUcTlNFm9yzsWelp/2FWpjJ8eDWbBlt3fvzNhRky9qYnL8PScVWtyreFwwqzjiGAksSlEhdKZPy04a6N02G4Ou2XU35KagprWucG70LvTc+nf0Gg4y9BbdgLOhDrcnCtVNxMjAdB04t89/1O/w1cDnyilFU='
CHANNEL_SECRET = '6fef92e07c670922c68d0c01a88d855b'

# 安全檢查：確保環境變數已設定
if not CHANNEL_ACCESS_TOKEN or not CHANNEL_SECRET:
    print('錯誤：請設定 CHANNEL_ACCESS_TOKEN 和 CHANNEL_SECRET 環境變數。')
    sys.exit(1)

# 初始化 LINE SDK
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# 定義 Webhook 的路由
@app.route("/callback", methods=['POST'])
def callback():
    """
    接收 LINE 傳來的 Webhook 請求。
    """
    # 取得驗證簽章
    signature = request.headers['X-Line-Signature']

    # 取得請求主體 (body)
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # 處理 Webhook 主體
    try:
        # 呼叫 handler 處理事件
        handler.handle(body, signature)
    except InvalidSignatureError:
        # 簽章驗證失敗
        abort(400)

    return 'OK'

# ==========================================
# 處理「文字訊息」事件的核心函式
# ==========================================
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """
    接收文字訊息事件。
    1. 當收到「測試」時，回覆「你好」。
    2. 其他訊息只列印在 logs，不回覆。
    """
    # ==========================================
    # 步驟 1. 【新增需求】都要 print 所有訊息出來
    # ==========================================
    
    # 取得使用者 ID (方便除錯看是誰傳的)
    user_id = event.source.user_id
    # 取得收到訊息的文字內容
    received_text = event.message.text
    
    # 【關鍵】使用 Python 标准 print 函式
    # 這行訊息將會出现在 Render 后台的「Logs」頁面中
    print(f"------------ 新訊息 ------------")
    print(f"[*] 來自使用者 ID: {user_id}")
    print(f"[*] 訊息內容: {received_text}")
    print(f"--------------------------------")

    # ==========================================
    # 步驟 2. 【核心邏輯修改】關鍵字條件回應
    # ==========================================
    
    # 使用 Python 的完全匹配 (==) 來判断
    # 為了避免空格影响，可以使用 .strip() (可选)
    # 例如：received_text.strip() == "測試"
    
    if received_text == "測試":
        # 1. 條件成立：準備要回覆的訊息物件 (你好)
        reply_message = TextSendMessage(text="你好")
        
        # 2. 使用 reply_token 回覆訊息
        # 注意：一個 replyToken 只能使用一次
        line_bot_api.reply_message(event.reply_token, reply_message)
        
        # 可选：也在 logs 记录一下已回應
        print(f"[#] 已針對「測試」指令回覆「你好」")
        
    else:
        # 條件不成立 (收到非「測試」的文字)
        # 邏輯上我們不做任何 replyMessage 动作 (不回覆)
        # 只依靠之前的 print 记录日誌
        print(f"[ ] 收到其他訊息，忽略不回應。")
        pass # 结束逻辑
        
        # ==========================================
# 新增：提供點餐 HTML 網頁的路由
# ==========================================
@app.route("/menu")
def liff_menu():
    """
    當使用者存取 https://luman-bot.onrender.com/menu 時，
    Flask 會讀取 templates/menu.html 並將其渲染為網頁送出。
    """
    # render_template 會自動去 templates 資料夾找檔案
    return render_template("menu.html")

# ==========================================
# 處理「文字訊息」事件的核心函式 (已優化判斷邏輯)
# ==========================================
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    received_text = event.message.text.strip() # 去除頭尾多餘空白
    
    # 除錯用：在後台 Log 顯示實際收到的訊息長度與內容
    print(f"------------ 新訊息 ------------")
    print(f"[*] 來自使用者 ID: {user_id}")
    print(f"[*] 訊息內容: [{received_text}]")
    print(f"--------------------------------")

    # 定義關鍵字
    order_keyword = "【鹿滿 吳媽媽早餐店 - 線上訂單】"

    # 1. 測試用指令
    if received_text == "測試":
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="你好"))
        print(f"[#] 已針對「測試」指令回覆「你好」")
        
    # 2. 修改判斷方式：使用 in 關鍵字，只要訊息中包含該標題即觸發
    elif order_keyword in received_text:
        # 準備要回覆給客人的確認訊息
        # reply_msg = (
        #     "✅請確認您的餐點與取餐時間是否正確唷！\n"
        #     "請等候老闆確認訂單後才算下單成功哦\n"
            
        #     "我們會在您指定的時間，\n"
        #     "為您準備好美味餐點等您來取餐🥰\n\n"
            
        #     "若有特殊需求忘記填寫在備註欄，\n"
        #     "也沒關係～\n"
        #     "歡迎直接在聊天室傳送訊息告訴我們！\n"
        #     "我們收到後會盡快為您處理，謝謝您的支持 ❤️\n\n"
            
        #     "（此為系統自動回覆，\n"
        #     "以上如果都確認無誤，\n"
        #     "則無須理會回應喔！）\n\n"
            
        #     "感謝您的配合，謝謝！！"
        # )
        # line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_msg))
        print(f"[#] 成功接收訂單並回覆確認訊息！")
        
    # 3. 其他訊息
    else:
        print(f"[ ] 收到其他訊息 (未觸發關鍵字)，忽略不回應。")
        pass
if __name__ == "__main__":
    # 在本地執行時啟用 Debug 模式，監聽所有介面，Port 預設 5000
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)