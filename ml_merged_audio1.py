from flask import Flask, request, jsonify
from flask_restful import Api, Resource
import subprocess
import os
import zipfile
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

app = Flask(__name__)
api = Api(app)

# Email configuration
SMTP_SERVER = "smtp.your-email-provider.com"  # Example: smtp.gmail.com
SMTP_PORT = 587
SENDER_EMAIL = "your_email@example.com"
SENDER_PASSWORD = "your_password"


class MashupService(Resource):
    def post(self):
        data = request.get_json()

        # Get inputs from request data
        singer_name = data.get("singer_name")
        num_videos = data.get("num_videos")
        duration = data.get("duration")
        email = data.get("email")

        # Validate inputs
        if not all([singer_name, num_videos, duration, email]):
            return {"message": "All fields (singer_name, num_videos, duration, email) are required."}, 400

        output_file = f"{singer_name.replace(' ', '_')}_mashup.mp3"

        try:
            # Run the Program 1 script to create mashup
            subprocess.run(["python", "1015579.py", singer_name, str(num_videos), str(duration), output_file],
                           check=True)

            # Zip the output file
            zip_filename = f"{output_file}.zip"
            with zipfile.ZipFile(zip_filename, "w") as zipf:
                zipf.write(output_file)

            # Send the zip file via email
            self.send_email(email, zip_filename)

            return {"message": "Mashup created and emailed successfully"}, 200
        except subprocess.CalledProcessError as e:
            return {"message": f"Error in mashup generation: {str(e)}"}, 500
        except Exception as e:
            return {"message": f"Error: {str(e)}"}, 500
        finally:
            # Clean up files
            if os.path.exists(output_file):
                os.remove(output_file)
            if os.path.exists(zip_filename):
                os.remove(zip_filename)

    def send_email(self, recipient_email, zip_filename):
        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = recipient_email
        msg["Subject"] = "Your Mashup File"

        # Attach the zip file
        with open(zip_filename, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename={zip_filename}")
            msg.attach(part)

        # Connect to the email server and send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())


api.add_resource(MashupService, "/mashup")

if __name__ == "__main__":
    app.run(debug=True)
