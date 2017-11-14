import smtplib
from email.mime.text import MIMEText
from fun_settings import AUTOMATION_EMAIL

DEFAULT_TO_ADDRESSES = [AUTOMATION_EMAIL]


def send_mail(from_address="john.abraham@fungible.com", to_addresses=None, subject="", content=""):
    result = {"status": False, "error_message": ""}
    if not to_addresses:
        to_addresses = DEFAULT_TO_ADDRESSES
        # to_addresses = ["qa@fungible.com"]
    print from_address, to_addresses
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
        print "Sent mail"
    except Exception as ex:
        result["error_message"] = "Unable to send mail: %s" % (str(ex))
        print result["error_message"]
    return result

if __name__ == "__main__":
    #send_mail(from_address="john.abraham@fungible.com", to_addresses=["automation@fungible.com"], subject="abc", content="abc")
    send_mail(subject="abc", content="abc")
