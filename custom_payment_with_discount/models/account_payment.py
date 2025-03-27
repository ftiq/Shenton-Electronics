from odoo import models, fields, api, _

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    cash_discount = fields.Monetary(
        string="Cash Discount",
        currency_field='currency_id',
        help="The cash discount to apply for this payment."
    )
    discount_account_id = fields.Many2one(
        'account.account',
        string="Discount Account",
        help="The account used to record cash discounts."
    )
    discount_applied = fields.Boolean(
        string="Discount Applied",
        default=False,
        help="Technical field to avoid applying the discount multiple times."
    )

    def action_post(self):
        """
        Overrides the post method to include cash discount logic.
        Ensures discount is applied only once and journal line labels are updated.
        """
        super(AccountPayment, self).action_post()

        for payment in self:
            move = payment.move_id

            if not move:
                raise ValueError(_("No journal entry found for the payment."))

            # Optional: Update all move line names to use the memo if empty or default
            memo = payment.communication or 'Payment'
            for line in move.line_ids:
                if not line.name or line.name == '/':
                    line.name = memo

            # Apply discount if applicable and not yet applied
            if (
                payment.cash_discount > 0
                and payment.discount_account_id
                and not payment.discount_applied
            ):
                # Set journal entry to draft if needed
                if move.state == 'posted':
                    move.button_draft()

                # Prepare journal lines using memo
                discount_line = {
                    'account_id': payment.discount_account_id.id,
                    'partner_id': payment.partner_id.id,
                    'name': memo,  # Use memo as label
                    'debit': payment.cash_discount if payment.payment_type == 'inbound' else 0.0,
                    'credit': payment.cash_discount if payment.payment_type == 'outbound' else 0.0,
                }
                receivable_discount_line = {
                    'account_id': payment.destination_account_id.id,
                    'partner_id': payment.partner_id.id,
                    'name': memo,  # Use memo as label
                    'debit': 0.0 if payment.payment_type == 'inbound' else payment.cash_discount,
                    'credit': 0.0 if payment.payment_type == 'outbound' else payment.cash_discount,
                }

                # Add discount lines
                move.write({
                    'line_ids': [
                        (0, 0, discount_line),
                        (0, 0, receivable_discount_line),
                    ]
                })

                # Re-post the move
                move.action_post()

                # Mark as applied
                payment.discount_applied = True
