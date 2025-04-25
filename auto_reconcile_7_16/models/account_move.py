from odoo import models, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model
    def create(self, vals):
        move = super().create(vals)
        move._run_auto_reconcile_7_16()
        return move

    def action_post(self):
        res = super().action_post()
        self._run_auto_reconcile_7_16()
        return res

    def _run_auto_reconcile_7_16(self):
        journal = self.env['account.journal'].search([('type', '=', 'general')], limit=1)

        # السطور من الحسابين 7 و 16 لنفس الشريك
        for partner in self.mapped('line_ids.partner_id'):
            lines = self.env['account.move.line'].search([
                ('partner_id', '=', partner.id),
                ('account_id.code', 'in', ['7', '16']),
                ('reconciled', '=', False),
                ('amount_residual', '>', 0.01)
            ])

            if not lines:
                continue

            acc_codes = set(lines.mapped('account_id.code'))
            if not acc_codes.issubset({'7', '16'}):
                continue

            debit_line = lines.filtered(lambda l: l.debit > 0)
            credit_line = lines.filtered(lambda l: l.credit > 0)

            if not debit_line or not credit_line:
                continue

            debit_line = debit_line[0]
            credit_line = credit_line[0]
            amount = min(debit_line.amount_residual, credit_line.amount_residual)

            if debit_line.account_id.code == '7':
                account_debit = debit_line.account_id
                account_credit = credit_line.account_id
            else:
                account_debit = credit_line.account_id
                account_credit = debit_line.account_id

            move_vals = {
                'journal_id': journal.id,
                'date': self.env['account.move'].search([], limit=1).date or self.env.context.get('date'),
                'ref': f'Auto Transfer for Partner {partner.name}',
                'line_ids': [
                    (0, 0, {
                        'account_id': account_debit.id,
                        'partner_id': partner.id,
                        'name': 'تحويل آلي إلى الحساب المقابل',
                        'debit': amount,
                        'credit': 0,
                    }),
                    (0, 0, {
                        'account_id': account_credit.id,
                        'partner_id': partner.id,
                        'name': 'تحويل آلي من الحساب المقابل',
                        'debit': 0,
                        'credit': amount,
                    }),
                ]
            }

            transfer_move = self.env['account.move'].create(move_vals)
            transfer_move.action_post()

            # تسوية الثلاثة
            all_lines = debit_line + credit_line + transfer_move.line_ids.filtered(
                lambda l: l.account_id in [account_debit, account_credit]
            )
            try:
                all_lines.reconcile()
            except:
                pass

            # بعدها تسوية كل حساب لوحده
            account_map = {}
            for l in lines + transfer_move.line_ids:
                if l.reconciled or abs(l.amount_residual) <= 0.01:
                    continue
                account_map.setdefault(l.account_id.id, self.env['account.move.line'])
                account_map[l.account_id.id] += l

            for acc_lines in account_map.values():
                deb = acc_lines.filtered(lambda l: l.debit > 0 and not l.reconciled)
                cred = acc_lines.filtered(lambda l: l.credit > 0 and not l.reconciled)
                if deb and cred:
                    try:
                        (deb + cred).reconcile()
                    except:
                        pass
