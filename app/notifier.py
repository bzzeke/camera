import smtplib
import imghdr
import os

from email.message import EmailMessage
from threading import Thread

from util import log

class Notifier(Thread):
    message = ""
    attachments = []

    def notify(self, message, attachments = []):

        if "CAMERA_DISABLE_NOTIFICATIONS" in os.environ:
            return

        self.message = message
        self.attachments = attachments
        self.start()

    def run(self):
        msg = EmailMessage()
        msg.set_content(self.message)
        msg["Subject"] = "Alert"
        msg["From"] = os.environ["FROM_EMAIL"]
        msg["To"] = os.environ["NOTIFY_EMAIL"]

        if len(self.attachments) > 0:
            for filepath in self.attachments:
                with open(filepath, "rb") as fp:
                    img_data = fp.read()

                msg.add_attachment(img_data, maintype="image", subtype=imghdr.what(None, img_data))

        self.send(msg)

    def send(self, message):
        try:
            s = smtplib.SMTP(host=os.environ["NOTIFYING_MAIL_SERVER"], port=25, timeout=10)
            s.send_message(message)
            s.quit()
        except Exception as e:
            log("[notifier] Failed to send email: %s" % str(e))
