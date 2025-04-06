from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    running_balance = fields.Monetary(
        string="Running Balance",
        store=False,
        compute="_compute_running_balance",
        currency_field="currency_id",
        help="Running balance based on account, partner, and currency."
    )

    running_balance_currency = fields.Monetary(
        string="Running Balance in Currency",
        store=False,
        compute="_compute_running_balance",
        currency_field="currency_id",
        help="Running balance in currency for the selected account, partner, and currency."
    )

    @api.depends_context("domain_running_balance")
    def _compute_running_balance(self):
        # استخدم الدومين من السياق أو افتراضي
        domain = self.env.context.get("domain_running_balance", [])

        # الترتيب الثابت يضمن نتيجة تراكمي صحيحة
        order = "date, id"

        # اجلب جميع الحركات المطابقة للدومين مع الترتيب
        all_lines = self.env['account.move.line'].search(domain, order=order)

        # جهز تراكم
        balance = 0.0
        balance_currency = 0.0

        # لتحديد السجلات الظاهرة فقط (لتسريع التحديث)
        current_ids = set(self.ids)

        for line in all_lines:
            balance += line.custom_amount or 0.0
            balance_currency += line.amount_currency or 0.0

            if line.id in current_ids:
                line.running_balance = balance
                line.running_balance_currency = balance_currency
