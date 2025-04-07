from odoo import api, fields, models

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    running_balance = fields.Monetary(
        string="Running Balance",
        store=False,
        compute="_compute_running_balance",
        currency_field="currency_id",
    )

    @api.depends('custom_amount', 'account_id', 'company_id', 'currency_id', 'partner_id')
    def _compute_running_balance(self):
        if not self:
            return

        sample = self[0]
        account_id = sample.account_id.id
        company_id = sample.company_id.id
        currency_id = sample.currency_id.id

        is_partner_required = sample.account_id.account_type in ['asset_receivable', 'liability_payable']
        partner_id = sample.partner_id.id if is_partner_required else None

        where = """
            account_id = %s AND company_id = %s AND currency_id = %s
        """
        params = [account_id, company_id, currency_id]
        if is_partner_required:
            where += " AND partner_id = %s"
            params.append(partner_id)

        query = f"""
            SELECT id, custom_amount
            FROM account_move_line
            WHERE {where}
            ORDER BY id
        """

        self.env.cr.execute(query, tuple(params))
        results = self.env.cr.fetchall()

        balance = 0.0
        balance_map = {}
        for line_id, amount in results:
            balance_map[line_id] = balance
            balance += amount or 0.0

        for rec in self:
            rec.running_balance = balance_map.get(rec.id, 0.0)
