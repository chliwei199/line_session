# -*- coding: utf-8 -*-

#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.

from __future__ import unicode_literals

from flask import Flask, render_template, redirect, request
import requests
import datetime
import errno
import json
import os
import sys
import tempfile
import uuid
from argparse import ArgumentParser

from flask import Flask, request, abort, send_from_directory
from werkzeug.middleware.proxy_fix import ProxyFix

from linebot import (
    LineBotApi, WebhookHandler
)
# from linebot.exceptions import (
#     LineBotApiError, InvalidSignatureError
# )
# from linebot.models import (
#     MessageEvent, TextMessage, TextSendMessage,
#     SourceUser, SourceGroup, SourceRoom,
#     TemplateSendMessage, ConfirmTemplate, MessageAction,
#     ButtonsTemplate, ImageCarouselTemplate, ImageCarouselColumn, URIAction,
#     PostbackAction, DatetimePickerAction,
#     CameraAction, CameraRollAction, LocationAction,
#     CarouselTemplate, CarouselColumn, PostbackEvent,
#     StickerMessage, StickerSendMessage, LocationMessage, LocationSendMessage,
#     ImageMessage, VideoMessage, AudioMessage, FileMessage,    AudioSendMessage,VideoSendMessage,

#     UnfollowEvent, FollowEvent, JoinEvent, LeaveEvent, BeaconEvent,
#     MemberJoinedEvent, MemberLeftEvent,
#     FlexSendMessage, BubbleContainer, ImageComponent, BoxComponent,
#     TextComponent, SpacerComponent, IconComponent, ButtonComponent,
#     SeparatorComponent, QuickReply, QuickReplyButton,
#     ImageSendMessage)

app = Flask(__name__)
# app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1, x_proto=1)

# get channel_secret and channel_access_token from your environment variable
channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
if channel_secret is None or channel_access_token is None:
    print('Specify LINE_CHANNEL_SECRET and LINE_CHANNEL_ACCESS_TOKEN as environment variables.')
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')


# function for create tmp dir for download content
def make_static_tmp_dir():
    try:
        os.makedirs(static_tmp_path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(static_tmp_path):
            pass
        else:
            raise


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except LineBotApiError as e:
        print("Got exception from LINE Messaging API: %s\n" % e.message)
        for m in e.error.details:
            print("  %s: %s" % (m.property, m.message))
        print("\n")
    except InvalidSignatureError:
        abort(400)

    return 'OK'

# @handler.add(MessageEvent, message=TextMessage)
# def handle_text_message(event):
#     text = event.message.text

#     if text == 'profile1':
#         if isinstance(event.source, SourceUser):
#             profile = line_bot_api.get_profile(event.source.user_id)
#             line_bot_api.reply_message(
#                 event.reply_token, [
#                     TextSendMessage(text='Display name: ' + profile.display_name),
#                     TextSendMessage(text='Status message: ' + str(profile.status_message)),
#                     TextSendMessage(text='User_id: ' + event.source.user_id),
#                 ]
#             )
#         else:
#             line_bot_api.reply_message(
#                 event.reply_token,
#                 TextSendMessage(text="Bot can't use profile API without user ID"))
#     else:
#         line_bot_api.reply_message(
#             event.reply_token, TextSendMessage(text=event.message.text))

@app.route("/test", methods=['GET'])
def test():
    return 'OK'

LINE_PAY_URL = 'https://sandbox-api-pay.line.me'
LINE_PAY_CHANNEL_ID = ''
LINE_PAY_CHANNEL_SECRET = ''
LINE_PAY_CONFIRM_URL = 'http://127.0.0.1:8000/pay/confirm'

@app.route("/pay/reserve", methods=['POST'])
def pay_reserve():
    product_name = 'Line payment Impl'
    amount = 10
    currency = 'TWD'
    productImageUrl = 'https://ithelp.ithome.com.tw/images/ironman/11th/event/kv_event/kv-bg-addfly.png'
    confirmUrl = LINE_PAY_CONFIRM_URL
    orderId = uuid.uuid4().hex
	
    data = {
        'amount': amount,
        'productName': product_name,
        'productImageUrl': productImageUrl,
        'confirmUrl': confirmUrl,
        'orderId': orderId,
        'currency': currency
    }

    headers = {'Content-Type': 'application/json','X-LINE-ChannelId': LINE_PAY_CHANNEL_ID,'X-LINE-ChannelSecret': LINE_PAY_CHANNEL_SECRET}
    response = requests.post(LINE_PAY_URL+'/v2/payments/request', headers=headers, data=json.dumps(data)).json()
    print(response["returnMessage"])
    return "Status:"+response["returnMessage"]+"\nURL:"+response["info"]["paymentUrl"]["web"]

@app.route("/pay/confirm", methods=['GET'])
def pay_confirm():
    transaction_id = request.args.get('transactionId')
    amount = 10
    currency = 'TWD'

    data = {
        'amount': amount,
        'currency': currency
    }

    headers = {'Content-Type': 'application/json','X-LINE-ChannelId': LINE_PAY_CHANNEL_ID,'X-LINE-ChannelSecret': LINE_PAY_CHANNEL_SECRET}
    response = requests.post(LINE_PAY_URL+'/v2/payments/'+transaction_id+'/confirm', headers=headers, data=json.dumps(data)).json()

    # print(response["returnCode"])
    # print(response["returnMessage"])

    return "ReturnCode:"+response["returnCode"]+"\nReturnMessage:"+response["returnMessage"]+"\nInfo:"+str(response["info"])


if __name__ == "__main__":
    arg_parser = ArgumentParser(
        usage='Usage: python ' + __file__ + ' [--port <port>] [--help]'
    )
    arg_parser.add_argument('-p', '--port', type=int, default=8000, help='port')
    arg_parser.add_argument('-d', '--debug', default=False, help='debug')
    options = arg_parser.parse_args()

    # create tmp dir for download content
    make_static_tmp_dir()

    app.run(debug=options.debug, port=options.port)
