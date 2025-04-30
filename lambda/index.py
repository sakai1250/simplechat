import json
import os
import urllib.request

# FastAPI サーバーのエンドポイント
FASTAPI_URL = os.environ.get("FASTAPI_URL", "https://9e90-34-31-253-220.ngrok-free.app/generate")

def lambda_handler(event, context):
    try:
        print("Received event:", json.dumps(event))

        # ユーザー情報（任意）
        user_info = None
        if 'requestContext' in event and 'authorizer' in event['requestContext']:
            user_info = event['requestContext']['authorizer']['claims']
            print(f"Authenticated user: {user_info.get('email') or user_info.get('cognito:username')}")

        # リクエストボディの取得と解析
        body = json.loads(event['body'])
        message = body['message']
        conversation_history = body.get('conversationHistory', [])

        # 会話履歴を結合（直前の履歴とmessageをつなげて1つのpromptとして送る）
        full_prompt = ""
        for msg in conversation_history:
            role = msg['role']
            content = msg['content']
            prefix = "User: " if role == "user" else "Assistant: "
            full_prompt += prefix + content + "\n"
        full_prompt += "User: " + message + "\nAssistant:"

        print("Sending prompt:", full_prompt)

        # FastAPIに渡す入力データ
        request_payload = {
            "prompt": full_prompt,
            "max_new_tokens": 512,
            "do_sample": True,
            "temperature": 0.7,
            "top_p": 0.9
        }

        # HTTPリクエスト作成
        req = urllib.request.Request(
            FASTAPI_URL,
            data=json.dumps(request_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        # リクエスト送信
        with urllib.request.urlopen(req) as res:
            res_body = res.read()
            print("Response from FastAPI:", res_body.decode())
            response_data = json.loads(res_body)

        # アシスタントの応答を取得
        assistant_response = response_data.get("generated_text", "")
        if not assistant_response:
            raise Exception("No response text from FastAPI")

        # 応答を履歴に追加
        conversation_history.append({"role": "user", "content": message})
        conversation_history.append({"role": "assistant", "content": assistant_response})

        # レスポンスを返却
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": True,
                "response": assistant_response,
                "conversationHistory": conversation_history
            })
        }

    except Exception as error:
        print("Error:", str(error))
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": False,
                "error": str(error)
            })
        }
