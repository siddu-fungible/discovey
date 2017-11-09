import smtplib
from email.mime.text import MIMEText


def send_mail(from_address, to_addresses, subject, content):
    try:
        msg = MIMEText(content, "html")
        msg['Subject'] = subject
        msg['From'] = from_address
        to_address_str = ", ".join(to_addresses)
        msg['To'] = to_address_str
        # print("Trying to send mail")
        s = smtplib.SMTP("smtp.gmail.com:465", timeout=20)
        s.starttls()
        s.sendmail(from_address, to_addresses, msg.as_string())
        # print("Sent mail")
        s.quit()
    except Exception as ex:
        print("Unable to send mail: %s" % (str(ex)))

if __name__ == "__main__":
    send_mail(from_address="automation@fungible.com", to_addresses=["john.abraham@fungible.com"], subject="abc", content="abc")