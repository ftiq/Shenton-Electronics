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
        string="Running Balance (Currency)",
        store=False,
        compute="_noop_compute",
        currency_field="currency_id",
    )

    def _noop_compute(self):
        for rec in self:
            rec.running_balance_currency = 0.0

    def _compute_running_balance(self):
        if not self:
            return

        # استخدم أول سجل لتحديد الحساب، الشركة، العملة، الشريك (إن وجد)
        sample = self[0]

        acc = sample.account_id
        company = sample.company_id
        currency = sample.currency_id
        partner = sample.partner_id if acc.account_type in ['asset_receivable', 'liability_payable'] else None

        # نبني WHERE clause
        query = """
            SELECT id, custom_amount
            FROM account_move_line
            WHERE account_id = %s AND company_id = %s AND currency_id = %s
        """
        args = [acc.id, company.id, currency.id]

        if partner:
            query += " AND partner_id = %s"
            args.append(partner.id)

        # ترتيب بدون ORDER BY = ترتيب الإدخال في Odoo
        self.env.cr.execute(query, tuple(args))
        all_lines = self.env.cr.fetchall()

        # احسب التراكم وفق الترتيب كما هو
        balance = 0.0
        balance_map = {}

        for line_id, amount in all_lines:
            balance += amount or 0.0
            balance_map[line_id] = balance

        # عيّن فقط للسجلات الحالية
        for rec in self:
            rec.running_balance = balance_map.get(rec.id, 0.0)
