import smtplib
from email.message import EmailMessage
import imghdr
import os

class Notifier():
    def notify(self, message, attachments = []):

        if "CAMERA_DISABLE_NOTIFICATIONS" in os.environ:
            return

        msg = EmailMessage()
        msg.set_content(message)
        msg["Subject"] = "Alert"
        msg["From"] = os.environ["FROM_EMAIL"]
        msg["To"] = os.environ["NOTIFY_EMAIL"]

        if len(attachments) > 0:
            for filepath in attachments:
                with open(filepath, 'rb') as fp:
                    img_data = fp.read()

                msg.add_attachment(img_data, maintype='image', subtype=imghdr.what(None, img_data))

        self.send(msg)

    def send(self, message):
        try:
            s = smtplib.SMTP(host=os.environ["NOTIFYING_MAIL_SERVER"], port=25, timeout=5)
            s.send_message(message)
            s.quit()
        except Exception as e:
            print("[notifier] Failed to send email: %s" % str(e))