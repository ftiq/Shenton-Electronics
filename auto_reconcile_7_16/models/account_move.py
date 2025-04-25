from odoo import models, api
import logging

_logger = logging.getLogger(__name__)

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            rec._auto_reconcile_for_move()
        return records

    def _auto_reconcile_for_move(self):
        if not self.move_id or not self.partner_id:
            return

        journal = self.env['account.journal'].search([('type', '=', 'general')], limit=1)
        if not journal:
            return

        partner = self.partner_id
        move = self.move_id

        # ✅ Filter directly with partner and move
        move_lines = self.env['account.move.line'].search([
            ('move_id', '=', move.id),
            ('partner_id', '=', partner.id),
            ('account_id.code', 'in', ['7', '16']),
            ('reconciled', '=', False),
            ('amount_residual', '!=', 0),
        ])

        if not move_lines or len(move_lines) < 2:
            return

        account_codes = set(move_lines.mapped('account_id.code'))
        if not account_codes.issuperset({'7', '16'}):
            return

        debit_line = move_lines.filtered(lambda l: l.debit > 0)
        credit_line = move_lines.filtered(lambda l: l.credit > 0)

        if not debit_line or not credit_line:
            return

        debit_line = debit_line[0]
        credit_line = credit_line[0]
        amount = min(debit_line.amount_residual, credit_line.amount_residual)

        # Determine correct direction
        if debit_line.account_id.code == '7':
            account_debit = debit_line.account_id
            account_credit = credit_line.account_id
        else:
            account_debit = credit_line.account_id
            account_credit = debit_line.account_id

        # Create balancing journal entry (voucher)
        move_vals = {
            'journal_id': journal.id,
            'date': move.date,
            'ref': f'Auto Transfer for {partner.name}',
            'line_ids': [
                (0, 0, {
                    'account_id': account_debit.id,
                    'partner_id': partner.id,
                    'name': 'Auto transfer (to)',
                    'debit': amount,
                    'credit': 0,
                }),
                (0, 0, {
                    'account_id': account_credit.id,
                    'partner_id': partner.id,
                    'name': 'Auto transfer (from)',
                    'debit': 0,
                    'credit': amount,
                }),
            ]
        }

        new_move = self.env['account.move'].create(move_vals)
        new_move.action_post()

        # Combine and reconcile
        all_lines = debit_line + credit_line + new_move.line_ids.filtered(
            lambda l: l.account_id in [account_debit, account_credit] and l.partner_id == partner
        )

        try:
            all_lines.reconcile()
        except Exception as e:
            _logger.warning(f'⚠️ Reconciliation failed for {partner.name}: {str(e)}')
