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

    @api.depends('custom_amount', 'amount_currency', 'account_id', 'company_id', 'partner_id', 'currency_id')
    def _compute_running_balance(self):
        # جميع الحسابات المطلوبة
        all_account_ids = self.mapped('account_id').ids
        company_ids = self.mapped('company_id').ids

        # جلب كل السطور من نفس الحسابات والشركات
        all_lines = self.env['account.move.line'].search([
            ('account_id', 'in', all_account_ids),
            ('company_id', 'in', company_ids),
        ], order='id ASC')

        balance_map = {}
        currency_balance_map = {}

        running_balances = {}  # المفتاح: (account_id, partner_id)

        for line in all_lines:
            key = (line.account_id.id, line.partner_id.id or 0)
            account_type = line.account_id.account_type

            if key not in running_balances:
                running_balances[key] = {'balance': 0.0, 'balance_currency': 0.0}

            delta = line.custom_amount or 0.0
            delta_currency = line.amount_currency or 0.0

            # إذا كان الحساب دائن، نخصم القيمة
            if account_type in ['liability', 'income', 'equity']:
                delta *= -1
                delta_currency *= -1

            running_balances[key]['balance'] += delta
            running_balances[key]['balance_currency'] += delta_currency

            balance_map[line.id] = running_balances[key]['balance']
            currency_balance_map[line.id] = running_balances[key]['balance_currency']

        # تعيين القيم للسجلات الحالية
        for rec in self:
            rec.running_balance = balance_map.get(rec.id, 0.0)
            rec.running_balance_currency = currency_balance_map.get(rec.id, 0.0)
