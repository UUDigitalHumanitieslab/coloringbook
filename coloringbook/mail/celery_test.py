import unittest
from mock import patch, call
from utilities import send_async_email
from celery.exceptions import OperationalError


class TestSendAsyncEmail(unittest.TestCase):
    @patch("utilities.mail_client.send")
    @patch("utilities.send_async_email.retry")
    def test_send_async_email(self, mock_retry, mock_send):
        # Arrange
        subject = "Test Subject"
        recipient = "test@example.com"
        html = "<p>This is a test email.</p>"

        # Act
        send_async_email(subject, recipient, html)

        # Assert
        mock_send.assert_called_once_with(
            call(subject=subject, recipients=[recipient], html=html)
        )

    @patch("utilities.mail_client.send", side_effect=OperationalError)
    @patch("utilities.send_async_email.retry")
    def test_send_async_email_retry_on_operational_error(self, mock_retry, mock_send):
        # Arrange
        subject = "Test Subject"
        recipient = "test@example.com"
        html = "<p>This is a test email.</p>"

        # Act
        send_async_email(subject, recipient, html)

        # Assert
        mock_retry.assert_called_once()


if __name__ == "__main__":
    unittest.main()
