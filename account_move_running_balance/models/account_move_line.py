from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    running_balance = fields.Monetary(
        string="الرصيد التراكمي",
        store=False,
        compute="_compute_running_balance",
        currency_field="currency_id",
    )

    running_balance_currency = fields.Monetary(
        string="الرصيد التراكمي بالعملة",
        store=False,
        compute="_compute_running_balance",
        currency_field="currency_id",
    )

    @api.depends_context("domain_running_balance")
    def _compute_running_balance(self):
        if not self:
            return

        domain = self.env.context.get("domain_running_balance", [])

        # اجلب كل القيود بعد الفلترة (الظاهرة)
        visible_lines = self.env['account.move.line'].search(domain, order='id')

        if not visible_lines:
            return

        # حدد أقل id ظاهر في الفلترة
        first_id = visible_lines[0].id

        # اجمع الحسابات والشركات من الظاهرة
        account_ids = visible_lines.mapped('account_id').ids
        company_ids = visible_lines.mapped('company_id').ids

        # اجلب كل الحركات المرتبطة بالحساب (قبل الفلترة)
        base_domain = [
            ('account_id', 'in', account_ids),
            ('company_id', 'in', company_ids),
            ('id', '<', first_id),  # السجلات السابقة فقط
        ]
        previous_lines = self.env['account.move.line'].search(base_domain)

        # احسب الرصيد الافتتاحي
        opening_balance = sum(l.custom_amount or 0.0 for l in previous_lines)
        opening_currency = sum(l.amount_currency or 0.0 for l in previous_lines)

        # تراكم من البداية
        balance = opening_balance
        currency_balance = opening_currency

        # نحفظ الرصيد لكل سجل ظاهر فقط
        balance_map = {}
        currency_map = {}

        for line in visible_lines:
            balance += line.custom_amount or 0.0
            currency_balance += line.amount_currency or 0.0
            balance_map[line.id] = balance
            currency_map[line.id] = currency_balance

        # التعيين فقط للسجلات الظاهرة (self)
        for rec in self:
            rec.running_balance = balance_map.get(rec.id, 0.0)
            rec.running_balance_currency = currency_map.get(rec.id, 0.0)
