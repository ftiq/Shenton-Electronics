from odoo import fields, models, tools, api

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    product_warehouse_id = fields.Many2one(
        'stock.warehouse', string='Warehouse', help='Choose warehouse for this product line.')

    warehouse_qty_available = fields.Float(
        string="Available in Warehouse",
        compute="_compute_warehouse_qty_available",
        store=False,
        readonly=True
    )

    @api.depends('product_id', 'product_warehouse_id')
    def _compute_warehouse_qty_available(self):
        StockQuant = self.env['stock.quant']
        for line in self:
            if line.product_id and line.product_warehouse_id:
                location = line.product_warehouse_id.lot_stock_id
                qty = StockQuant._get_available_quantity(
                    line.product_id,
                    location,
                    lot_id=False,
                    package_id=False,
                    owner_id=False,
                    strict=True
                )
                line.warehouse_qty_available = qty
            else:
                line.warehouse_qty_available = 0.0

    def _action_launch_stock_rule(self, previous_product_uom_qty=False):
        if self._context.get("skip_procurement"):
            return True

        procurements = []
        for line in self:
            line = line.with_company(line.company_id)
            if line.state != 'sale' or line.product_id.type not in ('consu', 'product'):
                continue

            qty = line._get_qty_procurement(previous_product_uom_qty)
            if tools.float_compare(qty, line.product_uom_qty, precision_digits=6) == 0:
                continue

            group_id = line._get_procurement_group()
            if not group_id:
                group_id = self.env['procurement.group'].create(line._prepare_procurement_group_vals())
                line.order_id.procurement_group_id = group_id
            else:
                updated_vals = {}
                if group_id.partner_id != line.order_id.partner_shipping_id:
                    updated_vals['partner_id'] = line.order_id.partner_shipping_id.id
                if group_id.move_type != line.order_id.picking_policy:
                    updated_vals['move_type'] = line.order_id.picking_policy
                if updated_vals:
                    group_id.write(updated_vals)

            values = line._prepare_procurement_values(group_id=group_id)

            # 👇 Custom warehouse logic
            if line.product_warehouse_id:
                values['warehouse_id'] = line.product_warehouse_id

            product_qty = line.product_uom_qty - qty
            line_uom = line.product_uom
            quant_uom = line.product_id.uom_id
            product_qty, procurement_uom = line_uom._adjust_uom_quantities(product_qty, quant_uom)

            procurements.append(self.env['procurement.group'].Procurement(
                line.product_id, product_qty, procurement_uom,
                line.order_id.partner_shipping_id.property_stock_customer,
                line.product_id.display_name, line.order_id.name,
                line.order_id.company_id, values
            ))

        if procurements:
            self.env['procurement.group'].run(procurements)

        for order in self.mapped('order_id'):
            pickings_to_confirm = order.picking_ids.filtered(lambda p: p.state not in ['cancel', 'done'])
            pickings_to_confirm.action_confirm()

        return True
