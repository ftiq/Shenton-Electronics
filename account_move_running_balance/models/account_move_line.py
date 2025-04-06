from psycopg2 import sql
from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    running_balance = fields.Monetary(
        string="Running Balance",
        store=False,
        compute="_compute_running_balance",
        currency_field="currency_id",
        help="Running balance based on account, partner, and currency.",
    )

    running_balance_currency = fields.Monetary(
        string="Running Balance in Currency",
        store=False,
        compute="_compute_running_balance",
        currency_field="currency_id",
        help="Running balance in currency for the selected account, partner, and currency.",
    )

    @api.depends_context("domain_running_balance")
    def _compute_running_balance(self):
        for record in self:
            record.running_balance = 0.0
            record.running_balance_currency = 0.0

            # اجلب الدومين مباشرة من السياق
            domain = self.env.context.get("domain_running_balance", [])

            # أضف شروط الحساب والجهة والتاريخ
            domain += [
                ('account_id', '=', record.account_id.id),
                ('company_id', '=', record.company_id.id),
                ('id', '>=', record.id),  # لأن الترتيب في Odoo غالبًا id desc
            ]

            if record.account_id.account_type in ('asset_receivable', 'liability_payable') and record.partner_id:
                domain.append(('partner_id', '=', record.partner_id.id))

            if record.currency_id:
                domain.append(('currency_id', '=', record.currency_id.id))

            # تنفيذ البحث باستخدام ORM
            matched_lines = self.env['account.move.line'].search(domain)

            record.running_balance = sum(m.custom_amount or 0.0 for m in matched_lines)
            record.running_balance_currency = sum(m.amount_currency or 0.0 for m in matched_lines)
