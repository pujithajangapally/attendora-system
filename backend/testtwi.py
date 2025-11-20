from twilio.rest import Client

client = Client("AC115fd4c34e0d3366cba43a3ae9240756", "cf4b27d191274419481dee121b8f9dd2")
message = client.messages.create(
    body="Test message from Attendora",
    from_="whatsapp:+14155238886",  # Twilio sandbox number
    to="whatsapp:+918919669223"     # Parent number
)
print("Message SID:", message.sid)