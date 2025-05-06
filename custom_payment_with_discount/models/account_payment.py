def action_post(self):
    super(AccountPayment, self).action_post()

    for payment in self:
        move = payment.move_id
        if not move:
            raise ValueError(_("No journal entry found for the payment."))

        # Remove any existing 0-value discount lines from previous drafts
        discount_names = ['Cash Discount', 'Receivable Adjustment for Discount']
        move.line_ids.filtered(lambda l: l.name in discount_names and l.debit == 0.0 and l.credit == 0.0).unlink()

        # Add discount lines only if the discount is positive and account is provided
        if payment.cash_discount > 0 and payment.discount_account_id:
            if move.state == 'posted':
                move.button_draft()

            # Prepare discount lines
            discount_line = {
                'account_id': payment.discount_account_id.id,
                'partner_id': payment.partner_id.id,
                'name': 'Cash Discount',
                'debit': payment.cash_discount if payment.payment_type == 'inbound' else 0.0,
                'credit': payment.cash_discount if payment.payment_type == 'outbound' else 0.0,
            }
            receivable_discount_line = {
                'account_id': payment.destination_account_id.id,
                'partner_id': payment.partner_id.id,
                'name': 'Receivable Adjustment for Discount',
                'debit': 0.0 if payment.payment_type == 'inbound' else payment.cash_discount,
                'credit': 0.0 if payment.payment_type == 'outbound' else payment.cash_discount,
            }

            # Add lines
            move.write({
                'line_ids': [
                    (0, 0, discount_line),
                    (0, 0, receivable_discount_line),
                ]
            })

            move.action_post()
