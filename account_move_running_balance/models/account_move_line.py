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
        help="Running balance in currency based on account, partner, and currency.",
    )

    def _compute_running_balance(self):
        if not self:
            return

        # Split records based on whether account type is receivable/payable
        receivable_payable_records = self.filtered(lambda r: r.account_id.account_type in ('asset_receivable', 'liability_payable'))
        normal_records = self - receivable_payable_records

        results_map = {}

        # === Receivable/Payable: group by account + company + partner ===
        for record in receivable_payable_records:
            query = """
                SELECT SUM(custom_amount), SUM(amount_currency)
                FROM account_move_line
                WHERE account_id = %s
                  AND company_id = %s
                  AND partner_id = %s
                  AND (date < %s OR (date = %s AND id <= %s))
            """
            args = (
                record.account_id.id,
                record.company_id.id,
                record.partner_id.id if record.partner_id else None,
                record.date,
                record.date,
                record.id
            )
            self.env.cr.execute(query, args)
            result = self.env.cr.fetchone()
            results_map[record.id] = (result[0] or 0.0, result[1] or 0.0)

        # === Normal accounts: group by account + company ===
        for record in normal_records:
            query = """
                SELECT SUM(custom_amount), SUM(amount_currency)
                FROM account_move_line
                WHERE account_id = %s
                  AND company_id = %s
                  AND (date < %s OR (date = %s AND id <= %s))
            """
            args = (
                record.account_id.id,
                record.company_id.id,
                record.date,
                record.date,
                record.id
            )
            self.env.cr.execute(query, args)
            result = self.env.cr.fetchone()
            results_map[record.id] = (result[0] or 0.0, result[1] or 0.0)

        # Assign values
        for record in self:
            result = results_map.get(record.id, (0.0, 0.0))
            record.running_balance = result[0]
            record.running_balance_currency = result[1]
