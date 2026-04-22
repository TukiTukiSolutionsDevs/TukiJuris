"""Transactional email service — Resend, SMTP, or console fallback."""

import asyncio
import logging
from abc import ABC, abstractmethod

from app.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# HTML Templates
# ---------------------------------------------------------------------------

_BASE_STYLE = (
    "font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;"
    " max-width: 600px; margin: 0 auto; background: #0f0f0f; color: #e5e5e5;"
    " padding: 40px; border-radius: 12px;"
)

_HEADER = """
<div style="text-align: center; margin-bottom: 32px;">
  <h1 style="color: #f59e0b; font-size: 24px; margin: 0;">TukiJuris</h1>
  <p style="color: #9ca3af; font-size: 14px; margin: 4px 0 0 0;">Plataforma Juridica Inteligente</p>
</div>
"""

_FOOTER = """
<div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #262626; text-align: center;">
  <p style="color: #6b7280; font-size: 12px; margin: 0;">
    TukiJuris &mdash; Plataforma Juridica Inteligente para el Derecho Peruano
  </p>
  <p style="color: #4b5563; font-size: 11px; margin: 6px 0 0 0;">
    Si no esperabas este correo, puedes ignorarlo de forma segura.
  </p>
</div>
"""

WELCOME_TEMPLATE = """
<div style="{base_style}">
  {header}
  <h2 style="color: #f5f5f5; font-size: 20px; margin: 0 0 16px 0;">
    Bienvenido, {{name}}
  </h2>
  <p style="color: #d1d5db; line-height: 1.7; margin: 0 0 16px 0;">
    Tu cuenta en TukiJuris esta lista. Ahora tenes acceso a la plataforma juridica
    inteligente especializada en derecho peruano.
  </p>
  <p style="color: #d1d5db; line-height: 1.7; margin: 0 0 24px 0;">
    Podes consultar legislacion, jurisprudencia y doctrina con respuestas citadas
    directamente desde las fuentes oficiales.
  </p>
  <div style="background: #1a1a1a; border-radius: 8px; padding: 20px; margin: 0 0 24px 0;">
    <p style="color: #9ca3af; font-size: 13px; margin: 0 0 8px 0; font-weight: 600;">
      EMPEZA AHORA
    </p>
    <ul style="color: #d1d5db; line-height: 1.8; margin: 0; padding-left: 20px;">
      <li>Hacé tu primera consulta legal</li>
      <li>Explora las areas del derecho disponibles</li>
      <li>Creá o uníte a una organizacion</li>
    </ul>
  </div>
  {footer}
</div>
""".format(base_style=_BASE_STYLE, header=_HEADER, footer=_FOOTER)

INVITE_TEMPLATE = """
<div style="{base_style}">
  {header}
  <h2 style="color: #f5f5f5; font-size: 20px; margin: 0 0 16px 0;">
    Invitacion a {{org}}
  </h2>
  <p style="color: #d1d5db; line-height: 1.7; margin: 0 0 16px 0;">
    <strong style="color: #f59e0b;">{{inviter}}</strong> te invito a unirte a
    <strong style="color: #f5f5f5;">{{org}}</strong> en TukiJuris.
  </p>
  <p style="color: #d1d5db; line-height: 1.7; margin: 0 0 24px 0;">
    Como miembro de la organizacion vas a poder colaborar en consultas juridicas
    y compartir el acceso a la plataforma.
  </p>
  <div style="text-align: center; margin: 32px 0;">
    <a href="{{url}}"
       style="background: #f59e0b; color: #0f0f0f; padding: 12px 32px; border-radius: 8px;
              text-decoration: none; font-weight: 700; font-size: 15px; display: inline-block;">
      Aceptar invitacion
    </a>
  </div>
  <p style="color: #6b7280; font-size: 12px; text-align: center; margin: 0;">
    O pega este enlace en tu navegador: <br>
    <span style="color: #9ca3af; word-break: break-all;">{{url}}</span>
  </p>
  {footer}
</div>
""".format(base_style=_BASE_STYLE, header=_HEADER, footer=_FOOTER)

USAGE_ALERT_TEMPLATE = """
<div style="{base_style}">
  {header}
  <h2 style="color: #f59e0b; font-size: 20px; margin: 0 0 16px 0;">
    Alerta de uso: {{pct}}% del limite alcanzado
  </h2>
  <p style="color: #d1d5db; line-height: 1.7; margin: 0 0 16px 0;">
    La organizacion <strong style="color: #f5f5f5;">{{org}}</strong> alcanzo el
    <strong style="color: #f59e0b;">{{pct}}%</strong> de su limite mensual de consultas.
  </p>
  <div style="background: #1a1a1a; border-radius: 8px; padding: 20px; margin: 0 0 24px 0;">
    <div style="display: flex; justify-content: space-between; margin-bottom: 12px;">
      <span style="color: #9ca3af; font-size: 13px;">Consultas utilizadas</span>
      <span style="color: #f5f5f5; font-weight: 600;">{{used}} / {{limit}}</span>
    </div>
    <div style="background: #262626; border-radius: 4px; height: 8px; overflow: hidden;">
      <div style="background: #f59e0b; height: 100%; width: {{pct}}%; border-radius: 4px;"></div>
    </div>
  </div>
  <p style="color: #d1d5db; line-height: 1.7; margin: 0 0 24px 0;">
    Considera actualizar el plan de tu organizacion para continuar usando la plataforma
    sin interrupciones.
  </p>
  {footer}
</div>
""".format(base_style=_BASE_STYLE, header=_HEADER, footer=_FOOTER)

PASSWORD_RESET_TEMPLATE = """
<div style="{base_style}">
  {header}
  <h2 style="color: #f5f5f5; font-size: 20px; margin: 0 0 16px 0;">
    Restablecer tu contrasena
  </h2>
  <p style="color: #d1d5db; line-height: 1.7; margin: 0 0 16px 0;">
    Recibimos una solicitud para restablecer la contrasena de tu cuenta.
    Este enlace es valido por <strong style="color: #f59e0b;">15 minutos</strong>.
  </p>
  <div style="text-align: center; margin: 32px 0;">
    <a href="{{url}}"
       style="background: #f59e0b; color: #0f0f0f; padding: 12px 32px; border-radius: 8px;
              text-decoration: none; font-weight: 700; font-size: 15px; display: inline-block;">
      Restablecer contrasena
    </a>
  </div>
  <p style="color: #6b7280; font-size: 12px; text-align: center; margin: 0 0 8px 0;">
    O pega este enlace en tu navegador: <br>
    <span style="color: #9ca3af; word-break: break-all;">{{url}}</span>
  </p>
  <p style="color: #4b5563; font-size: 12px; text-align: center; margin: 0;">
    Si no solicitaste este cambio, podes ignorar este correo. Tu contrasena no cambiara.
  </p>
  {footer}
</div>
""".format(base_style=_BASE_STYLE, header=_HEADER, footer=_FOOTER)

PAYMENT_CONFIRMATION_TEMPLATE = """
<div style="{base_style}">
  {header}
  <h2 style="color: #f5f5f5; font-size: 20px; margin: 0 0 16px 0;">
    ¡Pago confirmado!
  </h2>
  <p style="color: #d1d5db; line-height: 1.7; margin: 0 0 16px 0;">
    Tu pago fue procesado exitosamente. Tu plan fue actualizado a
    <strong style="color: #f59e0b;">{{plan}}</strong>.
  </p>
  <div style="background: #1a1a1a; border-radius: 8px; padding: 20px; margin: 0 0 24px 0;">
    <table style="width: 100%; color: #d1d5db; font-size: 14px;">
      <tr>
        <td style="padding: 6px 0; color: #9ca3af;">Plan</td>
        <td style="padding: 6px 0; text-align: right; font-weight: 600;">{{plan}}</td>
      </tr>
      <tr>
        <td style="padding: 6px 0; color: #9ca3af;">Monto</td>
        <td style="padding: 6px 0; text-align: right; font-weight: 600;">S/ {{amount}}</td>
      </tr>
      <tr>
        <td style="padding: 6px 0; color: #9ca3af;">Próximo cobro</td>
        <td style="padding: 6px 0; text-align: right;">{{next_date}}</td>
      </tr>
    </table>
  </div>
  <p style="color: #d1d5db; line-height: 1.7; margin: 0 0 24px 0;">
    Ya podes disfrutar de todas las funcionalidades de tu plan. Si tenes
    alguna consulta, escribinos a soporte@tukijuris.net.pe.
  </p>
  {footer}
</div>
""".format(base_style=_BASE_STYLE, header=_HEADER, footer=_FOOTER)

PAYMENT_FAILED_TEMPLATE = """
<div style="{base_style}">
  {header}
  <h2 style="color: #f5f5f5; font-size: 20px; margin: 0 0 16px 0;">
    Pago rechazado
  </h2>
  <p style="color: #d1d5db; line-height: 1.7; margin: 0 0 16px 0;">
    El pago de la suscripcion de <strong style="color: #f59e0b;">{{org_name}}</strong>
    al plan <strong style="color: #f59e0b;">{{plan}}</strong> fue rechazado.
  </p>
  <p style="color: #d1d5db; line-height: 1.7; margin: 0 0 24px 0;">
    Actualiza tu metodo de pago para evitar la suspension del servicio.
    <a href="{{billing_url}}" style="color: #f59e0b;">Ir a facturacion</a>.
  </p>
  {footer}
</div>
""".format(base_style=_BASE_STYLE, header=_HEADER, footer=_FOOTER)


# ---------------------------------------------------------------------------
# Provider abstraction
# ---------------------------------------------------------------------------


class EmailProvider(ABC):
    """Abstract base for all email transport providers."""

    @abstractmethod
    async def send(self, to: str, subject: str, html: str) -> bool:
        """Send an email. Returns True on success."""
        ...


class ResendProvider(EmailProvider):
    """Send via Resend REST API (resend.com)."""

    async def send(self, to: str, subject: str, html: str) -> bool:
        import httpx

        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {settings.resend_api_key}"},
                json={
                    "from": settings.email_from,
                    "to": [to],
                    "subject": subject,
                    "html": html,
                },
            )
            if res.status_code != 200:
                logger.warning(
                    "Resend API returned %s: %s", res.status_code, res.text[:200]
                )
            return res.status_code == 200


class SMTPProvider(EmailProvider):
    """Send via SMTP. Uses asyncio.to_thread to avoid blocking the event loop."""

    async def send(self, to: str, subject: str, html: str) -> bool:
        def _send_sync() -> bool:
            import smtplib
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText

            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = settings.email_from
            msg["To"] = to
            msg.attach(MIMEText(html, "html"))

            with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                server.starttls()
                server.login(settings.smtp_user, settings.smtp_password)
                server.send_message(msg)
            return True

        return await asyncio.to_thread(_send_sync)


class ConsoleProvider(EmailProvider):
    """Log emails to the console — safe default for development."""

    async def send(self, to: str, subject: str, html: str) -> bool:
        logger.info("[EMAIL] To: %s | Subject: %s", to, subject)
        logger.info("[EMAIL] Body preview: %s...", html[:300])
        return True


# ---------------------------------------------------------------------------
# Email service
# ---------------------------------------------------------------------------


class EmailService:
    """High-level service that dispatches emails via the configured provider.

    All public methods are fire-and-forget safe: failures are logged as warnings
    and never propagate to callers.
    """

    def __init__(self) -> None:
        self._provider: EmailProvider | None = None

    def _get_provider(self) -> EmailProvider:
        """Lazy-initialise the provider based on current settings."""
        if self._provider is not None:
            return self._provider

        if settings.email_provider == "resend" and settings.resend_api_key:
            self._provider = ResendProvider()
            logger.info("[EMAIL] Using Resend provider")
        elif settings.email_provider == "smtp" and settings.smtp_host:
            self._provider = SMTPProvider()
            logger.info("[EMAIL] Using SMTP provider (%s)", settings.smtp_host)
        else:
            self._provider = ConsoleProvider()
            logger.info("[EMAIL] Using Console provider (development mode)")

        return self._provider

    async def _send(self, to: str, subject: str, html: str) -> bool:
        """Internal send with fire-and-forget error handling."""
        if not settings.email_enabled:
            # Still use console when disabled so devs can see what would be sent
            logger.info(
                "[EMAIL disabled] Would send to %s — subject: %s", to, subject
            )
            return True
        try:
            return await self._get_provider().send(to, subject, html)
        except Exception as exc:
            logger.warning("[EMAIL] Failed to send to %s: %s", to, exc)
            return False

    async def send_welcome(self, to: str, name: str) -> bool:
        """Send a welcome email after successful registration."""
        html = WELCOME_TEMPLATE.replace("{name}", name)
        return await self._send(to, "Bienvenido a TukiJuris", html)

    async def send_org_invite(
        self,
        to: str,
        inviter_name: str,
        org_name: str,
        invite_url: str,
    ) -> bool:
        """Send an organization invitation email."""
        html = (
            INVITE_TEMPLATE.replace("{inviter}", inviter_name)
            .replace("{org}", org_name)
            .replace("{url}", invite_url)
        )
        subject = f"Te invitaron a {org_name} en TukiJuris"
        return await self._send(to, subject, html)

    async def send_usage_alert(
        self,
        to: str,
        org_name: str,
        used: int,
        limit: int,
    ) -> bool:
        """Send a usage alert when a plan threshold is reached."""
        pct = int(used / limit * 100) if limit > 0 else 0
        html = (
            USAGE_ALERT_TEMPLATE.replace("{org}", org_name)
            .replace("{used}", str(used))
            .replace("{limit}", str(limit))
            .replace("{pct}", str(pct))
        )
        subject = f"Alerta de uso: {pct}% del limite alcanzado"
        return await self._send(to, subject, html)

    async def send_password_reset(self, to: str, reset_url: str) -> bool:
        """Send a time-limited password reset link."""
        html = PASSWORD_RESET_TEMPLATE.replace("{url}", reset_url)
        return await self._send(to, "Restablecer contrasena - TukiJuris", html)

    async def send_payment_confirmation(
        self,
        to: str,
        plan_name: str,
        amount: str,
        next_billing_date: str,
    ) -> bool:
        """Send payment confirmation after successful checkout."""
        html = (
            PAYMENT_CONFIRMATION_TEMPLATE
            .replace("{plan}", plan_name)
            .replace("{amount}", amount)
            .replace("{next_date}", next_billing_date)
        )
        return await self._send(to, f"Pago confirmado - Plan {plan_name}", html)

    async def send_payment_failed(
        self,
        to: str,
        org_name: str,
        plan: str,
        billing_url: str = "",
    ) -> bool:
        """Notify the org owner that their renewal charge failed."""
        html = (
            PAYMENT_FAILED_TEMPLATE
            .replace("{org_name}", org_name)
            .replace("{plan}", plan)
            .replace("{billing_url}", billing_url)
        )
        return await self._send(to, "Pago rechazado - TukiJuris", html)

    # ── Trial lifecycle emails (stub — item 3b wires real delivery) ───────

    _TRIAL_SUBJECTS: dict[str, str] = {
        "trial.started_confirmation": "Tu prueba gratuita de TukiJuris comenzó",
        "trial.reminder_3d": "Tu prueba termina en 3 días",
        "trial.reminder_1d": "Tu prueba termina mañana",
        "trial.reminder_0d_charging": "Hoy te cobraremos el plan TukiJuris",
        "trial.auto_charged_receipt": "Cobro exitoso — bienvenido a TukiJuris",
        "trial.charge_failed_update_card": "Problema con tu pago — actualiza tu tarjeta",
        "trial.downgraded_no_card_postmortem": "Tu prueba terminó — vuelve cuando quieras",
        "trial.canceled_confirmation": "Prueba cancelada — lamentamos verte ir",
    }

    async def send_trial_email(
        self,
        event: str,
        *,
        user_id: object,
        trial_id: object,
        **kwargs: object,
    ) -> bool:
        """Send a trial lifecycle email.

        Log-only stub — real delivery will be wired in item 3b once the email
        provider integration is complete. This method always returns True so
        that callers do not need to handle the stub case specially.

        Supported events (8-template registry):
          trial.started_confirmation, trial.reminder_3d, trial.reminder_1d,
          trial.reminder_0d_charging, trial.auto_charged_receipt,
          trial.charge_failed_update_card, trial.downgraded_no_card_postmortem,
          trial.canceled_confirmation
        """
        subject = self._TRIAL_SUBJECTS.get(event, event)
        logger.info(
            "[TRIAL EMAIL stub] event=%s subject=%r user_id=%s trial_id=%s ctx=%s",
            event,
            subject,
            user_id,
            trial_id,
            kwargs,
        )
        return True


# Singleton instance used across the application
email_service = EmailService()
