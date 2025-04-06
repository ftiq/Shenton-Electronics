from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    running_balance = fields.Monetary(
        string="Running Balance",
        store=False,
        compute="_compute_running_balance",
        currency_field="currency_id",
    )

    running_balance_currency = fields.Monetary(
        string="Running Balance in Currency",
        store=False,
        compute="_compute_running_balance",
        currency_field="currency_id",
    )

    @api.depends_context("domain_running_balance")
    def _compute_running_balance(self):
        # ترتيب السجلات كما استلمناها
        lines = self

        # جلب الحركات بنفس الدومين لنجمع التراكم
        domain = self.env.context.get("domain_running_balance", [])
        all_lines = self.env['account.move.line'].search(domain)

        # خزن التراكم
        balance = 0.0
        balance_currency = 0.0

        for line in all_lines:
            balance += line.custom_amount or 0.0
            balance_currency += line.amount_currency or 0.0

            if line in lines:
                line.running_balance = balance
                line.running_balance_currency = balance_currency
