import smtplib
import imghdr
import os
import requests
import base64
import queue
import time

from threading import Thread

from util import log
from models.config import config

class Notifier(Thread):
    queue = queue.Queue()
    stop_flag = False

    def notify(self, message, attachments = []):

        if not config.notifications.enabled:
            return

        self.queue.put((message, attachments))

    def run(self):
        while not self.stop_flag:
            try:
                (message, attachments) = self.queue.get(block=False)
                self.send(message, attachments)
            except queue.Empty:
                time.sleep(0.1)
                continue

    def send(self, message, attachments):

        try:
            payload = {
                "text": message,
                "attachments": [],
                "meta": {
                    "surveillance": []
                }
            }

            if len(attachments) > 0:
                for filepath, meta in attachments:
                    with open(filepath, "rb") as fp:
                        img_data = fp.read()

                    payload["attachments"].append(base64.b64encode(img_data).decode())
                    payload["meta"]["surveillance"].append(meta)

            r = requests.post(config.notifications.url, json=payload)

            if r.status_code != 200:
                try:
                    error = r.json()
                    log("[notifier] Failed to send message {}: {}".format(message, error["error"]))
                except Exception as e:
                    log("[notifier] Failed to send message {}: {}".format(message, r.status_code))

        except Exception as e:
            log("[notifier] Failed to send message {}: {}".format(message, str(e)))

    def stop(self):
        self.stop_flag = True
        self.join()