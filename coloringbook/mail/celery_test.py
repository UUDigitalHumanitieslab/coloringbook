import unittest
from mock import patch, call
from coloringbook.mail.utilities import send_async_email
from flask_mail import Message


class TestSendAsyncEmail(unittest.TestCase):
    @patch("coloringbook.mail.utilities.mail_client.send")
    @patch("coloringbook.mail.utilities.send_async_email.retry")
    def test_send_async_email(self, mock_retry, mock_send):
        subject = "Test Subject"
        recipient = "test@example.com"
        html = "<p>This is a test email.</p>"

        expected_message = Message(subject=subject, recipients=[recipient], html=html)

        send_async_email(subject, recipient, html)

        call_args = mock_send.call_args

        self.assertEqual(call_args[0][0].subject, expected_message.subject)
        self.assertEqual(call_args[0][0].recipients, expected_message.recipients)
        self.assertEqual(call_args[0][0].html, expected_message.html)

    @patch("coloringbook.mail.utilities.mail_client.send", side_effect=Exception())
    @patch("coloringbook.mail.utilities.send_async_email.retry")
    def test_send_async_email_retry_on_error(self, mock_retry, mock_send):
        subject = "Test Subject"
        recipient = "test@example.com"
        html = "<p>This is a test email.</p>"

        try:
            send_async_email(subject, recipient, html)
        except Exception:
            pass

        mock_retry.assert_called_once()


if __name__ == "__main__":
    unittest.main()
