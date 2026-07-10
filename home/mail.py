import logging
import smtplib

from django.core.mail.backends.smtp import EmailBackend as DjangoSMTPEmailBackend

logger = logging.getLogger(__name__)


class ResilientSMTPEmailBackend(DjangoSMTPEmailBackend):
    """
    La fel ca backend-ul SMTP din Django, dar nu lasa o deconectare
    neasteptata a serverului (intalnita la Yahoo dupa multe trimiteri
    intr-un timp scurt) sa faca sa pice cu eroare intreaga actiune care
    a declansat emailul - de exemplu aprobarea unei pagini in workflow,
    care trimite automat o notificare.
    """

    def open(self):
        try:
            return super().open()
        except smtplib.SMTPServerDisconnected:
            logger.exception(
                "Serverul de mail a inchis conexiunea neasteptat - email-ul nu s-a trimis."
            )
            return None
