import smtplib
from email.mime.text import MIMEText
from fun_settings import AUTOMATION_EMAIL

DEFAULT_TO_ADDRESSES = [AUTOMATION_EMAIL]


def send_mail(from_address=AUTOMATION_EMAIL, to_addresses=None, subject="", content=""):
    result = {"status": False, "error_message": ""}
    if not to_addresses:
        to_addresses = DEFAULT_TO_ADDRESSES
    try:
        msg = MIMEText(content, "html")
        msg['Subject'] = subject
        msg['From'] = from_address
        to_address_str = ", ".join(to_addresses)
        msg['To'] = to_address_str
        s = smtplib.SMTP("localhost", timeout=5)
        s.starttls()
        s.sendmail(from_address, to_addresses, msg.as_string())
        s.quit()
        result["status"] = True
    except Exception as ex:
        result["error_message"] = "Unable to send mail: %s" % (str(ex))
    return result

if __name__ == "__main__":
    send_mail(from_address="automation@fungible.com", to_addresses=["automation@fungible.com"], subject="abc", content="abc")